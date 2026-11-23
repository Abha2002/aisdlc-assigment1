# Reminder Agent Constitution

## Core Principles

### I. Spec First

Every behavior MUST trace to one or more specification requirement IDs: `OSC-n`, `INV-n`, `BP-n`, `GR-n`, or `EVAL-n`. Each feature or behavior change MUST identify its applicable IDs and acceptance criteria in the specification before implementation. Behavior without a requirement ID MUST NOT be implemented.

### II. Oracle Independence

`evals/`, `tests/`, and `.harness/` are human-owned. The coding agent MUST NOT edit, remove, or weaken benchmark cases, expected results, thresholds, evaluators, or tests, and MUST NOT disable or loosen a guardrail to obtain a pass. Application repairs may change only `src/` and `prompts/`. A harness integrity failure MUST be treated as a failed evaluation, not bypassed.

### III. Bounded Non-Determinism

Model wording may vary, but output schema, applicable invariants, and guardrails MUST pass on every successful sample. Evaluation MUST use human-owned ground truth and thresholds declared before the first evaluation. A run passes only when all thresholds in `evals/thresholds.json` are met: aggregate semantic score >= `0.85`, per-case semantic score >= `0.70`, and structural, invariant, and guardrail pass rates each equal `1.0`. Structural, invariant, or guardrail failures MUST NOT be offset by higher semantic scores. Service errors MUST be reported as failures or inconclusive results, never omitted to manufacture a pass.

### IV. Untrusted Model Output; No Actions

The application MUST parse and validate every model response against the fixed JSON schema (`OSC-1`) and enforce applicable invariants and guardrails before returning it. It MUST NOT execute model-requested actions, including deleting reminders, sending email, or calling tools. It only returns a validated reminder description or a specified clarification/refusal result.

### V. Secret Handling

API keys MUST come only from environment variables. Secrets MUST NOT appear in code, prompts, logs, evaluation evidence, returned output, or git history. Secrets included in user text MUST NOT be echoed (`GR-3`).

### VI. Explicit Service-Failure Taxonomy

Model/service timeouts, HTTP 5xx errors, rate limits, and a missing API key MUST raise `reminder.errors.ModelServiceError`. These failures MUST NOT be converted into a fabricated reminder or any other success-shaped result. Evaluation outages MUST remain visibly inconclusive or failed, not pass.

### VII. Deterministic Local Handling

Blank input and clearly invalid input MUST be handled locally without a model call. Offline tests MUST verify these behaviors and confirm that no model call is made.

### VIII. Human Accountability

A harness PASS is necessary but not sufficient for acceptance. After PASS, a human MUST record `ACCEPT` or `REJECT` and document known limitations. A coding agent MUST NOT record human acceptance. A failed or inconclusive harness run MUST NOT be recorded as accepted.

## Technical Constraints

- The project targets Python 3.11.
- Requirement identifiers and their definitions are maintained in the specification and evaluation requirements.
- Thresholds and evaluation rules are controlled by the human-owned oracle; they MUST NOT be changed by the coding agent to obtain a pass.
- The application returns structured reminder JSON only; it does not perform reminder actions.

## Development and Acceptance Workflow

1. Identify the applicable requirement IDs before implementation.
2. Keep changes within `src/` and `prompts/`; do not modify human-owned oracle files.
3. Run the existing tests and evaluation harness without changing their cases, expected results, thresholds, evaluators, or guardrails.
4. Report PASS, FAIL, or INCONCLUSIVE accurately, including service failures and known limitations.
5. After a PASS, obtain and record a human `ACCEPT` or `REJECT` decision with known limitations.

## Governance

This constitution governs specification, implementation, evaluation, and acceptance. Amendments require human approval. The oracle-independence and no-action principles MUST NOT be waived by the coding agent. Reviews MUST verify requirement traceability, oracle integrity, threshold compliance, secret handling, honest failure reporting, and human-recorded acceptance.

**Version**: 1.0.0 | **Ratified**: 2026-11-23 | **Last Amended**: 2026-11-23
