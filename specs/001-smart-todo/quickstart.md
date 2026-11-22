# Quickstart Plan

## Development setup

1. Use Python 3.11.
2. Install development tools from `requirements-dev.txt` in a virtual environment.
3. Keep runtime code dependent only on the Python standard library.

## Implementation sequence

1. Add the exception hierarchy in `src/todo/errors.py`.
2. Implement pure validation and normalization helpers plus JSON loading/saving in `src/todo/service.py`.
3. Implement `TaskService` public operations and exact returned dict behavior.
4. Implement argparse command dispatch in `src/todo/cli.py`.
5. Add `src/todo/__main__.py` as the module entry point.
6. Export only implementation details that do not create unspecified public behavior.

## Verification sequence

Run the project quality and test gates without editing human-owned tests or harnesses:

```text
ruff check src tests
bandit -r src
pytest -q --cov=src/todo --cov-report=term-missing
python -m todo --file <path> <command>
```

The Python commands above are verification examples, not implementation artifacts.

## Acceptance checks

- Every public behavior maps to an FR/NFR requirement.
- Valid operations return exact task/list/deletion JSON shapes.
- TodoError CLI failures produce stderr text and exit code 2 with no stdout.
- Corrupt files are reported and never overwritten.
- Mutation writes are atomic and leave no temp files.
- Coverage is at least 90% for `src/todo`.
- Human records ACCEPT/REJECT after harness PASS; harness FAIL is fixed at the root cause.
