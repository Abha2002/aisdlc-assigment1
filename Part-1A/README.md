# Part 1A — Smart Todo (deterministic) with Spec Kit + harness

## Run the harness
```bash
python -m venv .venv && . .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python .harness/lock.py                            # human-only, once, before implementation
python .harness/run_harness.py --label <name>      # exit 0 = PASS
```
Results land in `evidence/harness-results/<name>/`; on FAIL, `feedback.md` is the structured evidence for the agent.
Gates: G0 integrity (tests/harness unchanged), G1 ruff, G2 bandit, G3 secret scan, G4 pytest + coverage >= 90%.

See `speckit-prompts/00-WORKFLOW.md` for the Spec Kit sequence.
