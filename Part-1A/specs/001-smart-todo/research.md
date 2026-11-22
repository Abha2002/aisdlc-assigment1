# Phase 0 Research: Smart Todo

## Decision 1: JSON persistence

**Decision**: Store state in one JSON file with the exact root shape `{version, next_id, tasks}`.

**Rationale**: It directly satisfies FR-10, is inspectable, uses the standard library, and can be validated consistently before every operation.

**Alternatives considered**: SQLite was rejected because the specification requires one JSON file and a compact standard-library file format. Pickle was prohibited.

## Decision 2: Load-modify-save per operation

**Decision**: Reload the JSON file for every service operation, validate and mutate only after validation, then atomically save mutations.

**Rationale**: It provides persistence across `TaskService` instances and ensures corruption is checked on every operation. Read-only operations never create a missing file.

**Alternatives considered**: Caching state in memory was rejected because it could become stale across service instances.

## Decision 3: Atomic replacement

**Decision**: Use `tempfile.mkstemp` in the destination directory, set POSIX 0600, write and close the temporary file, then `os.replace`.

**Rationale**: This is same-directory atomic replacement, satisfies FR-10, supports POSIX permissions, and ensures the destination is not truncated before replacement succeeds.

**Alternatives considered**: Direct `open(..., "w")` was rejected because failed writes can corrupt existing data. In-place replacement through an external tool was not needed.

## Decision 4: Pure validation helpers

**Decision**: Place title, priority, tag, id, status, sort, filter, and store-shape validation in small pure helpers in `service.py` or an internal section of that module.

**Rationale**: Pure helpers make exact rules testable and keep public operations below complexity 10. No extra public module or helper API is required.

**Alternatives considered**: Validation embedded in every public method would duplicate logic and increase complexity.

## Decision 5: Argparse CLI

**Decision**: Build the CLI with `argparse`, dispatch subcommands to `TaskService`, and catch only `TodoError` for the mandated error contract.

**Rationale**: Argparse is standard-library-only and supports the exact command grammar. `main(argv=None)` can remain independently testable and return an integer instead of exiting.

**Alternatives considered**: A manual parser was rejected because argparse provides consistent argument parsing and help behavior.

## Decision 6: Deterministic output

**Decision**: Preserve task key shape, use explicit priority/id sort keys, normalize tags, and serialize JSON consistently.

**Rationale**: The specification requires deterministic behavior apart from timestamps. Stable sorting and normalized values reduce implementation-dependent variation.

**Alternatives considered**: Set or dictionary iteration for tag/filter ordering was rejected because they do not guarantee the required first-occurrence or sort behavior.

