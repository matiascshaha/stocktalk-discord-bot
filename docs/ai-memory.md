# AI Memory

Use this file as durable memory for high-value repo knowledge.

## Entry format

| Date | Area | Type | Fact/Decision | Evidence | Owner | Review date |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | ui-tests | fact | Replace me | path:line | handle | YYYY-MM-DD |
| 2026-02-18 | testing | decision | Test architecture is feature-first (`tests/features/<feature>/{happy_path,edge_cases,contracts,smoke}`) with class/module unit suites mirrored under `tests/unit/src/`, and shared assets under `tests/testkit/`. | AGENTS.md:64; docs/testing.md:9; tests/README.md:13; tests/TEST_INDEX.md:17 | codex | 2026-05-18 |
| 2026-02-16 | testing | decision | Test modules must contain tests only; shared setup/fakes/helpers go in `conftest.py` or `tests/testkit/`; runner/tooling tests live in `tests/tooling`, enforced by `scripts.check_test_file_purity`. | AGENTS.md:66; docs/testing.md:16; .github/workflows/reliability.yml:27 | codex | 2026-05-16 |
| 2026-02-16 | architecture | decision | Provider integrations should live under `src/providers/<provider>/` with separate contract and client modules; parser orchestrators should call provider entry points instead of embedding provider protocol details. | AGENTS.md:50; docs/conventions.md:28 | codex | 2026-05-16 |
| 2026-02-11 | docs | decision | Deep application/platform knowledge lives in `docs/system-context/` and is linked from `docs/architecture.md`; consult it early for behavior-heavy tasks. | AGENTS.md:22; docs/architecture.md:35; docs/system-context/index.md:1 | codex | 2026-05-11 |
| 2026-02-11 | docs | decision | System context is organized as task-routed files (topology, dependencies, APIs, UI journeys, Jira process, domain model, onboarding, source registry) to mirror real onboarding and speed retrieval. | docs/system-context/index.md:11; docs/system-context/reference/source-registry.md:1; docs/architecture.md:37 | codex | 2026-05-11 |

## Types

- `fact`: stable technical truth
- `decision`: selected approach with rationale
- `gotcha`: recurring failure pattern
- `command`: canonical command for setup/verify/release

## Rules

- Keep entries short and verifiable.
- Link to source files, PRs, or run logs.
- Remove or supersede stale entries.
