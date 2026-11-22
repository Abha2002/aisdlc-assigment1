# Part 1A — harness-log.md  (WRITE THIS YOURSELF from your real runs; delete the hints)

## 1. Context
- Spec Kit version / coding agent + model used:
- Date, repo commit of the locked harness (`git rev-parse 6abe828`):
- Task/spec context given to the agent before generation (which commands, which artifacts):

## 2. Initial generation
- What `/speckit.implement` produced (files, tasks completed). Snapshot location: `evidence/initial-generation/`.

## 3. Harness executions
| Label | Date | G0 | G1 | G2 | G3 | G4 | Overall | Result folder |
|---|---|---|---|---|---|---|---|---|
(one row per run — copy from summary.json, do not hand-edit results)

## 4. Failure → repair cycle(s)  (only real failures)
For each: failing gate/test + requirement id, expected vs observed, the exact evidence you gave the agent
(`feedback.md` path), what changed in `src/`, re-run result (same gates), root cause fixed or symptom patched?

## 5. Specification changes (if any)
Which upstream artifact changed, why, and the history (commit).

## 6. Final human review
- Decision: ACCEPT / REJECT
- Justification (what you reviewed yourself in the code, beyond the harness):
- Known limitations / residual risks:
