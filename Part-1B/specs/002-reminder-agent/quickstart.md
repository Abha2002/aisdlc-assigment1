# Quickstart Validation Guide

## Prerequisites

- Python 3.11
- The project virtual environment
- `anthropic` and `tzdata` installed
- `ANTHROPIC_API_KEY` set only in the shell for live model validation

```powershell
py -3.11 -m venv .venv
. .venv/Scripts/Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Offline Contract Validation

Run the existing offline tests. These must verify blank handling and the missing-key path without making a model call.

```powershell
python -m pytest
```

Do not modify `tests/test_agent_offline.py` or any oracle artifact to make the result pass.

## Live or Evaluated Validation

Before the first evaluation, the human-owner lock step must remain in place:

```powershell
python .harness\lock.py
python .harness\run_eval.py --label initial --runs 3
```

Live validation is successful only when all thresholds remain unchanged and every service outage is reported as INCONCLUSIVE or failure.

## Minimum Scenario Matrix

1. **Blank text**: no model call and no fabricated create result.
2. **Create**: valid title, future datetime, offset-matching IANA timezone, recurrence as specified.
3. **Relative time**: resolve "in 2 hours" from supplied `now`.
4. **Elapsed same-day clock**: move to the next allowed occurrence.
5. **Recurrence**: map every day/week/month to `daily`/`weekly`/`monthly`.
6. **Named timezone**: override the default timezone rather than silently replacing it.
7. **Ambiguous reschedule/snooze**: clarify, never guess an existing target.
8. **Past or over-horizon date**: clarify.
9. **Unsupported action**: refuse.
10. **Prompt injection or secret**: preserve a valid safe object and never echo the instruction or secret.
11. **Malformed model JSON**: retry once, then return safe clarify.
12. **Missing key or API outage**: raise `ModelServiceError`.

See [the public API contract](contracts/public-api.md) and [the data model](data-model.md) for exact result requirements.
