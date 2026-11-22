# Data Model: Smart Todo

## Task

A task is a dict with exactly these keys:

| Field | Type | Rules |
|---|---|---|
| `id` | int | Positive sequential id; bool is not accepted as an id |
| `title` | str | Stripped surrounding whitespace; 1 to 100 characters after stripping |
| `priority` | str | Exactly `low`, `medium`, or `high` |
| `status` | str | Exactly `todo`, `in_progress`, or `done` |
| `tags` | list[str] | Stripped, lower-cased ASCII tags matching `[a-z0-9-]{1,20}`, max 10 distinct values |
| `created_at` | str | ISO-8601 timestamp with UTC timezone offset |

No additional task keys are allowed in persisted or returned data.

## Store

The JSON root is:

```json
{
  "version": 1,
  "next_id": 1,
  "tasks": []
}
```

| Field | Type | Rules |
|---|---|---|
| `version` | int | Exactly 1; bool is not acceptable |
| `next_id` | int | Positive integer greater than every previously assigned id; is never decreased |
| `tasks` | list[dict] | Each entry must satisfy the Task shape and invariant rules |

## Lifecycle invariants

- A successful add assigns `next_id`, returns a copy, and increments `next_id` in the persisted store.
- Delete removes only the identified task and does not decrease `next_id`.
- Update changes only title, priority, and/or tags supplied as non-None values.
- Status and `created_at` are immutable through update.
- Status transitions follow only the FR-8 allowlist.
- A failed validation or lookup leaves persisted task state unchanged.
- Returned dicts and nested tag lists are copies, never direct references to loaded mutable state.

## Persistence invariants

- The file contains only the approved store shape and task entries.
- A missing file is not created by read-only operations.
- A mutation creates or replaces the file only after valid in-memory changes exist.
- A corrupt or wrong-shaped file raises `StorageError` and remains byte-for-byte unchanged.
- A failed save raises `StorageError`, leaves existing destination bytes unchanged, and removes temp files.
