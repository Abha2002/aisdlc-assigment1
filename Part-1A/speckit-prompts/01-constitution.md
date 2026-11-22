Create a constitution for a small Python 3.11 project, "Smart Todo", a task manager with a service
layer and a CLI. Principles must be measurable and enforceable by an automated harness:

1. Spec first: all code traces to an approved spec requirement id (FR-n / NFR-n). No unspecified features.
2. Test oracle independence: tests in `tests/` and everything in `.harness/` are owned by the human.
   The coding agent MUST NOT edit, delete, skip, xfail or weaken them, must not edit the specification
   or constitution to make checks pass, and must not add `# noqa`, `# nosec` or any lint/security suppression.
3. Quality gate: `ruff check src tests` reports zero findings with rules E,F,W,I,B,S,UP,C90, line length 100,
   cyclomatic complexity <= 10 per function.
4. Security gate: `bandit -r src` reports zero MEDIUM or HIGH findings. No secrets, tokens or credentials in the
   repository. No `eval`, `exec`, `pickle`, `shell=True`, or unsafe deserialisation.
5. Test gate: all tests pass and line coverage of `src/todo` is >= 90%.
6. Dependencies: runtime uses the Python standard library only.
7. Determinism: given the same inputs and file contents, every operation yields the same result
   (timestamps excepted).
8. Persistence safety: writes are atomic and never corrupt existing data; the data file is created owner-only (0600).
9. Human accountability: a human records ACCEPT/REJECT after the harness PASS. Failures are fixed at the root
   cause, never by changing the oracle.
