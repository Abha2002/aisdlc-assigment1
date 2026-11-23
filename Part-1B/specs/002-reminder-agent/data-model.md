# Data Model

## ReminderRequest

The public input representation passed to `handle`.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `text` | `str` | yes | A blank or whitespace-only value is handled locally and never sent to the model. |
| `now` | `str` | yes | ISO-8601 instant with an offset; used as the reference for resolution and horizon checks. |
| `tz` | `str` | yes | Default IANA timezone; replaced only by an explicitly named zone in the request. |
| `existing_reminders` | `list[dict] | None` | no | Only these records may provide reschedule/snooze target IDs. |

## IntentObject

The sole successful JSON-serializable output shape. All fields are always present; extra keys are invalid.

| Field | Type | Rules |
|---|---|---|
| `intent` | `str` | Exactly `create`, `reschedule`, `snooze`, `clarify`, or `refuse`. |
| `title` | `str | null` | At most 200 characters; create requires a non-empty string. |
| `datetime` | `str | null` | ISO-8601 with a UTC offset; null for clarify, refuse, and snooze. |
| `timezone` | `str | null` | IANA zone name or null. |
| `recurrence` | `str` | Exactly `none`, `daily`, `weekly`, or `monthly`; only create may use a recurrence other than `none`. |
| `snooze_minutes` | `int | null` | 1 through 1440; non-null only for snooze. |
| `target_reminder_id` | value matching supplied reminder ID or null | Required for snooze/reschedule; null for create. |
| `clarification_question` | `str | null` | Non-empty and at most 300 characters for clarify. |
| `refusal_reason` | `str | null` | Non-empty and at most 300 characters for refuse. |

## ExistingReminder

Caller-owned input used only for target resolution.

| Field | Type | Required | Rules |
|---|---|---:|---|
| `id` | scalar identifier | yes | Exact membership defines a valid target. |
| `title` | `str` | no, when provided | Human-readable matching context only. |
| `datetime` | `str` | no | Informational context only. |

No persistence or mutation occurs. The implementation must not execute a reschedule, snooze, delete, notification, message, tool, or other action.

## Validation Rules

- A datetime for create or reschedule must be strictly later than `now` and no later than 1826 days after `now`.
- A datetime offset must match the offset of `timezone` for the represented instant.
- Clarify requires a non-empty clarification question and a null datetime.
- Snooze requires a valid duration and exact target membership in `existing_reminders`.
- Reschedule requires a valid future datetime and exact target membership.
- Refuse requires a non-empty refusal reason.
- `snooze_minutes`, recurrence, target ID, clarification question, and refusal reason must obey their intent-specific null/non-null conditions.

Traceability: OSC-4 through OSC-10 and INV-1 through INV-9.
