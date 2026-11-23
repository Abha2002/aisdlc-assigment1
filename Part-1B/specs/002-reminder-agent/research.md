# Research and Decisions

## Official Anthropic SDK

- **Decision**: Use `anthropic.Anthropic(api_key=...)` and its supported message API. Read configuration only from `ANTHROPIC_API_KEY`, `REMINDER_MODEL`, and `REMINDER_TEMPERATURE`.
- **Rationale**: This satisfies the official SDK requirement and keeps credentials and model configuration environment-controlled.
- **Alternatives considered**: Raw HTTP calls or a different SDK were rejected because they add protocol handling and do not satisfy the official-SDK constraint.
- **Requirement IDs**: OSC-2, OSC-3, BP-5, GR-3.

## Model Configuration

- **Decision**: Default `MODEL_NAME` to `claude-haiku-5-5` and default `TEMPERATURE` to `0.3`; set temperature from `REMINDER_TEMPERATURE`.
- **Decision**: If the SDK/API rejects the temperature parameter, remove it on a subsequent call in the same invocation and set module `TEMPERATURE` to `None`.
- **Rationale**: The temperature fallback supports model/API variants while recording the effective configuration.
- **Alternatives considered**: Retrying with the original temperature or failing immediately were rejected; one fallback is narrowly compatible and preserves the at-most-two-call retry budget.
- **Requirement IDs**: OSC-2, OSC-4.

## Prompt Contract

- **Decision**: Supply a system prompt containing the fixed schema, all supported intents, applicable OSC/INV rules, relative-time resolution rules, existing-reminder context, and instructions to emit JSON only.
- **Rationale**: Context and JSON-only output reduce ambiguity, while code validation remains authoritative.
- **Alternatives considered**: Asking the model to validate itself was rejected because it is not a security or correctness boundary.
- **Requirement IDs**: OSC-4 through OSC-10, INV-1 through INV-9, BP-1 through BP-6, GR-1 through GR-3.

## JSON Parsing and Retry

- **Decision**: Extract a single JSON object from model text, rejecting arrays and trailing/non-JSON content. Retry the model at most once if parsing or OSC/INV validation fails.
- **Decision**: After the first attempt, add a concise correction instruction requesting valid JSON and compliance with the original schema/rules. After a second failed attempt, return the safe fixed `clarify` object.
- **Rationale**: The retry recovers common formatting and rule violations without making model output indefinitely authoritative.
- **Alternatives considered**: Retrying more than once was rejected by the one-retry requirement; returning partial output was rejected by OSC-4.
- **Requirement IDs**: OSC-4 through OSC-10, INV-1 through INV-9, BP-3.

## Local Short-Circuiting

- **Decision**: Treat `None`, non-string values, or whitespace-only text as blank. Return or raise locally according to the public contract and offline test expectations: blank input must not call the model or create success/fabrication.
- **Rationale**: Constitution VII requires deterministic local handling and no model call.
- **Alternatives considered**: Sending blank input to the model was rejected.
- **Requirement IDs**: BP-3, OSC-4.

## Time and Zone Resolution

- **Decision**: The prompt receives the caller-supplied `now`, `tz`, existing reminders, and JSON schema. Code validation parses the returned offset and IANA timezone and verifies DST-correct offset consistency and horizon rules.
- **Rationale**: `now` and the supplied timezone are authoritative; code catches model clock assumptions and invalid offsets.
- **Alternatives considered**: Computing all semantic dates locally first was rejected because the agent must interpret natural language; local validation is retained as the final authority.
- **Requirement IDs**: BP-1, BP-2, INV-2, INV-9.

## Existing-Reminder Matching

- **Decision**: Reschedule/snooze target IDs are validated against the supplied list by exact ID membership. Ambiguous or absent matches produce `clarify`.
- **Rationale**: Exact IDs prevent guessing and ensure callers cannot cause arbitrary target IDs.
- **Alternatives considered**: Title-only or fuzzy output was rejected for targets with no exact unique match.
- **Requirement IDs**: INV-4, INV-5, BP-6.

## Service Failures

- **Decision**: Missing `ANTHROPIC_API_KEY`, timeouts, rate limits, API/HTTP 5xx-style errors, and SDK network/API failures are mapped to `ModelServiceError`.
- **Rationale**: The service failure taxonomy is explicit and prevents fabricated success results.
- **Alternatives considered**: Returning `clarify` for model/service outages was rejected because outages are service errors, while unparseable model text is an output-validation case.
- **Requirement IDs**: OSC-3, OSC-4, EVAL-5.
