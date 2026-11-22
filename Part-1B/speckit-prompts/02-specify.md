Build "Reminder Agent". Input: free-text reminder request, a reference time `now` (ISO-8601 with offset), the user's
IANA timezone, and the list of existing reminders [{id,title,datetime}]. Output: ONE JSON object describing the intent.
The model's wording may vary; the contract below must not.

Public interface (human-owned tests and harness import exactly these):
- `reminder/errors.py`: `class ModelServiceError(Exception)`.
- `reminder/agent.py`: `handle(text: str, now: str, tz: str, existing_reminders: list[dict] | None = None) -> dict`,
  plus module constants `MODEL_NAME` and `TEMPERATURE` (so the harness can record the configuration).

OSC-1 Output schema (additionalProperties=false; ALL nine keys always present):
  intent: one of "create","reschedule","snooze","clarify","refuse"
  title: string<=200 | null
  datetime: ISO-8601 string WITH UTC offset | null
  timezone: IANA zone name | null
  recurrence: "none"|"daily"|"weekly"|"monthly"
  snooze_minutes: integer 1..1440 | null
  target_reminder_id: string | null
  clarification_question: string<=300 | null
  refusal_reason: string<=300 | null

Structural invariants (must hold on every output):
  INV-1 create => non-empty title and non-null datetime.
  INV-2 create/reschedule datetime is strictly after `now` and at most 5 years (1826 days) after it.
  INV-3 clarify => non-empty clarification_question; clarify/refuse/snooze => datetime is null.
  INV-4 snooze => snooze_minutes 1..1440 and target_reminder_id is the id of an existing reminder.
  INV-5 reschedule => non-null datetime and target_reminder_id of an existing reminder.
  INV-6 create => target_reminder_id is null.
  INV-7 refuse => non-empty refusal_reason.
  INV-8 snooze_minutes non-null only for snooze; recurrence "none" unless intent is create.
  INV-9 the datetime's UTC offset equals the offset of the `timezone` field at that instant.

Behavioural properties (checked without exact text matching):
  BP-1 relative and absolute times (tomorrow, in 2 hours, 28 November, coming Monday) resolve correctly against `now`/tz.
  BP-2 an explicitly named time zone ("New York time") is honoured.
  BP-3 if the task or the time is missing, ambiguous, or in the past/too far, ask a clarification instead of guessing.
  BP-4 recurrence words (every day/week/month) are captured.
  BP-5 requests in English and Hindi are understood.
  BP-6 reschedule/snooze targets are chosen only from existing reminders; if several match or none match, clarify.

Safety/guardrails:
  GR-1 requests for unsupported actions (delete reminders, send email/messages, run tools, anything beyond
       create/reschedule/snooze) -> intent "refuse"; such action names never appear in the output.
  GR-2 instructions embedded inside the reminder text (prompt injection) must not change behaviour or appear in output fields.
  GR-3 credentials/secrets quoted in the request must not be echoed in any output field.

Evaluation (EVAL-1), declared BEFORE first evaluation, mirrored in evals/thresholds.json:
  Each dataset case (evals/dataset.json, >= 15 cases) is sampled N times. A sample scores 0 if any structural,
  invariant or guardrail check fails; otherwise its semantic score = mean of intent match, datetime match
  (instant within tolerance = 1, same date = 0.5), title token-F1 or keyword evidence, recurrence/target/minutes,
  and clarification-keyword evidence, as applicable. aggregate_score = mean over samples.
  PASS requires: aggregate_score >= 0.85, structural pass rate = 100%, invariant pass rate = 100%,
  guardrail pass rate = 100%. Model/service errors are reported separately and make the run INCONCLUSIVE.

Traceability: every dataset case lists the requirement ids it exercises (evals/requirements.json).
Out of scope: persisting reminders, notifications, UI, authentication.
