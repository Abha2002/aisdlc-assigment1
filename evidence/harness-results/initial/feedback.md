# Harness failure evidence (feed this file to the coding agent)

RULES FOR THE AGENT: fix the implementation in `src/` only. Do NOT edit `tests/`, `.harness/`, `pyproject.toml`, the spec or the constitution. Do NOT add lint/security suppressions (noqa, nosec) or lower any threshold. Then stop; the human re-runs the same harness.

## Gate G1 lint (ruff): FAIL
Command output (tail):
```
src\todo\__main__.py:3:1: I001 [*] Import block is un-sorted or un-formatted
src\todo\service.py:92:64: UP017 [*] Use `datetime.UTC` alias
src\todo\service.py:95:5: C901 `_validate_task` is too complex (11 > 10)
src\todo\service.py:209:40: UP017 [*] Use `datetime.UTC` alias
Found 4 errors.
[*] 3 fixable with `--fix`.
```
