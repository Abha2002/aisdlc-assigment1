Python 3.11. Package `src/reminder/`: `errors.py`, `agent.py` (public `handle`), `prompts.py` or `prompts/*.txt` for the
system prompt. Use the official `anthropic` SDK; model from env `REMINDER_MODEL` (default `claude-haiku-5-5`),
temperature from `REMINDER_TEMPERATURE` (default 0.3; if the API rejects the parameter, omit it and set TEMPERATURE to
None). API key only from `ANTHROPIC_API_KEY`; if missing, or on API/timeout/rate-limit errors, raise ModelServiceError.
Flow: validate/short-circuit blank input locally -> build prompt (pass now, tz, existing reminders, and the schema;
ask for JSON only) -> call model -> extract and parse JSON -> validate against the OSC-1 schema and INV rules in code ->
if the model output is unparseable or violates a rule, retry at most once, then return a safe `clarify` object rather than
invalid output. Never execute actions. Do not read or write anything under evals/, tests/ or .harness/.
