# Tasks: Smart Todo

## Phase 1: Public Modules and State Foundation

- [ ] T001 Create the public exception hierarchy with `TodoError`, `ValidationError`, `TaskNotFoundError`, `InvalidTransitionError`, and `StorageError` in `src/todo/errors.py`; align exports and inheritance with the public API contract. Implements: FR-12, NFR-7.
- [ ] T002 Create `TaskService` with the exact approved constructor and public method signatures in `src/todo/service.py`, preserving copy isolation for returned task dictionaries. Implements: FR-1 through FR-9, FR-12, NFR-7.
- [ ] T003 Implement package initialization and public surface in `src/todo/__init__.py` without adding unspecified convenience APIs. Implements: FR-12, NFR-3, NFR-7.
- [ ] T004 Implement pure input validators for task ids, titles, priorities, tags, statuses, sort modes, and list filters, keeping each helper below cyclomatic complexity 10. Implements: FR-2, FR-3, FR-4, FR-5, FR-8, FR-9, NFR-2.
- [ ] T005 Implement store and task shape validation for the exact version 1 root and task schemas, including type guards that reject booleans where integers are required. Implements: FR-10, FR-11, NFR-2.

## Phase 2: Persistence and Corruption Safety

- [ ] T006 Implement the reload operation for every service method, using a missing file as mutation-only initial state and never creating a file for read-only operations. Implements: FR-10, FR-11.
- [ ] T007 Reject empty files, malformed JSON, wrong JSON roots, invalid task entries, and corrupt store invariants with `StorageError` without modifying the file. Implements: FR-11, NFR-5.
- [ ] T008 Implement atomic same-directory persistence using `tempfile.mkstemp`, JSON serialization, flush/close, and `os.replace`, including POSIX owner-only mode 0600 where supported. Implements: FR-10, NFR-6, NFR-7.
- [ ] T009 Implement save failure cleanup and preservation behavior so `StorageError` leaves the existing destination byte-identical and removes temporary files. Implements: FR-10, NFR-3.
- [ ] T010 Implement the exact persisted root shape `{"version":1,"next_id":int,"tasks":[...]}` and enforce monotonic `next_id` invariants across restarts. Implements: FR-10, FR-7, FR-1.

## Phase 3: Service Operations

- [ ] T011 Implement `add_task` with title stripping, medium priority default, empty tags default, UTC ISO-8601 creation timestamps, sequential ids, and persisted task copies. Implements: FR-1, FR-2, FR-3, FR-4, FR-10.
- [ ] T012 Prevent failed adds from consuming an id by completing title, priority, tag, and state validation before allocation or mutation. Implements: FR-2, FR-3, FR-4, FR-10.
- [ ] T013 Implement normalized tag handling for add and update: lowercase and strip values, enforce ASCII regex and distinct-tag limits, and preserve first-occurrence order. Implements: FR-4, FR-9.
- [ ] T014 Implement `get_task` id validation and lookup behavior, including rejection of bool and non-int ids and `TaskNotFoundError` for unknown integer ids. Implements: FR-5, FR-11.
- [ ] T015 Implement `update_task` field-selection semantics, required-field validation, partial updates, explicit `tags=[]` clearing, and immutable `status`/`created_at` fields. Implements: FR-6, FR-4, FR-3, FR-10.
- [ ] T016 Complete update validation before mutation or persistence so invalid updates leave state unchanged and unknown ids follow lookup rules. Implements: FR-6, FR-5, FR-11.
- [ ] T017 Implement `delete_task`, removing only the requested existing task while retaining `next_id` so deleted and highest ids are never reused. Implements: FR-7, FR-10.
- [ ] T018 Implement `set_status` with exact valid statuses, the five allowed transitions, same-status rejection, and leave-state-unchanged behavior for invalid transitions. Implements: FR-8, FR-5, FR-10.
- [ ] T019 Implement `list_tasks` with case-insensitive exact-match tag filtering, status filtering, combinable filters, priority ordering, id ordering, and empty-list results. Implements: FR-9, FR-10.
- [ ] T020 Ensure every service mutation reloads and validates persisted state, mutates only a copied task/list state, and persists through the atomic save routine. Implements: FR-10, FR-11, FR-1 through FR-9.
- [ ] T021 Ensure all service results expose exactly the six task keys and deep-copy nested tags, even when tasks come from persisted state. Implements: FR-1, FR-6, FR-8, FR-9, FR-10.

## Phase 4: CLI and Entry Point

- [ ] T022 Implement the argparse command grammar for `add`, `get`, `edit`, `delete`, `status`, and `list`, with `[--file PATH]` and default `tasks.json`. Implements: FR-12, FR-1 through FR-9.
- [ ] T023 Implement repeatable `--tag` arguments for `add` and `edit`, passing each occurrence as one tag while preserving commas as ordinary tag characters. Implements: FR-12, FR-4.
- [ ] T024 Implement CLI dispatch for successful task, list, and delete operations and serialize exactly one JSON document to stdout. Implements: FR-12.
- [ ] T025 Implement CLI `TodoError` handling so failures print only `error: <message>` to stderr, emit no stdout, and return exit code 2. Implements: FR-12.
- [ ] T026 Implement `todo.cli.main(argv=None)` so it returns 0 for success or 2 for `TodoError` and never calls `sys.exit`. Implements: FR-12, NFR-2.
- [ ] T027 Implement `todo/__main__.py` module execution and propagate the integer result from `todo.cli.main` as the process exit status. Implements: FR-12.

## Phase 5: Quality, Security, and Verification

- [ ] T028 Add or adjust human-owned test coverage for public API signatures, exact task/store shapes, copy isolation, and persistence across service instances. Implements: FR-1 through FR-12, NFR-4.
- [ ] T029 Add or adjust verification coverage for corruption detection, read-only missing-file behavior, atomic failure cleanup, id non-reuse, and status-transition boundaries. Implements: FR-5, FR-7, FR-8, FR-10, FR-11, NFR-4.
- [ ] T030 Add or adjust verification coverage for CLI grammar, repeatable tags, exact stdout/stderr contracts, and exit codes. Implements: FR-12, NFR-4.
- [ ] T031 Keep all implementation functions at cyclomatic complexity 10 or less and decompose validation or dispatch branches rather than suppressing complexity. Implements: NFR-1, NFR-2.
- [ ] T032 Keep `ruff check src tests` free of all constitution findings, including E, F, W, I, B, S, UP, C90, line length 100, and complexity limits. Implements: NFR-1, NFR-2.
- [ ] T033 Verify `bandit -r src` reports zero MEDIUM or HIGH findings and avoid prohibited or unsafe filesystem/network patterns. Implements: NFR-3, NFR-5.
- [ ] T034 Verify line coverage of `src/todo` is at least 90%. Implements: NFR-4.
- [ ] T035 Verify runtime imports and package dependencies are limited to the Python standard library and contain no required third-party runtime dependency. Implements: NFR-7.
- [ ] T036 Perform a repository secret scan and verify no secrets, tokens, credentials, or private keys are added. Implements: NFR-5.
- [ ] T037 Verify created data files have POSIX owner-only permissions 0600 where POSIX permissions are applicable. Implements: NFR-6.
- [ ] T038 Run the complete human-owned pytest and harness acceptance gate, confirming every FR and NFR acceptance criterion is exercised without edits to test or harness assets. Implements: FR-1 through FR-12, NFR-1 through NFR-7.
