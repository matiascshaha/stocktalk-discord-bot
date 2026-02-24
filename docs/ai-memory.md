# AI Memory

Use this file as durable memory for high-value repo knowledge.

## Entry format

| Date | Area | Type | Fact/Decision | Evidence | Owner | Review date |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | ui-tests | fact | Replace me | path:line | handle | YYYY-MM-DD |
| 2026-02-24 | trading | decision | Runtime stock sizing now uses additive buying power (`max(cash_power,0) + margin-side component`) and enforces a hard projected Margin Equity % floor via `trading.min_margin_equity_pct` (default 35). | src/trading/buying_power.py:44; src/webull_trader.py:236; config/settings.py:199 | codex | 2026-05-24 |
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
