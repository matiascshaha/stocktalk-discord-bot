# Development Architecture Decisions

## Purpose

Define architecture and code-organization decisions that are language-agnostic.
Use this when deciding where new behavior should live.

## Core Rules

- One module/file should have one clear responsibility.
- Keep orchestration separate from business rules.
- Keep transport/integration adapters separate from domain policy.
- Prefer explicit contracts between layers over implicit behavior.
- Organize by domain responsibility first, then by technical detail.

## Layer Boundaries

- Entrypoints: bootstrapping and wiring only.
- Orchestrators: flow control, delegation, and sequencing.
- Domain logic: decisions, rules, and calculations.
- Contracts/schemas: stable interfaces between modules.
- Adapters: mapping to/from external systems and SDKs.
- Utilities: generic cross-domain helpers only.

## Dependency Direction

- High-level flow should point inward toward contracts and domain logic.
- Adapters depend on contracts; contracts do not depend on adapters.
- Orchestrators call domain/services; domain logic should not depend on orchestrators.
- Avoid circular dependencies across domains.

## Placement Rules

- If logic belongs to one domain, place it in that domain package.
- If logic is reusable across domains, place it in a clearly named shared module.
- Do not place policy logic in convenience files just because they are already open.
- Split growing files early when navigation or ownership becomes unclear.

## Extension Strategy

- Add new providers/brokers behind existing ports/contracts.
- Extend by adding modules/packages, not by bloating core orchestrators.
- Keep behavior changes localized; avoid broad cross-cutting edits when possible.

## Decision Checklist

Before adding code, answer:

1. What responsibility does this code own?
2. Which layer should own it (orchestrator, domain, contract, adapter, utility)?
3. Is it local behavior (class-private) or shared behavior (new module)?
4. Does placement keep future extensions easy without rewrites?
5. Does this preserve clear dependency direction?
