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
- Keep parser orchestration in parser modules and keep provider-specific protocol details in provider modules.
- Avoid single-file dumps for growing domains; introduce subpackages early when it improves navigation and ownership.

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
