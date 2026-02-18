# AGENTS.md

This file defines how AI agents should operate in this repository.

## Mission

Deliver correct changes fast by prioritizing context quality over prompt length.

## Non-negotiable workflow

1. Retrieve context first.
2. Cite evidence (`path:line`) before patching non-trivial tasks.
3. Make the smallest safe change.
4. Run validation commands.
5. Update memory/docs when durable knowledge changes.

## Context fetch order

1. `docs/architecture.md`
2. `docs/conventions.md`
3. `docs/testing.md`
4. `docs/system-context/index.md` (when task touches product/platform behavior)
5. Domain docs (`docs/*-patterns.md`, `docs/*-runbook.md`)
6. Relevant source files and tests
7. `docs/ai-memory.md` for previous decisions and gotchas

## Required output format for implementation tasks

1. Relevant evidence list with file references.
2. Patch summary.
3. Validation command results.
4. Risks and follow-ups.

## Validation policy

Always run, in this order if available:
1. Format/lint
2. Typecheck/static analysis
3. Targeted tests for changed scope
4. Full test suite or impacted pipeline checks

Use commands from `docs/runbook.md`.

## Change boundaries

- Do not modify unrelated files.
- Do not silently change APIs/contracts.
- If assumptions are required, state them explicitly.

## Project structure policy

- Use folder-first organization for integration domains with multiple responsibilities.
- Place provider code under `src/providers/<provider>/` and split by concern:
  - request/transport client logic
  - contract/schema definitions
  - mapping/normalization helpers (when needed)
- Place brokerage integrations under `src/brokerages/<broker>/` with one subpackage per broker (for example `webull`, `public`).
- Keep brokerage transport/API wrappers separate from runtime execution policy and order-routing logic.
- Place order-routing and execution decision logic under `src/trading/orders/`; do not embed broker strategy in Discord client adapters.
- Keep adapters thin (`discord_client`, provider adapters): parse/map/delegate only, with no dumped business policy blocks.
- Keep parser orchestration in parser modules and keep provider-specific protocol details in provider modules.
- Avoid single-file dumps for growing domains; introduce subpackages early when it improves navigation and ownership.

## Test structure policy

- Test modules (`test_*.py`) should contain tests only.
- Shared fixtures belong in `conftest.py`.
- Shared fakes/factories/payloads/helpers/datasets belong in `tests/testkit/`.
- Keep deterministic behavior tests in `tests/features/<feature>/(happy_path|edge_cases|contracts)`.
- Keep live/external checks in `tests/features/<feature>/smoke`.
- Keep class/module unit tests in `tests/unit/src/` mirroring `src/`.
- Keep test-runner/tooling tests in `tests/tooling`.
- Enforce purity with `python -m scripts.check_test_file_purity` in deterministic CI.

## Memory update rules

Update `docs/ai-memory.md` when discovering durable facts:
- Stable build/test commands
- Environment quirks
- Selector/test flakiness patterns
- CI failure signatures and fixes
- Architectural decisions

Every memory entry must include date and owner.

## Escalation triggers

Stop and ask for clarification when:
- Requirements conflict with existing conventions.
- Security/compliance boundaries are unclear.
- Multiple valid solutions have materially different trade-offs.

## Cursor integration note

- Treat `.cursor/rules/*.mdc` as scoped routing rules.
- Keep durable policy and standards in `AGENTS.md` and `docs/`.
- If a rule changes behavior expectations, update matching docs in `docs/`.
