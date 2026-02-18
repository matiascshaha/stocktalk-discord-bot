# Test Index

Use this map to find tests by behavior domain first, then by layer.

## Parser

- Unit: `tests/unit/parser/test_parser_schema.py`
- Contract: `tests/contract/parser/test_ai_parser_contract.py`
- Smoke (live provider): `tests/smoke/ai/test_ai_live_smoke.py`
- Smoke (live parser->trader flow): `tests/smoke/ai/test_ai_pipeline_live_smoke.py`
- Case catalog: `tests/support/cases/parser_messages.py`

Quick commands:

```bash
pytest tests/unit/parser tests/contract/parser
TEST_AI_LIVE=1 pytest tests/smoke/ai -m "smoke and live"
```

## Trading Execution

- Unit (planner/executor/policy/market-hours/quotes): `tests/unit/trading/`
- Contract (Webull adapter payloads): `tests/contract/brokerage/test_webull_contract.py`
- Integration (Discord->order execution wiring): `tests/integration/discord_flow/test_discord_flow.py`
- Smoke (Webull read/write): `tests/smoke/webull/test_webull_smoke.py`
- Case catalogs: `tests/support/cases/execution_modes.py`, `tests/support/cases/trading_policy.py`

Quick commands:

```bash
pytest tests/unit/trading tests/contract/brokerage/test_webull_contract.py
pytest tests/integration/discord_flow -m integration
TEST_WEBULL_READ=1 pytest tests/smoke/webull/test_webull_smoke.py -m "smoke and live and not webull_write"
```

## Discord Flow

- Integration (deterministic message handling): `tests/integration/discord_flow/test_discord_flow.py`
- Smoke (live Discord connectivity): `tests/smoke/discord/test_discord_live_smoke.py`
- Shared factories: `tests/support/factories/discord_messages.py`

Quick commands:

```bash
pytest tests/integration/discord_flow -m integration
TEST_DISCORD_LIVE=1 pytest tests/smoke/discord/test_discord_live_smoke.py -m discord_live
```

## Providers & Config

- Unit providers: `tests/unit/providers/test_provider_dispatch.py`
- Unit config/path matrix: `tests/unit/config/test_paths.py`, `tests/unit/config/test_matrix.py`

Quick commands:

```bash
pytest tests/unit/providers tests/unit/config
```

## Tooling & Health

- Tooling runner tests: `tests/tooling/scripts/`
- Purity guard: `scripts/check_test_file_purity.py`
- Health runner: `scripts/quality/run_health_checks.py`

Quick commands:

```bash
python -m scripts.check_test_file_purity
pytest tests/tooling
python -m scripts.quality.run_health_checks
pytest -m feature_regression
```
