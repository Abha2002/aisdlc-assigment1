Build "Smart Todo": a task manager with a Python service API and a CLI, persisting to a JSON file.
Use exactly these requirement ids so tests can trace to them.

Public interface (must match exactly; the human-owned tests import these names):
- `todo/errors.py`: `TodoError(Exception)`, and subclasses `ValidationError`, `TaskNotFoundError`,
  `InvalidTransitionError`, `StorageError`.
- `todo/service.py`: `class TaskService(path)` with methods
  `add_task(title, priority="medium", tags=None) -> dict`, `get_task(task_id) -> dict`,
  `update_task(task_id, title=None, priority=None, tags=None) -> dict`, `delete_task(task_id) -> None`,
  `set_status(task_id, new_status) -> dict`, `list_tasks(tag=None, status=None, sort="priority") -> list[dict]`.
- `todo/cli.py`: `main(argv=None) -> int` (returns exit code, does not call sys.exit); `todo/__main__.py`
  makes `python -m todo` work. Source lives under `src/todo/`.

A task is a dict with EXACTLY the keys: id (int), title (str), priority, status, tags (list[str]),
created_at (ISO-8601 string with timezone offset, UTC). Returned dicts are copies of stored data.

Functional requirements (each acceptance criterion is binary):
- FR-1 Create: `add_task` returns the new task with status "todo", default priority "medium", tags [], and id
  assigned sequentially starting at 1.
- FR-2 Title: stripped of surrounding whitespace; must be a str of 1..100 chars after stripping, else ValidationError.
  A failed add must not consume an id.
- FR-3 Priority: exactly one of "low","medium","high" (lowercase, case-sensitive), else ValidationError.
- FR-4 Tags: must be a list of str. Each tag is stripped and lower-cased, must match [a-z0-9-]{1,20}, duplicates
  removed keeping first occurrence order, at most 10 distinct tags; otherwise ValidationError.
- FR-5 Read: `get_task` returns the task; unknown id (including 0 and negatives) -> TaskNotFoundError;
  non-int id (incl. bool, str, float, None) -> ValidationError.
- FR-6 Update: only provided (non-None) fields change; `tags=[]` clears tags; at least one field is required
  (else ValidationError); validation happens before any change (invalid update leaves task unchanged);
  status and created_at are never changed by update; unknown id -> TaskNotFoundError.
- FR-7 Delete: removes the task; ids are never reused, even after deleting the highest id and across restarts.
- FR-8 Status: values "todo","in_progress","done". Allowed transitions only: todo->in_progress, todo->done,
  in_progress->todo, in_progress->done, done->todo. Any other change (including to the same status) raises
  InvalidTransitionError and leaves the task unchanged; unknown status value -> ValidationError.
- FR-9 List: optional `tag` filter (case-insensitive exact match on normalised tags), optional `status` filter,
  both combinable; `sort="priority"` orders high, medium, low then by id ascending; `sort="id"` orders by id
  ascending; any other sort or status value -> ValidationError; no matches -> [].
- FR-10 Persistence: all state is stored in one JSON file given by `path` (shape:
  {"version":1,"next_id":int,"tasks":[...]}). Writing is atomic (temp file in the same directory, then os.replace);
  a failed write raises StorageError, leaves the previous file byte-identical and leaves no temp files.
  Read-only operations do not create the file. State persists across TaskService instances.
- FR-11 Corruption: an empty file, invalid JSON, or JSON of the wrong shape raises StorageError on every operation
  and the file is never modified or overwritten.
- FR-12 CLI: `python -m todo [--file PATH] <command>` (default file `tasks.json`) with commands
  add TITLE [--priority P] [--tag T ...]; get ID; edit ID [--title] [--priority] [--tag T ...];
  delete ID; status ID NEW_STATUS; list [--tag T] [--status S] [--sort priority|id].
  Success: print one JSON document (task, list, or {"deleted": ID}) to stdout, exit code 0.
  Any TodoError: print `error: <message>` to stderr, nothing to stdout, exit code 2.

Non-functional requirements:
- NFR-1 ruff clean (see constitution). NFR-2 complexity <= 10. NFR-3 bandit: zero MEDIUM/HIGH.
- NFR-4 coverage >= 90% of src/todo. NFR-5 no secrets in repo. NFR-6 data file permissions 0600 on POSIX.
- NFR-7 runtime depends on the standard library only.

Out of scope: multi-user access, concurrency control, a web UI, due dates, authentication.
