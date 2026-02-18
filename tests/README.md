# Test Strategy & Confidence

## Mission

Deliver deterministic confidence through class-mirrored unit tests and feature-owned behavior/contract suites, with live smoke checks isolated by feature.

## Reliability Contract

- `Green`: deterministic checks pass and enabled smoke checks pass.
- `Yellow`: deterministic checks pass but external smoke has failures.
- `Red`: deterministic checks fail.

## Directory Layout

- `tests/unit`: deterministic unit tests in a flat class/module layout.
- `tests/features/<feature>/happy_path`: expected successful behavior scenarios.
- `tests/features/<feature>/edge_cases`: guardrail/failure behavior scenarios.
- `tests/features/<feature>/contracts`: strict schema/interface/payload contracts.
- `tests/features/<feature>/smoke`: live/external smoke checks for the feature.
- `tests/tooling`: deterministic tests for quality runners and helper scripts.
- `tests/testkit`: shared builders, doubles, payloads, scenario catalogs, helpers, and datasets.

Use `tests/TEST_INDEX.md` to find tests by feature quickly.

## Test File Purity

- Test modules contain tests only.
- Shared setup/helpers/fakes belong in `tests/testkit/` or `conftest.py`.
- CI enforces this via `python -m scripts.check_test_file_purity`.

## Marker Contract

Configured in `pytest.ini`:

- `unit`
- `feature`
- `happy_path`
- `edge_case`
- `contract`
- `feature_regression`
- `tooling`
- `smoke`
- `live`
- `webull_write`
- `discord_live`

Default `pytest` excludes live markers (`live`, `webull_write`, `discord_live`).

## Core Commands

```bash
python -m scripts.check_test_file_purity
pytest tests/unit tests/features tests/tooling
pytest -m feature_regression
python -m scripts.quality.run_health_checks
python -m scripts.quality.run_full_matrix
```

## Live Smoke Examples

```bash
TEST_AI_LIVE=1 pytest tests/features/signal_generation/smoke/test_ai_live_smoke.py -m "smoke and live"
TEST_AI_LIVE=1 TEST_AI_SCOPE=sample pytest tests/features/trade_execution/smoke/test_ai_pipeline_live_smoke.py -m "smoke and live"
TEST_DISCORD_LIVE=1 pytest tests/features/message_intake/smoke/test_discord_live_smoke.py -m "discord_live"
TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production pytest tests/features/broker_webull_adapter/smoke/test_webull_read_smoke.py -m "smoke and live and not webull_write"
TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=paper pytest tests/features/broker_webull_adapter/smoke/test_webull_write_smoke.py -m "webull_write"
```
