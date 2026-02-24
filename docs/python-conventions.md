# Python Conventions

## Purpose

Define Python-specific coding rules for this repository.
Primary goal: clean structure, readable code, and predictable placement.

## Module Structure

- One module = one purpose.
- Avoid large mixed-responsibility modules.
- Keep imports, constants, contracts/models, and implementation clearly separated.

## Service and Orchestrator Files

- Service/orchestrator modules should not collect random top-level helper functions.
- If helper logic is only used by one class, keep it as a private method on that class.
- If helper logic is shared across classes/modules, move it to a dedicated helper module.
- Keep service classes focused on orchestration/delegation, not raw utility accumulation.

## Functions and Methods

- Keep functions/methods short and single-purpose.
- Prefer guard clauses over deep nesting.
- Use explicit names; avoid vague names like `process_data` or `helper`.
- Keep side effects obvious at call sites.

## Types and Contracts

- Add type hints on public functions/methods.
- Prefer explicit models/contracts (for example Pydantic models) at boundaries.
- Validate incoming boundary data before executing business logic.

## Error Handling

- Fail clearly with actionable messages.
- Do not swallow exceptions silently.
- Raise domain-meaningful errors at boundaries; log context once.

## State and Dependencies

- Avoid hidden global state.
- Inject dependencies where practical instead of hardcoding behavior.
- Keep external API/SDK calls behind adapter modules.

## Organization Patterns

- Promote shared test helpers to `tests/support/`, not test modules.
- Promote shared runtime helpers to clearly named modules under the owning domain.
- Prefer new files/folders over bloated existing files when ownership is clearer.
