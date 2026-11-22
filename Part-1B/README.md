# Part 1B — Natural-Language Reminder Agent (non-deterministic) with Spec Kit + one evaluation harness

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export ANTHROPIC_API_KEY=...            # shell only; never commit
python .harness/lock.py                 # human-only, before implementation
python -m pytest                        # evaluator + offline contract tests (no API calls)
python .harness/run_eval.py --label initial --runs 3
```
Pipeline: `evals/dataset.json` (21 cases) -> `reminder.agent.handle` -> schema (`schema_eval.py`) ->
invariants/guardrails (`property_eval.py`) -> semantic score (`quality_eval.py`) -> aggregate vs
`evals/thresholds.json` -> PASS / FAIL / INCONCLUSIVE (model outage). Results: `evidence/eval-runs/<label>/`.
Exit codes: 0 PASS, 1 FAIL, 3 INCONCLUSIVE, 4 oracle modified, 5 app not importable.
Note: `tests/test_agent_offline.py` only passes once the agent exists (it tests blank input and the no-key path).
