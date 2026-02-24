# AI Memory

Use this file as durable memory for high-value repo knowledge.

## Entry format

| Date | Area | Type | Fact/Decision | Evidence | Owner | Review date |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | ui-tests | fact | Replace me | path:line | handle | YYYY-MM-DD |
| 2026-02-24 | architecture | decision | Webull stock payload/sizing logic now lives in `src/brokerages/webull/stock_payload_builder.py`; `WebullTrader` delegates stock payload construction to keep order sizing logic modular and avoid mutating `StockOrderRequest` input quantity. | src/brokerages/webull/stock_payload_builder.py:1; src/webull_trader.py:309 | codex | 2026-05-24 |
| 2026-02-24 | testing | decision | Unified test entrypoint is `./scripts/testing/run.sh`; production Webull write verification is manual-only via `night`/`night-probe` with explicit `YES_IM_LIVE` ack and cleanup cancel. | scripts/testing/run.sh:1; tests/brokers/webull/smoke/test_webull_live.py:125; docs/testing.md:1 | codex | 2026-05-24 |
| 2026-02-22 | testing | decision | Test tree is domain-first (`tests/parser`, `tests/channels`, `tests/brokers`, `tests/system`, `tests/unit`); strategy split lives lower (`contract`/`integration`/`smoke`) and marker taxonomy is orthogonal (`unit|contract|integration|e2e`, `smoke`, `live`, `write`, domain markers). | tests/README.md:1; docs/testing.md:9; pytest.ini:1 | codex | 2026-05-22 |
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
