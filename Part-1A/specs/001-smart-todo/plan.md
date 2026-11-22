# Implementation Plan: Smart Todo

**Branch**: `001-smart-todo` | **Date**: 2026-11-22 | **Spec**: `spec.md`

## Summary

Implement a small Python 3.11 task manager with a service API and argparse CLI. State is persisted in one JSON document. Validation is isolated in small pure helpers, each operation reloads and validates state, mutates an in-memory copy only after validation, and atomically replaces the store. The implementation is confined to `src/todo/{__init__,__main__,errors,service,cli}.py` and is traceable to FR/NFR identifiers.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Python standard library only at runtime; no third-party imports.

**Storage**: One JSON file at the path supplied to `TaskService`, default `tasks.json` for the CLI.

**Testing**: pytest and pytest-cov; human-owned tests and harnesses remain untouched.

**Target Platform**: Local command-line environment on POSIX or Windows; POSIX 0600 permissions are required where supported.

**Project Type**: Small standalone CLI and Python service package.

**Performance Goals**: Small local store; no performance target beyond deterministic local operations.

**Constraints**:
- Runtime standard library only.
- Ruff rules E, F, W, I, B, S, UP, C90; 100-character lines; cyclomatic complexity <= 10.
- Bandit zero MEDIUM/HIGH findings.
- Line coverage of `src/todo` >= 90%.
- Atomic writes, copy isolation, corruption rejection, and no temp leftovers.
- No changes under `tests/` or `.harness/`.

## Constitution Check

- **Spec-first**: PASS — every implementation unit and behavior is mapped to FR/NFR requirements.
- **Independent oracle**: PASS — no planned edits to tests or harness; no suppression comments.
- **Quality**: PASS, pending implementation — design keeps functions small and complexity <= 10.
- **Security**: PASS, pending implementation — standard-library JSON and filesystem operations; no prohibited APIs or credentials.
- **Test gate**: PASS, pending implementation — human-owned pytest suite and coverage gate remain authoritative.
- **Dependencies**: PASS — runtime imports are standard-library only.
- **Determinism**: PASS — store reload, stable sorting, and explicit normalized values; timestamps are the only exempt nondeterminism.
- **Persistence safety**: PASS — same-directory `mkstemp`, permissions, write, flush/fsync as appropriate, and `os.replace`.
- **Accountability**: PASS — harness output requires later human ACCEPT/REJECT.

## Implementation Design

### Module responsibilities

- `todo/errors.py`: exception hierarchy only.
- `todo/service.py`: pure validation helpers, state loading and shape validation, in-memory mutations, sorting/filtering, and atomic persistence. Public `TaskService` methods preserve exact signatures.
- `todo/cli.py`: argparse parser construction and dispatch; catches `TodoError`; writes JSON to stdout or an error line to stderr and returns an exit code.
- `todo/__main__.py`: calls `cli.main()` and converts its return value to process exit status without making CLI behavior unavailable to direct `main(argv=None)` calls.
- `todo/__init__.py`: package initialization only; no unspecified public convenience API.

### State lifecycle

1. Each operation loads the JSON file.
2. A missing file is treated as a writable initial state for mutation operations and as no data for read-only operations without creating the file.
3. Existing files are accepted only as shape `{"version":1,"next_id":int,"tasks":[...]}` with well-formed task entries and a valid `next_id` invariant.
4. Empty, invalid JSON, or wrong shape raises `StorageError` and remains unmodified.
5. Mutations validate all inputs before changing the loaded state.
6. Successful mutations increment or update state and call atomic save.
7. Returned task dicts are deep copies, including the tags list.

### Atomic storage

The save routine creates a same-directory temporary file via `tempfile.mkstemp`, applies POSIX 0600 permissions, serializes deterministic JSON, flushes and closes the file, and calls `os.replace(temp_path, final_path)`. Any failure raises `StorageError`, removes the temp path if present, and leaves the original destination unchanged. Because replacement is atomic, an existing file is not truncated before replacement succeeds.

### Validation strategy

Small pure helpers validate and normalize:
- id (reject bool and non-int), title, priority, tags, status, sort mode, and list filters.
- store shape and task shape.
- allowed status transitions.

Validation occurs before task lookup/mutation only as required by each operation and before each save.

## Project Structure

### Documentation (this feature)

```text
specs/001-smart-todo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── public-api.md
```

### Source Code (repository root)

```text
src/
└── todo/
    ├── __init__.py
    ├── __main__.py
    ├── errors.py
    ├── service.py
    └── cli.py
```

### Human-owned test assets

```text
tests/
.harness/
```

No implementation work modifies these directories.

## Complexity Tracking

No constitution exemption is expected. Any function above complexity 10 must be decomposed into smaller pure helpers rather than justified or suppressed.

