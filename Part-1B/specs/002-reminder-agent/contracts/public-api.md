# Public API Contract

## Module: `reminder.agent`

### `handle`

```text
handle(
    text: str,
    now: str,
    tz: str,
    existing_reminders: list[dict] | None = None,
) -> dict
```

### Inputs

- `text`: reminder request text.
- `now`: caller-supplied ISO-8601 reference instant with an offset.
- `tz`: caller-supplied IANA timezone.
- `existing_reminders`: optional transient reminder records available for exact target matching.

### Success Result

Exactly these keys and no others:

```json
{
  "intent": "create",
  "title": "Call",
  "datetime": "2026-11-24T18:00:00-05:00",
  "timezone": "America/New_York",
  "recurrence": "none",
  "snooze_minutes": null,
  "target_reminder_id": null,
  "clarification_question": null,
  "refusal_reason": null
}
```

The JSON shape is identical for clarify, refuse, snooze, reschedule, and create; values are constrained by OSC-4 through OSC-10 and INV-1 through INV-9.

## Module: `reminder.errors`

### `ModelServiceError`

Raised when:

- `ANTHROPIC_API_KEY` is missing.
- The SDK reports a timeout.
- The API reports a rate limit.
- The API reports an HTTP/API/server or network failure.

It must not be converted into a clarification or a valid success-shaped object.

## Module Exports

- `reminder.agent.handle`
- `reminder.agent.MODEL_NAME`
- `reminder.agent.TEMPERATURE`
- `reminder.errors.ModelServiceError`

## Result Rules

| Intent | Datetime | Title | Target | Recurrence | Snooze | Explanation |
|---|---|---|---|---|---|---|
| `create` | future, <= 1826 days | non-empty, <= 200 chars | null | any supported | null | Create only |
| `reschedule` | future, <= 1826 days | optional | exact existing ID | none | null | Existing target required |
| `snooze` | null | optional | exact existing ID | none | 1-1440 | Existing target required |
| `clarify` | null | optional | normally null | none | null | Non-empty clarification question |
| `refuse` | null | null | null | none | null | Non-empty refusal reason |

Traceability: OSC-1 through OSC-10, INV-1 through INV-9.
