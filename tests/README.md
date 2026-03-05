# Test Strategy & Confidence

## Mission Statement

Deliver deterministic confidence for parser behavior, channel flow, and broker integration with explicit pass/fail health signals.

## Reliability Contract

- `PR required`: `./scripts/testing/run.sh critical` must pass.
- `Nightly signal`: `./scripts/testing/run.sh live-read` validates external read-only integrations.
- `Manual cost-controlled`: `./scripts/testing/run.sh ai-live` is manual only.

## How We Measure Validity

1. Critical deterministic checks (`unit` + `contract` + key `integration`) must pass on PR.
2. Live smoke is split from PR gating and run read-only by schedule/manual mode.
3. Runner report summarizes pass/fail/skip with rerun commands and artifact paths.

If critical deterministic checks fail, confidence is low regardless of live smoke status.

## Parser-to-Trader Contract

Canonical parser output contract lives in:

- `src/models/parser_models.py`

Trading adapter consumes this contract in:

- `src/discord_client.py`

Required structure:

- top-level: `{"contract_version": "...", "source": {...}, "signals": [...], "meta": {...}}`
- signal fields: `ticker`, `action`, `confidence`, `weight_percent`, `urgency`, `sentiment`, `reasoning`, `is_actionable`, `vehicles`
- vehicle fields: `type`, `enabled`, `intent`, `side` (+ option fields when `type=OPTION`)

Behavior mapping:

- `action=BUY` -> place BUY stock order
- `action=SELL` -> place SELL stock order
- `action=HOLD` -> no order placement

Provider-path note:

- OpenAI parser runtime is fast-stage first with fallback full parse.
- Webull/Discord integration tests in this tree mock `AIParser.parse(...)` normalized output (post-parser contract), not raw provider response payloads.

## Directory Layout

Top-level folders are domain-first:

- `tests/unit`: deterministic unit tests (kept as-is for core logic coverage).
- `tests/parser`: parser-specific contracts and parser live smoke checks.
- `tests/channels`: message-source tests (Discord now, extensible for other sources).
- `tests/brokers`: brokerage tests (Webull now, extensible for other broker adapters).
- `tests/system`: cross-domain system/tooling behavior tests.
- `tests/support`: shared fixtures, fakes, factories, payload builders, and reusable test helpers.

Strategy split is inside each domain where needed:

- `contract`
- `integration`
- `smoke`

## Marker Contract (Standardized)

Markers are orthogonal axes:

- Layer: `unit`, `contract`, `integration`, `e2e`
- Intent: `smoke`
- Runtime/risk: `live`, `write`
- Domain: `parser`, `channel`, `broker`, `system`
- Specificity: `source_discord`, `broker_webull`

Rules:

- Every test must carry one layer marker.
- `write` tests are also `live` tests.
- Legacy markers are removed (`webull_write`, `discord_live`).

Default run behavior (`pytest.ini`):

- `pytest` excludes `live` and `write` tests by default.

## Test Matrix

| Layer | Purpose | Command | External deps | Blocking? |
|---|---|---|---|---|
| PR critical gate | Highest-risk deterministic Discord -> parser -> Webull execution confidence | `./scripts/testing/run.sh critical` | None | Yes |
| Full deterministic | Full deterministic suite (`not smoke/live/write`) | `./scripts/testing/run.sh deterministic` | None | Optional |
| Live read smoke | Discord live + Webull paper read-only smoke | `./scripts/testing/run.sh live-read` | Discord/Webull credentials + network | Nightly/manual |
| All non-write coverage | Deterministic + live-read in one command | `./scripts/testing/run.sh all` | Mixed | Manual |
| AI live (cost-controlled) | Live provider smoke + AI pipeline live test | `./scripts/testing/run.sh ai-live --ai-scope sample` | AI key + network | Manual only |
| Production write probe | Explicitly acknowledged production write check | `./scripts/testing/run.sh night-probe --ack YES_IM_LIVE` | Production Webull credentials + network | Manual only |

## Runner Artifacts

`./scripts/testing/run.sh <profile>` writes:

- `artifacts/ci_report.json`: machine-readable run summary.
- `artifacts/junit-*.xml`: per-suite JUnit output for CI integrations.
- `artifacts/logs/*.log`: full stdout/stderr per suite.

## Safety Defaults

- Default `pytest` run excludes `live` and `write` markers.
- No write-path trading tests run unless `night-probe` is explicitly invoked with `--ack YES_IM_LIVE`.

## Environment Flags

- `TEST_AI_LIVE`
- `TEST_AI_SCOPE` (`sample`, `full`)
- `TEST_DISCORD_LIVE`
- `TEST_WEBULL_READ`
- `TEST_WEBULL_WRITE`
- `TEST_WEBULL_ENV` (`paper`, `production`)
- `TEST_BROKERS` (default: `webull`)
