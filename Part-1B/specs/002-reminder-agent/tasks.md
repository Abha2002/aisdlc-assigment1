# Tasks: Reminder Agent

**Input**: Approved design documents in `/specs/002-reminder-agent/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/public-api.md`

## Phase 1: Setup

- [ ] T001 Create the Python 3.11 package structure for `src/reminder/` and expose the planned package modules according to the implementation plan. Implements: OSC-1, OSC-2, OSC-3.
- [ ] T002 Add the official `anthropic` SDK and `tzdata` runtime dependencies plus the development requirements needed for offline validation. Implements: OSC-2, OSC-3, BP-5.
- [ ] T003 [P] Define local project configuration for Python 3.11 imports and package discovery of `src/reminder/` without changing `evals/`, `tests/`, or `.harness/`. Implements: OSC-1, OSC-4, EVAL-1.

## Phase 2: Foundational Contract and Configuration

**Purpose**: Establish the public contract and local failure/configuration rules before behavior-specific work.

- [ ] T004 [P] Implement `reminder.errors.ModelServiceError` with the service-failure taxonomy required by the public API. Implements: OSC-3, OSC-4, EVAL-5.
- [ ] T005 [P] Implement `reminder.agent.MODEL_NAME` and `TEMPERATURE` configuration, using `REMINDER_MODEL` and `REMINDER_TEMPERATURE` with the approved defaults and environment-only API-key handling. Implements: OSC-2, OSC-3, GR-3.
- [ ] T006 Implement the exact fixed intent-object shape and its JSON-serializable field types, with no extra keys, in `src/reminder/agent.py`. Implements: OSC-4, OSC-5, OSC-6, OSC-7, OSC-8, OSC-9, OSC-10.
- [ ] T007 Implement local input validation for blank or malformed `text`, `now`, and `tz` values so blank or malformed service input cannot produce fabricated success. Implements: OSC-4, INV-3, BP-3.
- [ ] T008 Implement a prompt in `src/reminder/prompts.py` or `prompts/` that states the fixed schema, supported intents, recurrence values, exact target rules, and JSON-only response requirement. Implements: OSC-4 through OSC-10, INV-1 through INV-9, BP-1 through BP-6, GR-1 through GR-3.

**Checkpoint**: Public contract, configuration, local short-circuiting, and prompt boundary are ready.

## Phase 3: User Story 1 - Create and Recurrence Reminders (Priority: P1)

**Goal**: Interpret English and Hindi create requests and resolve a valid future local datetime, title, timezone, and recurrence.

**Independent Test**: Submit create requests covering tomorrow, absolute clock times, relative durations, recurring words, named zones, and elapsed same-day times.

- [ ] T009 [P] [US1] Implement `handle(text, now, tz, existing_reminders=None)` in `src/reminder/agent.py` with the exact OSC-1 signature and return contract. Implements: OSC-1, OSC-4, OSC-5.
- [ ] T010 [P] [US1] Implement reference-time parsing and strict create/reschedule horizon validation from the caller-supplied `now`, including 1826-day and DST-offset checks. Implements: INV-2, INV-9, BP-1, BP-2.
- [ ] T011 [US1] Implement natural-language resolution for tomorrow, relative durations, month/day dates, coming weekdays, evening, and elapsed same-day clock times against `now` and `tz`. Implements: BP-1, BP-3, INV-2.
- [ ] T012 [US1] Implement explicit named-zone resolution so a named IANA zone overrides the supplied default timezone and retains the correct instant offset. Implements: BP-2, OSC-7, OSC-8, INV-9.
- [ ] T013 [US1] Implement recurrence mapping for every-day, every-week, and every-month wording to `daily`, `weekly`, and `monthly`, while keeping non-recurring results at `none`. Implements: BP-4, OSC-9, INV-8.
- [ ] T014 [US1] Implement create-result assembly with a meaningful non-empty title, future offset-bearing datetime, IANA timezone, recurrence, and null target/snooze fields. Implements: INV-1, INV-6, INV-8, OSC-6 through OSC-10.
- [ ] T015 [US1] Implement English and Hindi interpretation behavior for create requests and recurrence concepts, including Hindi clarification wording where applicable. Implements: BP-5, INV-3, OSC-6.

