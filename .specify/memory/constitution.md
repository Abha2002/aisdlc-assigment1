# Smart Todo Constitution

## Core Principles

### I. Spec-First Implementation
All implementation work, including code and public behavior, MUST trace to an approved requirement identifier (`FR-n` or `NFR-n`). Every feature, CLI command, service operation, and configuration behavior MUST have a corresponding approved requirement. No agent-created, unspecified, or convenience feature is permitted. Traceability MUST be verifiable against the approved specification and the implementation before a change is accepted.

### II. Independent Test Oracle
The contents of `tests/` and everything in `.harness/` are human-owned test oracles. The coding agent MUST NOT edit, delete, skip, xfail, weaken, or work around those tests or harness assets. The coding agent MUST NOT edit the specification or constitution to make a check pass. The coding agent MUST NOT add `# noqa`, `# nosec`, or any other lint or security suppression. Oracle and gate outcomes are authoritative evidence of implementation correctness.

### III. Python Quality Gate
Implementation MUST use Python 3.11. The quality gate is `ruff check src tests` and MUST report zero findings for rules `E`, `F`, `W`, `I`, `B`, `S`, `UP`, `C90`, a maximum line length of 100 characters, and a cyclomatic complexity of no more than 10 per function. Any violation blocks acceptance.

### IV. Security Gate
`bandit -r src` MUST report zero MEDIUM or HIGH findings. No secrets, tokens, credentials, private keys, or credential-bearing configuration may exist in the repository. Source code MUST NOT use `eval`, `exec`, `pickle`, `shell=True`, or unsafe deserialisation. These requirements are mandatory and may not be suppressed.

### V. Test and Coverage Gate
The complete automated test suite MUST pass. Line coverage for `src/todo` MUST be at least 90%, as measured by the project's coverage tooling. A passing harness, test suite, or coverage report may not be produced by excluding tests, weakening assertions, masking failures, or changing coverage scope outside the approved configuration.

### VI. Standard-Library Dependency Boundary
The Smart Todo runtime MUST use only the Python standard library. No third-party runtime package may be introduced or imported. Development and test dependencies may be used only in the development environment and MUST NOT become runtime dependencies.

### VII. Deterministic Behavior
Given identical inputs and file contents, every service and CLI operation MUST yield the same observable result, excepting explicitly permitted timestamp values. Operations MUST NOT depend on random, unordered, locale-dependent, ambient-time, or externally mutable behavior unless an approved requirement explicitly permits it.

### VIII. Persistence Safety
All writes that update persisted task data MUST be atomic and MUST prevent corruption or loss of existing valid data on write failure. The data file MUST be created with owner-only permissions (`0600`). Any persistence implementation or migration MUST preserve these guarantees and verify or enforce the required permissions.

### IX. Human Accountability and Root-Cause Fixing
A human MUST record `ACCEPT` or `REJECT` after an automated harness reports PASS. A rejected or failing result MUST be fixed at its root cause in the implementation, specification-approved behavior, or build configuration. Failures MUST never be resolved by changing tests, harnesses, oracle data, specification wording, constitution wording, or gate settings to obtain a pass.

## Additional Constraints

- Smart Todo MUST remain a small Python 3.11 project with a service layer and a CLI.
- The implementation SHOULD preserve clear separation between service-domain behavior and CLI presentation.
- Generated artifacts, local state, caches, credentials, and test databases MUST NOT be committed to the repository.
- Any change to a gate, dependency policy, persistence guarantee, or security prohibition requires an approved constitution amendment and MUST remain measurable and enforceable.

## Development Workflow

- Before implementation, approved `FR-n` and `NFR-n` requirements MUST identify the behavior to be added or changed.
- Changes MUST include or update only specification-approved implementation and documentation.
- Before human acceptance, the coding agent MUST run or verify the applicable automated quality, security, test, and coverage gates.
- Any gate failure is a blocking condition until its root cause is corrected.
- Human review is required before final acceptance; a harness PASS alone is insufficient for ACCEPT.

## Governance

This constitution supersedes informal practices and non-approved requirements. It may be amended only through explicit human approval of a documented, measurable change. Amendments must preserve automated enforceability and must not relax, bypass, or invalidate existing human-owned oracles. All implementations and pull requests must be checked against every applicable principle. Unresolved ambiguity MUST be returned to a human for specification clarification rather than resolved by inventing behavior.

**Version**: 1.0.0 | **Ratified**: 2026-11-22 | **Last Amended**: 2026-11-22
