# Part 1B workflow checklist (you run these; keep every generated artifact)

Setup:
1. `python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt`
2. `export ANTHROPIC_API_KEY=...` (shell only — never commit it, never put it in a file in the repo).
   Optional: `export REMINDER_MODEL=claude-haiku-5-5` `export REMINDER_TEMPERATURE=0.3`
   No Anthropic key? Any provider works if `reminder.agent.handle` keeps the same interface; record the provider.
3. `specify init . --ai <your-agent>`; review `evals/` (dataset, thresholds, requirements) and `.harness/`,
   make sure `evals/thresholds.json` matches the threshold written in your spec, then
   **lock the oracle before any implementation**: `python .harness/lock.py` and commit.

Spec Kit sequence: constitution (01) -> specify (02) -> clarify (03) -> plan (04) -> tasks -> analyze -> implement (05).
If you change the spec's behaviour/threshold *before the first evaluation*, change the matching `evals/` file,
re-lock, and log it. After the first evaluation, the threshold and expected results are frozen.

After /speckit.implement:
- `cp -r src prompts evidence/initial-generation/ && git tag initial-generation`
- `python -m pytest` (evaluator + offline contract tests; no API calls)
- `python .harness/run_eval.py --label initial --runs 3`
  PASS -> human review.  FAIL -> give `evidence/eval-runs/initial/feedback.md` to the agent, let it repair
  `src/`/`prompts/` only, then `--label repair-1`, ...  INCONCLUSIVE -> model/service outage: wait and rerun; it is
  NOT an application failure and not evidence of a repair cycle.
- Final: `python .harness/run_eval.py --label final --runs 3 --final` (writes `evidence/eval-results.json`),
  `cp -r src prompts evidence/final-generation/`.
- Write `evidence/harness-log.md` yourself, from what actually happened. Do not invent failures.
