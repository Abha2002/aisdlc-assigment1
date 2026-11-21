# Part 1A workflow checklist (you run these; keep every generated artifact)

Setup (once, as in Lab Sheet 1):
1. Install deps: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt`
2. Run `specify init . --ai <your-agent>` in this folder (keeps the existing tests/ and .harness/).
3. Review `tests/` and `.harness/`, then **lock them**: `python .harness/lock.py` and commit.
   The locked tests are the independent oracle; the agent must not edit them.

Spec Kit sequence — paste each prompt file into the matching command:
| Step | Command | Prompt file |
|---|---|---|
| 1 | /speckit.constitution | 01-constitution.md |
| 2 | /speckit.specify | 02-specify.md |
| 3 | /speckit.clarify | 03-clarify.md (answer the questions yourself; record answers) |
| 4 | /speckit.plan | 04-plan.md |
| 5 | /speckit.tasks | (no extra prompt) |
| 6 | /speckit.analyze | (no extra prompt; read findings, fix upstream artifacts if needed) |
| 7 | /speckit.implement | 05-implement.md |

After step 7 (do NOT hand-edit the code first):
- `cp -r src evidence/initial-generation/` and `git tag initial-generation`
- `python .harness/run_harness.py --label initial`
- If FAIL: give `evidence/harness-results/initial/feedback.md` to the agent, let it fix `src/` only,
  rerun with `--label repair-1`, repeat as needed. Record each step in `evidence/harness-log.md`
  **in your own words**, from what actually happened. Do not invent a failure.
- When PASS: `cp -r src evidence/final-generation/`, review the code yourself, record ACCEPT/REJECT.

If you find an ambiguity or error in a requirement, change the *spec* artifact (not the tests), note it
in the log, and if the locked tests must change, re-run `lock.py` and document why.
