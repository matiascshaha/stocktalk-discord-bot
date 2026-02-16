# Test Strategy & Confidence

## Mission Statement

Deliver deterministic confidence for parser behavior, Discord flow, and Webull integration with explicit pass/fail health signals.

## Reliability Contract

- `Green`: deterministic suite passes and smoke checks pass.
- `Yellow`: deterministic suite passes, but external smoke checks are partial/failing.
- `Red`: deterministic checks fail.

## How We Measure Validity

Application validity is measured by expected behavior proving out in tests, not by code shape:

1. Deterministic checks (`unit` + `contract`) must pass.
2. Smoke checks verify external integrations and report drift/non-determinism.
3. Health report summarizes what is verified vs skipped.

If deterministic checks fail, confidence is low regardless of smoke status.

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

## Directory Layout

- `tests/unit`: pure deterministic logic and path/config behavior.
- `tests/contract`: schema/interface compatibility with parser and broker adapters.
- `tests/integration`: mocked component interaction flows (Discord + parser + trader wiring).
- `tests/smoke`: live/read-only environment checks, plus opt-in write-path smoke tests.
- `tests/support`: shared matrix and artifact helpers.

## Test Matrix

| Layer | Purpose | Command | External deps | Blocking? |
|---|---|---|---|---|
| Paths/Config contracts | Verify path resolution + config loading contract | `pytest tests/unit/test_paths.py` | None | Yes |
| Parser deterministic contracts | Validate parser output shape and normalization | `pytest tests/contract/test_ai_parser_contract.py tests/unit/test_parser_schema.py` | None | Yes |
| Discord mocked flow | Verify filtering + notifier/trader behavior deterministically | `pytest tests/integration/test_discord_flow.py` | None | Yes |
| Message-to-trader deterministic pipeline | Verify real message fixtures flow through parser shape into trader order calls | `pytest tests/integration/test_discord_flow.py -k "real_message_pipeline_fake_ai_to_trader"` | None | Yes |
| Webull SDK contracts | Verify adapter compatibility + payload builders | `pytest tests/contract/test_webull_contract.py` | None | Yes |
| AI live smoke | Validate real provider behavior for enabled provider matrix | `RUN_LIVE_AI_TESTS=1 pytest tests/smoke/test_ai_live_smoke.py -m "smoke and live"` | AI key + network | No |
| AI->Trader live pipeline | Validate live AI parses incoming message and drives trader path | `RUN_LIVE_AI_TESTS=1 pytest tests/integration/test_discord_flow.py -k "live_ai_pipeline_message_to_trader" -m "smoke and live"` | AI key + network | No |
| Webull read smoke | Validate login/account/balance/instrument with real endpoint | `RUN_WEBULL_READ_SMOKE=1 pytest tests/smoke/test_webull_smoke.py -m "smoke and live and not webull_write"` | Webull credentials + network | No (initially) |
| Discord live smoke | Validate real Discord connectivity and channel access | `RUN_DISCORD_LIVE_SMOKE=1 pytest tests/smoke/test_discord_live_smoke.py -m "discord_live"` | Discord token + network | No |
| Webull write smoke | Opt-in stock/options write-path checks | `RUN_WEBULL_WRITE_TESTS=1 pytest tests/smoke/test_webull_smoke.py -m "webull_write"` | Webull trading endpoint + network + market hours (production) | No (opt-in only) |

## Health Checks

Canonical commands:

```bash
python -m scripts.full_confidence
python -m scripts.full_confidence --webull-smoke-paper-trade
python -m scripts.full_confidence --include-webull-write
python -m scripts.full_confidence --mode deterministic
pytest
pytest -m smoke
python -m scripts.healthcheck
FULL_CONFIDENCE_REQUIRED=1 python -m scripts.healthcheck
```

`python -m scripts.healthcheck` writes `artifacts/health_report.json` with:

- `timestamp`
- `git_sha`
- `overall_status` (`green`, `yellow`, `red`)
- `checks[]`
- `failures[]`
- `skips[]`
- `external_dependencies`

Exit codes:

- `0` = green
- `1` = deterministic failure
- `2` = external-smoke-only failure (yellow)
- With `FULL_CONFIDENCE_REQUIRED=1`, skipped external checks also keep status non-green.

## Markers & Defaults

Configured in `pytest.ini`:

- markers: `unit`, `contract`, `smoke`, `live`, `webull_write`, `discord_live`
- default test run excludes: `live`, `webull_write`, `discord_live`

## Webull Reality Notes

- Stock order preview is implemented as a local estimate because the installed SDK does not provide a stock preview endpoint equivalent to options preview.
- Options endpoint behavior can vary by account, region, and Webull backend availability.
- Options structure is contract-tested locally; live options endpoint failures are treated as non-blocking smoke results for now.

## Safety Defaults

- Default `pytest` run excludes live and write-path markers.
- No write-path trading tests run unless explicitly enabled (`RUN_WEBULL_WRITE_TESTS=1`).
- When `WEBULL_PAPER_REQUIRED=1` (default), write-path tests require paper mode.

## Environment Flags

- `RUN_LIVE_AI_TESTS`
- `RUN_LIVE_AI_PIPELINE_FULL`
- `RUN_DISCORD_LIVE_SMOKE`
- `RUN_WEBULL_READ_SMOKE`
- `RUN_WEBULL_WRITE_TESTS`
- `WEBULL_PAPER_REQUIRED`
- `WEBULL_SMOKE_PAPER_TRADE`
- `TEST_AI_PROVIDERS` (default: `openai,anthropic,google`)
- `TEST_BROKERS` (default: `webull`)
- `FULL_CONFIDENCE_REQUIRED`

Runner defaults:

- `python -m scripts.full_confidence` delegates execution to `python -m scripts.healthcheck` after setting env flags for the selected profile.
- `python -m scripts.full_confidence` enables strict gates and live smoke checks.
- Default full run uses production Webull read smoke (`WEBULL_SMOKE_PAPER_TRADE=0`).
- `--include-webull-write` follows your `PAPER_TRADE` setting unless you force `--webull-smoke-paper-trade`.
