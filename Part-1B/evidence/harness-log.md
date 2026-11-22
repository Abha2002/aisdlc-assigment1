# Part 1B — harness-log.md  (WRITE THIS YOURSELF from your real runs; delete the hints)

## 1. Model / configuration (no secrets)
- Provider, model id, temperature, runs per case, Python version, date:
- Prompt/system-instruction version (commit):

## 2. Threshold and scoring (as declared in the spec BEFORE first evaluation)
- Thresholds (copy from evals/thresholds.json) and where in the spec they were declared (commit/date):
- Scoring method in your own words:

## 3. Evaluation runs
| Label | Date | Decision | structural | invariant | guardrail | mean semantic | aggregate | Service errors |
|---|---|---|---|---|---|---|---|---|
(copy from evidence/eval-runs/<label>/eval-results.json — do not hand-edit results)

## 4. Meaningful failures and repair (only real ones)
For each: case id, requirement id, generated output, which layer failed, evidence given to the agent
(`feedback.md` path), what changed in src/prompts, re-evaluation result, whether the root cause was fixed
without touching evals/thresholds/guardrails.

## 5. Model/service failures (distinct from application failures)
Any INCONCLUSIVE runs, errors seen, and what you did.

## 6. Final human review
- Decision: ACCEPT / REJECT
- Justification (cases you inspected by hand beyond the score):
- Known limitations and residual risks:
