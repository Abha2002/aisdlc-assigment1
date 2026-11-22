# Public API Contract

## Exceptions

`todo.errors` MUST export:

- `TodoError(Exception)`
- `ValidationError(TodoError)`
- `TaskNotFoundError(TodoError)`
- `InvalidTransitionError(TodoError)`
- `StorageError(TodoError)`

## Service

`todo.service.TaskService(path)` MUST implement:

- `add_task(title, priority="medium", tags=None) -> dict`
- `get_task(task_id) -> dict`
- `update_task(task_id, title=None, priority=None, tags=None) -> dict`
- `delete_task(task_id) -> None`
- `set_status(task_id, new_status) -> dict`
- `list_tasks(tag=None, status=None, sort="priority") -> list[dict]`

Task dict keys are exactly `id`, `title`, `priority`, `status`, `tags`, and `created_at`. Returned dicts are copies.

## CLI

`todo.cli.main(argv=None) -> int` MUST return rather than call `sys.exit`.

Supported syntax:

```text
python -m todo [--file PATH] add TITLE [--priority P] [--tag T ...]
python -m todo [--file PATH] get ID
python -m todo [--file PATH] edit ID [--title TITLE] [--priority P] [--tag T ...]
python -m todo [--file PATH] delete ID
python -m todo [--file PATH] status ID NEW_STATUS
python -m todo [--file PATH] list [--tag T] [--status S] [--sort priority|id]
```

The default file is `tasks.json`. `--tag` is repeatable for `add` and `edit`; comma-separated values are not separators.

Successful output is exactly one JSON document: a task, a task list, or `{"deleted": ID}`. Successful exit code is 0.

Any `TodoError` produces no stdout, writes `error: <message>` to stderr, and returns exit code 2.

## Module Entry Point

`todo/__main__.py` MUST make `python -m todo` execute `todo.cli.main` and propagate its integer exit code.
