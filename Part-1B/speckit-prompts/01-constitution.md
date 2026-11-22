Create a constitution for a small Python 3.11 project, "Reminder Agent": it converts natural-language reminder
requests into structured reminder JSON using an LLM. Principles must be measurable:

1. Spec first: behaviour traces to spec requirement ids (OSC-n, INV-n, BP-n, GR-n, EVAL-n).
2. Oracle independence: `evals/`, `tests/` and `.harness/` are human-owned. The coding agent MUST NOT edit, remove or
   weaken benchmark cases, expected results, thresholds, evaluators or tests, and must not disable or loosen a
   guardrail merely to pass. Repairs may only change `src/` and `prompts/`.
3. Non-determinism is bounded, not ignored: model wording may vary, but the output schema, invariants and
   guardrails must hold on EVERY sample. Quality is judged against ground truth with a declared threshold.
4. The application never trusts model output: it parses and validates it, and never executes any action
   (delete, send email, call tools) - it only returns a reminder description.
5. Secrets: API keys come only from environment variables; no secrets in code, prompts, logs, evidence or git.
6. Failure taxonomy: model/service failures (timeouts, 5xx, rate limits, missing key) raise
   `reminder.errors.ModelServiceError` and must never be converted into a fake "successful" result.
7. Determinism where possible: blank input and clearly invalid input are handled locally without a model call.
8. Human accountability: a human records ACCEPT/REJECT after the harness PASS, with known limitations.