**Checkpoint**: US1 independently returns valid create intents for relative, absolute, recurring, timezone, and bilingual requests.

## Phase 4: User Story 2 - Reschedule and Snooze Existing Reminders (Priority: P1)

**Goal**: Resolve unique supplied targets and return only valid reschedule or snooze intents.

**Independent Test**: Submit uniquely matching, ambiguous, and unmatched title or target requests; verify no guessed targets.

- [ ] T016 [P] [US2] Implement exact existing-reminder ID membership validation for every reschedule and snooze target. Implements: INV-4, INV-5, BP-6.
- [ ] T017 [US2] Implement unique title/target matching from `existing_reminders`; return clarify for zero or multiple matches and never guess an ID or datetime. Implements: BP-3, BP-6, INV-3.
- [ ] T018 [US2] Implement reschedule-result assembly with a unique target ID, strict future datetime within 1826 days, matching IANA offset, `recurrence=none`, and null snooze fields. Implements: INV-2, INV-5, INV-8, INV-9, OSC-7 through OSC-10.
- [ ] T019 [US2] Implement snooze-result assembly with a unique target ID, integer duration from 1 through 1440, null datetime, and `recurrence=none`. Implements: INV-4, INV-3, INV-8, OSC-7, OSC-10.

**Checkpoint**: US2 independently returns valid reschedule/snooze intents only for exact unique supplied targets.

## Phase 5: User Story 3 - Clarify Missing or Invalid Input (Priority: P2)

**Goal**: Ask focused clarification instead of guessing for missing, ambiguous, past, or over-horizon information.

**Independent Test**: Submit missing task/time, ambiguous calendar expressions, elapsed absolute dates, and dates beyond 1826 days.

- [ ] T020 [P] [US3] Implement clarify-result assembly with a non-empty clarification question of at most 300 characters, null datetime, no snooze duration, and no guessed target ID. Implements: INV-3, INV-6, INV-8, OSC-6.
- [ ] T021 [US3] Implement past absolute-time and over-horizon rejection for create/reschedule so the result becomes clarify rather than success. Implements: INV-2, BP-3, OSC-7.
- [ ] T022 [US3] Implement focused clarification for missing tasks, missing times, ambiguous dates, ambiguous targets, and malformed calendar expressions. Implements: BP-3, BP-6, INV-3.
- [ ] T023 [US3] Implement language-aware clarification so Hindi requests use Hindi questions where appropriate and English requests receive English questions. Implements: BP-5, OSC-6.

**Checkpoint**: US3 independently refuses to guess when task, time, target, or date validity is insufficient.

## Phase 6: User Story 4 - Refuse Unsupported and Unsafe Requests (Priority: P2)

**Goal**: Refuse unsupported actions and preserve the fixed contract around prompt injection and secrets.

**Independent Test**: Submit delete, email, message, tool, prompt-injection, and credential-containing requests.

- [ ] T024 [P] [US4] Implement refuse-result assembly for unsupported actions with a non-empty refusal reason and no unsupported action text or success fields. Implements: GR-1, INV-7, OSC-6.
- [ ] T025 [US4] Add prompt-injection and embedded-instruction containment so reminder text cannot alter behavior or enter title or clarification/refusal output. Implements: GR-2, OSC-4, INV-1.
- [ ] T026 [US4] Implement credential and secret redaction so quoted credentials or secret values are never copied into any output field. Implements: GR-3, OSC-4, OSC-6.

**Checkpoint**: US4 independently returns safe refuse or valid reminder intents without leaking instructions or secrets.

