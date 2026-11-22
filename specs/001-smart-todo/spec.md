# Feature Specification: Smart Todo

**Feature Branch**: `001-smart-todo`  
**Created**: 2026-11-22  
**Status**: Draft  
**Input**: Python task manager with a service API and CLI, persisting state in a JSON file.

## User Scenarios & Testing

### User Story 1 - Create and Manage Tasks (Priority: P1)

A user creates tasks with a title, priority, and tags, then reads, updates, deletes, or changes the status of those tasks through the Python service API or CLI.

**Why this priority**: Task creation and lifecycle management are the core product behavior.

**Independent Test**: Add, retrieve, update, list, change status, and delete tasks against a temporary JSON file; verify the exact values and error classes.

**Acceptance Scenarios**:

1. **Given** an empty or existing valid store, **When** the user adds a valid task, **Then** the task is returned with status `todo`, the requested or default priority, normalized tags, a sequential id, and UTC ISO-8601 creation time.
2. **Given** a task exists, **When** the user updates only provided fields, **Then** that task changes without changing status or creation time and is returned as a copy.
3. **Given** a task exists, **When** the user deletes or changes it according to valid rules, **Then** state changes only as approved and persisted results remain observable across service instances.

### User Story 2 - Find Tasks (Priority: P2)

A user lists tasks with optional tag and status filters and chooses priority or id ordering.

**Why this priority**: Filters and deterministic ordering make stored tasks usable.

**Independent Test**: Create tasks with varied priorities, tags, and statuses, then verify combined filters and both sort modes.

**Acceptance Scenarios**:

1. **Given** tasks with tags and statuses, **When** the user combines valid filters, **Then** only matching tasks are returned.
2. **Given** matching tasks, **When** the user sorts by priority or id, **Then** the prescribed deterministic order is returned.

### User Story 3 - Operate from the CLI (Priority: P3)

A user performs task operations through `python -m todo` with JSON output and clear errors.

**Why this priority**: The CLI exposes the service behavior for command-line use.

**Independent Test**: Invoke each CLI command with valid and invalid inputs and verify stdout, stderr, JSON, and exit codes.

**Acceptance Scenarios**:

1. **Given** valid CLI arguments and a valid store, **When** a command succeeds, **Then** exactly one JSON document is printed to stdout and the process exit code is 0.
2. **Given** invalid CLI input or a TodoError, **When** a command fails, **Then** stderr contains `error: <message>`, stdout is empty, and the exit code is 2.

### Edge Cases

- Invalid add, update, or status input must not mutate state or consume an id.
- Unknown, non-integer, and boolean task ids must produce the specified validation or not-found behavior.
- An empty, malformed, or wrong-shaped JSON file is corruption and must be detected on every operation.
- A failed persistence write must preserve the prior file bytes and leave no temporary file.
- Read-only operations must not create a missing data file.
- `tags=[]` updates or clears tags as an explicit field while `tags=None` means tags were not provided.

## Clarifications

### Session 2026-11-22

- **Status transitions**: `done -> in_progress` is NOT allowed. The exact allowed transitions remain those listed in FR-8: `todo -> in_progress`, `todo -> done`, `in_progress -> todo`, `in_progress -> done`, and `done -> todo`.
- **Concurrent writers**: Concurrency control and concurrent-writer guarantees are out of scope. Multiple processes must not be assumed to coordinate; no operation-level concurrency semantics are specified. If simultaneous writes occur, last-writer-wins is acceptable.
- **Tag filtering**: Tag filters use exact-match semantics only. Prefix, substring, and partial matching are not supported; a filter matches a tag only when the case-insensitively normalized values are equal.
- **CLI tag arguments**: `--tag` is repeatable for `add` and `edit`. For example, `--tag work --tag urgent` supplies two tags. Comma-separated tag values are not supported: a comma is subject to the normal tag validation and is not interpreted as a separator.
- **Title characters**: Titles may contain non-ASCII characters. The title rule is based on Python string length after surrounding whitespace is stripped: it must contain 1 through 100 characters. Tags remain ASCII-only because the required tag pattern is `[a-z0-9-]{1,20}`.

## Requirements

### Public Interface

The implementation MUST expose exactly these public names and signatures:

- `todo/errors.py`: `TodoError(Exception)` and subclasses `ValidationError`, `TaskNotFoundError`, `InvalidTransitionError`, and `StorageError`.
- `todo/service.py`: `class TaskService(path)` with methods:
  - `add_task(title, priority="medium", tags=None) -> dict`
  - `get_task(task_id) -> dict`
  - `update_task(task_id, title=None, priority=None, tags=None) -> dict`
  - `delete_task(task_id) -> None`
  - `set_status(task_id, new_status) -> dict`
  - `list_tasks(tag=None, status=None, sort="priority") -> list[dict]`
- `todo/cli.py`: `main(argv=None) -> int`; it MUST return an exit code and MUST NOT call `sys.exit`.
- `todo/__main__.py`: MUST make `python -m todo` work.
- Source MUST live under `src/todo/`.

A task dict MUST contain exactly these keys: `id`, `title`, `priority`, `status`, `tags`, and `created_at`. `id` MUST be an int, `title` and `created_at` MUST be strings, `priority` and `status` MUST be strings, `tags` MUST be a list of strings, and `created_at` MUST be ISO-8601 with a timezone offset representing UTC. Returned task dicts MUST be copies of stored data.

### Functional Requirements

