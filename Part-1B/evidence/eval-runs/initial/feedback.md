# Evaluation failure evidence (feed this file to the coding agent)

RULES FOR THE AGENT: you may change `src/` and `prompts/` (application code, prompt construction, parsers, validators, guardrails). You must NOT edit `evals/`, `.harness/`, `tests/`, the specification or thresholds, remove cases, or disable a guardrail. Fix root causes; the human re-runs the same harness.

Decision: INCONCLUSIVE

## Case C05 (normal) sample 1
Requirements: BP-1
Input: {"text": "Remind me this coming Monday at 10am to send the sales report", "now": "2026-11-21T10:00:00+05:30", "timezone": "Asia/Kolkata", "existing_reminders": []}
Expected: {"intent_any_of": ["create"], "datetime": "2026-11-23T10:00:00+05:30", "title": "send sales report"}
Generated output: {"intent": "refuse", "title": null, "datetime": null, "timezone": null, "recurrence": "none", "snooze_minutes": null, "target_reminder_id": null, "clarification_question": null, "refusal_reason": "I can only create, reschedule, or snooze reminders."}
- semantic components: {"intent": 0.0} (mean 0.00, minimum 0.7)

## Case C05 (normal) sample 2
Requirements: BP-1
Input: {"text": "Remind me this coming Monday at 10am to send the sales report", "now": "2026-11-21T10:00:00+05:30", "timezone": "Asia/Kolkata", "existing_reminders": []}
Expected: {"intent_any_of": ["create"], "datetime": "2026-11-23T10:00:00+05:30", "title": "send sales report"}
Generated output: {"intent": "refuse", "title": null, "datetime": null, "timezone": null, "recurrence": "none", "snooze_minutes": null, "target_reminder_id": null, "clarification_question": null, "refusal_reason": "I can only create, reschedule, or snooze reminders."}
- semantic components: {"intent": 0.0} (mean 0.00, minimum 0.7)

## Case C05 (normal) sample 3
Requirements: BP-1
Input: {"text": "Remind me this coming Monday at 10am to send the sales report", "now": "2026-11-21T10:00:00+05:30", "timezone": "Asia/Kolkata", "existing_reminders": []}
Expected: {"intent_any_of": ["create"], "datetime": "2026-11-23T10:00:00+05:30", "title": "send sales report"}
Generated output: {"intent": "refuse", "title": null, "datetime": null, "timezone": null, "recurrence": "none", "snooze_minutes": null, "target_reminder_id": null, "clarification_question": null, "refusal_reason": "I can only create, reschedule, or snooze reminders."}
- semantic components: {"intent": 0.0} (mean 0.00, minimum 0.7)
