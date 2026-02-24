# AGENTS.md

Agent operating guide for this repository. Keep it simple, accurate, and aligned with docs that are actively maintained.

## Mission

Ship correct changes fast, with clean structure and minimal churn.

## Context First (required)

Read in this order before non-trivial edits:

1. `docs/conventions.md`
2. `docs/architecture.md`
3. `docs/development-architecture.md`
4. `docs/python-conventions.md` (for Python code changes)
5. `docs/testing.md`
6. `docs/test-standards.md`
7. `docs/runbook.md`
8. `docs/system-context/index.md` (when task touches product/platform behavior)
9. relevant source files/tests
10. `docs/ai-memory.md` (durable decisions/gotchas)

## Non-Negotiable Workflow

1. Gather context from docs and code first.
2. Cite evidence (`path:line`) before non-trivial patches.
3. Make the smallest safe change.
4. Run validation commands from `docs/runbook.md`.
5. Update docs/memory when behavior or durable decisions change.

## Code Placement Guardrails

- Do not dump random helper functions into service/orchestration files.
- If logic is only used by one class, keep it as a private class method.
- If logic is shared, move it to a dedicated helper/module with a clear name.
- Keep adapters thin and focused on mapping/transport.
- Keep orchestration separate from policy/validation/mapping logic.
- Keep folder-first organization as domains grow.

## Testing Guardrails

- Follow `docs/testing.md` for test placement.
- Follow `docs/test-standards.md` for strategy and test quality.
- Keep `test_*.py` files test-only; shared helpers go in `tests/support/` or `conftest.py`.
- Keep default deterministic behavior intact (live/write suites are explicitly gated).

## PR and Conflict Workflow

- Follow PR workflow and auto-merge policy in `docs/conventions.md` and `docs/runbook.md`.
- Always check mergeability before enabling auto-merge.
- If conflicts exist, ask the requester how to resolve each file before editing conflict blocks.

## Change Boundaries

- Do not modify unrelated files.
- Do not silently change public contracts.
- State assumptions explicitly when required.
- If requirements conflict with docs, stop and ask.