- **FR-1**: `add_task` MUST return the new task with status `todo`, default priority `medium` when omitted, tags `[]` when omitted, and an id assigned sequentially starting at 1.
- **FR-2**: On add, `title` MUST be stripped of surrounding whitespace. It MUST be a str of 1 through 100 characters after stripping; otherwise, `ValidationError` MUST be raised. A failed add MUST NOT consume an id.
- **FR-3**: On add or update, priority MUST be exactly `low`, `medium`, or `high`, lowercase and case-sensitive; otherwise, `ValidationError` MUST be raised.
- **FR-4**: On add or update, tags MUST be a list of str. Each tag MUST be stripped and lower-cased, match `[a-z0-9-]{1,20}`, and contain no more than 10 distinct tags. Duplicate tags MUST be removed while preserving first occurrence order. Otherwise, `ValidationError` MUST be raised.
- **FR-5**: `get_task` MUST return the requested task. Unknown ids, including 0 and negative ids, MUST raise `TaskNotFoundError`. Non-int ids, including bool, str, float, and None, MUST raise `ValidationError`.
- **FR-6**: `update_task` MUST change only fields whose arguments are non-None. `tags=[]` MUST clear tags. At least one field MUST be provided; otherwise, `ValidationError` MUST be raised. Validation MUST complete before mutation; an invalid update MUST leave the task unchanged. `status` and `created_at` MUST never change through update. Unknown ids MUST raise `TaskNotFoundError`.
- **FR-7**: `delete_task` MUST remove the requested task. Deleted ids MUST never be reused, including for the highest id and across restarts.
- **FR-8**: Valid statuses MUST be exactly `todo`, `in_progress`, and `done`. Allowed transitions MUST be only `todo -> in_progress`, `todo -> done`, `in_progress -> todo`, `in_progress -> done`, and `done -> todo`. Any other change, including setting the same status, MUST raise `InvalidTransitionError` and leave the task unchanged. An unknown status value MUST raise `ValidationError`. Unknown task ids MUST follow FR-5 id rules.
- **FR-9**: `list_tasks` MUST optionally filter by normalized tag exact match case-insensitively and optionally filter by status. Both filters MUST be combinable. `sort="priority"` MUST order high, medium, low and then id ascending. `sort="id"` MUST order id ascending. Any other sort or status value MUST raise `ValidationError`. No matches MUST produce `[]`.
- **FR-10**: All state MUST be stored in one JSON file specified by `path` using exactly the shape `{"version":1,"next_id":int,"tasks":[...]}`. Writes MUST use an atomic temp file in the same directory followed by `os.replace`. A failed write MUST raise `StorageError`, leave the previous file byte-identical, and leave no temp files. Read-only operations MUST NOT create the file. State MUST persist across `TaskService` instances.
- **FR-11**: An empty file, invalid JSON, or JSON of the wrong shape MUST raise `StorageError` on every operation and MUST not modify or overwrite the corrupt file.
- **FR-12**: The CLI syntax MUST be exactly `python -m todo [--file PATH] <command>` with default file `tasks.json` and commands:
  - `add TITLE [--priority P] [--tag T ...]`
  - `get ID`
  - `edit ID [--title] [--priority] [--tag T ...]`
  - `delete ID`
  - `status ID NEW_STATUS`
  - `list [--tag T] [--status S] [--sort priority|id]`

  In `add` and `edit`, `--tag` MUST be repeatable; each occurrence supplies one tag. Comma-separated values are not a list separator.

  On success, the CLI MUST print exactly one JSON document to stdout: a task, a list, or `{"deleted": ID}`, and MUST exit with code 0. On any `TodoError`, it MUST print `error: <message>` to stderr, print nothing to stdout, and exit with code 2.

### Non-Functional Requirements

- **NFR-1**: `ruff check src tests` MUST report zero findings under the constitution's rules, including E, F, W, I, B, S, UP, C90, line length 100, and cyclomatic complexity 10 or less per function.
- **NFR-2**: Cyclomatic complexity MUST be 10 or less per function.
- **NFR-3**: `bandit -r src` MUST report zero MEDIUM or HIGH findings.
- **NFR-4**: Line coverage of `src/todo` MUST be at least 90%.
- **NFR-5**: The repository MUST contain no secrets, tokens, credentials, or private keys.
- **NFR-6**: A created data file MUST have POSIX owner-only permissions of 0600.
- **NFR-7**: Runtime dependencies MUST be limited to the Python standard library.

## Key Entities

- **Task**: A persisted task dict with id, title, priority, status, tags, and UTC ISO-8601 `created_at`.
- **TaskStore**: The JSON file state containing format version 1, the next id, and the task list.
- **TodoError**: Base exception type for validation, lookup, transition, and storage failures.

## Success Criteria

### Measurable Outcomes

- **SC-1**: All FR and NFR acceptance criteria pass the human-owned automated harness.
- **SC-2**: The service and CLI expose the exact public interface and persist deterministic state for identical valid inputs and file contents, except timestamp values.
- **SC-3**: No implementation feature exists outside the approved FR/NFR requirements.

## Assumptions

- The JSON file is local and accessed by one process at a time; concurrency control is out of scope.
- Timestamp values may differ on separate creation operations, but all other identical valid operation results must be deterministic.
- Missing store files are initialized only as a consequence of a successful write operation, not a read-only operation.

## Out of Scope

- Multi-user access
- Concurrency control
- A web UI
- Due dates
- Authentication
