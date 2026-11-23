# Implementation Plan: Reminder Agent

**Branch**: `002-reminder-agent` | **Date**: 2026-11-23 | **Spec**: [Feature Specification](spec.md)

**Input**: Feature specification from `/specs/002-reminder-agent/spec.md`

## Summary

Implement a Python library entry point that converts reminder text, a reference instant, an IANA timezone, and optional existing reminders into exactly one OSC-1 intent object. The design uses the official `anthropic` SDK, local pre-validation, an authoritative prompt, strict JSON extraction and validation, one bounded retry for malformed or invariant-violating model output, and safe `clarify` fallback. No reminder action is executed.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Official `anthropic` SDK; `tzdata` for IANA timezone support

**Storage**: None; existing reminders are caller-provided transient input

**Testing**: Existing offline contract tests and human-owned evaluation harness; no modifications to `evals/`, `tests/`, or `.harness/`

**Target Platform**: Python package/library

**Project Type**: Single Python library

**Performance Goals**: At most two model calls for one `handle` invocation; local blank-input handling makes no model call

**Constraints**: API key is read only from `ANTHROPIC_API_KEY`; model name and temperature come from environment/configuration; model/service failures raise `ModelServiceError`; output must remain JSON-serializable and schema-valid

**Scale/Scope**: One public `handle` function and a small package under `src/reminder/`, with a system prompt under `prompts/` or `src/reminder/prompts/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan compliance |
|---|---|
| I. Spec First | Every implementation behavior is mapped to OSC, INV, BP, GR, or EVAL IDs in `research.md`, `data-model.md`, and the public contract. |
| II. Oracle Independence | Planning and implementation boundaries exclude `evals/`, `tests/`, and `.harness/`. |
| III. Bounded Non-Determinism | Output is schema-validated and invariant/guardrail checked; only one retry is allowed; evaluation thresholds remain unchanged. |
| IV. Untrusted Model Output; No Actions | Model text is parsed as untrusted data, never executed or used to call tools. |
| V. Secret Handling | The API key is environment-only and credentials embedded in request text are excluded from output. |
| VI. Explicit Service-Failure Taxonomy | Missing keys and API/timeout/rate-limit failures raise `ModelServiceError`; they are never success-shaped. |
| VII. Deterministic Local Handling | Blank input and structurally malformed service input are short-circuited locally. |
| VIII. Human Accountability | The plan does not record acceptance or alter harness results. |

**Gate result**: PASS. No constitution exception or waiver is proposed.

**Post-Phase-1 re-check**: PASS. The design keeps oracle files untouched, exposes only the fixed public contract, validates model output before return, limits retries to one, maps service failures to `ModelServiceError`, and performs no action execution.

## Project Structure

### Documentation (this feature)

```text
specs/002-reminder-agent/
├── spec.md
├── plan.md              # This file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── public-api.md
└── tasks.md             # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
src/reminder/
├── __init__.py
├── agent.py       # Public handle(text, now, tz, existing_reminders)
├── errors.py      # ModelServiceError
└── prompts.py or prompts/

prompts/           # Optional project-level system prompt location
```

**Structure Decision**: A single Python package is sufficient. Public behavior remains in `src/reminder/`; the prompt is maintained separately; implementation must not create or modify oracle directories.

## Complexity Tracking

No constitution violations require complexity tracking.
