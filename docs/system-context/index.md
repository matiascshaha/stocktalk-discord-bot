# System Context

Use this folder for deep application and platform context that agents need for implementation-quality decisions.

## When to use

- The task depends on business workflow details.
- The task crosses multiple services, queues, jobs, or environments.
- A bug requires system-level debugging or dependency tracing.

## Reading order

1. `docs/architecture.md` for high-level orientation.
2. `docs/system-context/architecture/topology.md` for cluster relationships and system boundaries.
3. `docs/system-context/architecture/system-map.md` for service boundaries and ownership.
4. `docs/system-context/architecture/dependency-matrix.md` for upstream/downstream contract impact.
5. `docs/system-context/contracts/api-catalog.md` for OpenAPI/contract discovery.
6. `docs/system-context/product/ui-journeys.md` for user flows and requirement mapping.
7. `docs/system-context/architecture/integration-flows.md` for end-to-end request/event paths.
8. `docs/system-context/operations/failure-modes.md` for known operational risks and diagnostics.
9. `docs/system-context/process/jira-process.md` for delivery workflow and project conventions.
10. `docs/system-context/architecture/domain-model.md` for business entities and invariants.
11. `docs/system-context/reference/glossary.md` for internal terms and acronyms.

## Task routing

| Task type | Read first | Then read |
|---|---|---|
| Feature delivery | `docs/system-context/product/ui-journeys.md` | `docs/system-context/contracts/api-catalog.md`, `docs/system-context/architecture/dependency-matrix.md` |
| Bug investigation | `docs/system-context/operations/failure-modes.md` | `docs/system-context/architecture/integration-flows.md`, `docs/system-context/architecture/topology.md` |
| API contract change | `docs/system-context/contracts/api-catalog.md` | `docs/system-context/architecture/dependency-matrix.md`, `docs/system-context/architecture/system-map.md` |
| Cross-team impact analysis | `docs/system-context/architecture/dependency-matrix.md` | `docs/system-context/architecture/topology.md`, `docs/system-context/architecture/domain-model.md` |
| Ticket/process questions | `docs/system-context/process/jira-process.md` | `docs/system-context/reference/source-registry.md` |

## Source ingestion workflow

1. Register source docs in `docs/system-context/reference/source-registry.md` (Confluence, Jira, OpenAPI repos, dashboards).
2. Distill stable, reusable facts into the focused files in this folder.
3. Record owner and review date in every updated file.
4. Link to source-of-truth pages instead of duplicating large content.
5. Add durable rules/decisions to `docs/ai-memory.md` when behavior expectations change.

## Documentation modeling standards

- Model architecture with C4-style levels where useful: landscape/context -> container/service -> component.
- Write docs by intent (Diataxis-style): how-to steps, reference tables, and explanatory context should be clearly separated.
- Keep architecture docs pragmatic and lean: include what materially affects design, operations, and delivery decisions.

## Context files

| File | Purpose | Owner | Last reviewed |
|---|---|---|---|
| `docs/system-context/architecture/topology.md` | System landscape, cluster boundaries, dependency direction | team-name | YYYY-MM-DD |
| `docs/system-context/architecture/system-map.md` | Services/modules, interfaces, owners, boundaries | team-name | YYYY-MM-DD |
| `docs/system-context/architecture/dependency-matrix.md` | Upstream/downstream dependencies, contracts, blast radius | team-name | YYYY-MM-DD |
| `docs/system-context/contracts/api-catalog.md` | API inventory and OpenAPI source links | team-name | YYYY-MM-DD |
| `docs/system-context/product/ui-journeys.md` | User journeys mapped to requirements and backend touchpoints | team-name | YYYY-MM-DD |
| `docs/system-context/architecture/integration-flows.md` | Cross-system data/control flow and invariants | team-name | YYYY-MM-DD |
| `docs/system-context/operations/failure-modes.md` | Common failures, signals, and recovery patterns | team-name | YYYY-MM-DD |
| `docs/system-context/process/jira-process.md` | Jira projects, issue lifecycle, required workflow conventions | team-name | YYYY-MM-DD |
| `docs/system-context/architecture/domain-model.md` | Core entities, relationships, and business rules | team-name | YYYY-MM-DD |
| `docs/system-context/reference/glossary.md` | Shared language, domain terms, and acronyms | team-name | YYYY-MM-DD |
| `docs/system-context/process/onboarding-playbook.md` | Fast-track learning path mirroring real team onboarding | team-name | YYYY-MM-DD |
| `docs/system-context/reference/source-registry.md` | Canonical source links and ingestion status | team-name | YYYY-MM-DD |

## Maintenance rules

- Keep this folder factual and operational, not speculative.
- Prefer short sections with links to source-of-truth systems/docs.
- Add dates and owners to major sections when updated.
