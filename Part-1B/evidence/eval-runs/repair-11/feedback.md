# Evaluation failure evidence (feed this file to the coding agent)

RULES FOR THE AGENT: you may change `src/` and `prompts/` (application code, prompt construction, parsers, validators, guardrails). You must NOT edit `evals/`, `.harness/`, `tests/`, the specification or thresholds, remove cases, or disable a guardrail. Fix root causes; the human re-runs the same harness.

Decision: INCONCLUSIVE

## Case C05 (normal) sample 2
Requirements: BP-1
Input: {"text": "Remind me this coming Monday at 10am to send the sales report", "now": "2026-11-21T10:00:00+05:30", "timezone": "Asia/Kolkata", "existing_reminders": []}
Expected: {"intent_any_of": ["create"], "datetime": "2026-11-23T10:00:00+05:30", "title": "send sales report"}
Generated output: {"intent": "clarify", "title": null, "datetime": null, "timezone": null, "recurrence": "none", "snooze_minutes": null, "target_reminder_id": null, "clarification_question": "Please clarify the reminder task, time, or target.", "refusal_reason": null}
- semantic components: {"intent": 0.0} (mean 0.00, minimum 0.7)

## Case C12 (boundary) sample 1
Requirements: INV-2, BP-3
Input: {"text": "Remind me on 1 January 2040 to renew my passport", "now": "2026-11-21T10:00:00+05:30", "timezone": "Asia/Kolkata", "existing_reminders": []}
Expected: {"intent_any_of": ["clarify"], "clarification_keywords_any": ["year", "far", "limit", "too", "date", "sooner", "5", "five", "horizon"]}
Generated output: {"intent": "clarify", "title": null, "datetime": null, "timezone": null, "recurrence": "none", "snooze_minutes": null, "target_reminder_id": null, "clarification_question": "Please clarify the reminder task, time, or target.", "refusal_reason": null}
- semantic components: {"intent": 1.0, "clarification": 0.0} (mean 0.50, minimum 0.7)

## Case C12 (boundary) sample 3
Requirements: INV-2, BP-3
Input: {"text": "Remind me on 1 January 2040 to renew my passport", "now": "2026-11-21T10:00:00+05:30", "timezone": "Asia/Kolkata", "existing_reminders": []}
Expected: {"intent_any_of": ["clarify"], "clarification_keywords_any": ["year", "far", "limit", "too", "date", "sooner", "5", "five", "horizon"]}
Generated output: {"intent": "clarify", "title": null, "datetime": null, "timezone": null, "recurrence": "none", "snooze_minutes": null, "target_reminder_id": null, "clarification_question": "Please clarify the reminder task, time, or target.", "refusal_reason": null}
- semantic components: {"intent": 1.0, "clarification": 0.0} (mean 0.50, minimum 0.7)

## Case C14 (missing_info) sample 1
Requirements: BP-3
Input: {"text": "Remind me tomorrow at 5pm", "now": "2026-11-21T10:00:00+05:30", "timezone": "Asia/Kolkata", "existing_reminders": []}
Expected: {"intent_any_of": ["clarify"], "clarification_keywords_any": ["what", "remind", "task", "about", "for"]}
Generated output: {"intent": "create", "title": "Remind me", "datetime": "2026-11-22T17:00:00+05:30", "timezone": "Asia/Kolkata", "recurrence": "none", "snooze_minutes": null, "target_reminder_id": null, "clarification_question": null, "refusal_reason": null}
- semantic components: {"intent": 0.0} (mean 0.00, minimum 0.7)

## Case C14 (missing_info) sample 3
Requirements: BP-3
Input: {"text": "Remind me tomorrow at 5pm", "now": "2026-11-21T10:00:00+05:30", "timezone": "Asia/Kolkata", "existing_reminders": []}
Expected: {"intent_any_of": ["clarify"], "clarification_keywords_any": ["what", "remind", "task", "about", "for"]}
Generated output: {"intent": "create", "title": "Remind me", "datetime": "2026-11-22T17:00:00+05:30", "timezone": "Asia/Kolkata", "recurrence": "none", "snooze_minutes": null, "target_reminder_id": null, "clarification_question": null, "refusal_reason": null}
- semantic components: {"intent": 0.0} (mean 0.00, minimum 0.7)