## Phase 7: Model Output Handling and Service Failures

- [ ] T027 Implement the Anthropic SDK message call with the system prompt, caller context, JSON-only instruction, environment-only key lookup, and at-most-two-call budget. Implements: OSC-2, OSC-3, OSC-4, BP-5, EVAL-5.
- [ ] T028 Implement strict single-object JSON extraction that rejects arrays, trailing text, malformed JSON, and extra-key/non-schema output. Implements: OSC-4, OSC-5, OSC-6, INV-1 through INV-9.
- [ ] T029 Implement one bounded retry for parse or invariant violations, followed by the fixed safe clarify fallback for a second failed attempt. Implements: OSC-4, INV-3, BP-3.
- [ ] T030 Implement explicit `ModelServiceError` mapping for missing keys, timeout, rate limit, API/server/network, and SDK failures while keeping model-output failures on the retry/clarify path. Implements: OSC-3, EVAL-5.
- [ ] T031 Implement temperature API compatibility fallback that omits unsupported temperature on the second call and updates `TEMPERATURE` to `None`. Implements: OSC-2, OSC-4.

## Phase 8: Validation and Evaluation

- [ ] T032 Add or adjust verification coverage for the public signature, exact result keys, field limits, intent enum, timezone offsets, horizon, recurrence, target IDs, clarification, refusal, and bilingual behavior. Implements: OSC-1 through OSC-10, INV-1 through INV-9, BP-1 through BP-6, GR-1 through GR-3.
- [ ] T033 Preserve oracle independence by verifying no implementation task or change reads or writes `evals/`, `tests/`, or `.harness/` assets. Implements: EVAL-1, EVAL-2, EVAL-5.
- [ ] T034 Lock and verify `evals/thresholds.json` before the first evaluation and keep threshold values unchanged during implementation. Implements: EVAL-1.
- [ ] T035 Verify `evals/requirements.json` lists every exercised requirement ID for each acceptance-dataset case and retain complete OSC/INV/BP/GR/EVAL traceability. Implements: EVAL-2, EVAL-3, EVAL-4.
- [ ] T036 Implement or verify evaluators so any structural, invariant, or guardrail failure makes the sample score zero. Implements: EVAL-3.
- [ ] T037 Implement or verify passing non-error evaluation semantics, including intent, datetime, title or keyword evidence, recurrence, target, minutes, and clarification evidence as applicable. Implements: EVAL-4.
- [ ] T038 Keep model/service errors separate from pass/fail scoring and ensure each makes evaluation inconclusive. Implements: EVAL-5.
- [ ] T039 Run the existing offline contract suite and the minimum scenario matrix from `quickstart.md`, including blank input and missing-key behavior with no model call. Implements: OSC-1 through OSC-10, INV-1 through INV-9, BP-1 through BP-6, GR-1 through GR-3.
- [ ] T040 Run the human-owned initial evaluation with unchanged thresholds and 3 runs, confirming aggregate semantic, structural, invariant, guardrail, and traceability outcomes. Implements: SC-1 through SC-6, EVAL-1 through EVAL-5.

## Dependencies

- Phase 2 blocks all behavior-specific work.
- US1 (Phase 3) depends on the exact contract and configuration from Phase 2.
- US2 (Phase 4) depends on target-validation and contract foundations.
- US3 (Phase 5) depends on time validation and fixed clarify shape.
- US4 (Phase 6) depends on the fixed refuse shape and prompt/secret containment.
- Phase 7 depends on the public contract and behavior-specific validators.
- Phase 8 depends on all implementation phases and must not modify oracle assets.

## Parallel Opportunities

- T003, T004, T005, T006, and T007 can proceed independently after package setup.
- US1, US2, US3, and US4 implementation can proceed in parallel after foundational contract completion.
- Contract and output validation tasks can be implemented in parallel with independent time and target validators.
- Final offline and evaluation tasks run only after implementation phases complete.
