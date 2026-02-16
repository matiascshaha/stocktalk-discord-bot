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
| AI live smoke | Validate real provider behavior for enabled provider matrix | `TEST_AI_LIVE=1 pytest tests/smoke/test_ai_live_smoke.py -m "smoke and live"` | AI key + network | No |
| AI->Trader live pipeline | Validate live AI parses incoming message and drives trader path | `TEST_AI_LIVE=1 TEST_AI_SCOPE=sample pytest tests/integration/test_discord_flow.py -k "live_ai_pipeline_message_to_trader" -m "smoke and live"` | AI key + network | No |
| Webull read smoke | Validate login/account/balance/instrument with real endpoint | `TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production pytest tests/smoke/test_webull_smoke.py -m "smoke and live and not webull_write"` | Webull credentials + network | No (initially) |
| Discord live smoke | Validate real Discord connectivity and channel access | `TEST_DISCORD_LIVE=1 pytest tests/smoke/test_discord_live_smoke.py -m "discord_live"` | Discord token + network | No |
| Webull write smoke | Opt-in stock/options write-path checks | `TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=paper pytest tests/smoke/test_webull_smoke.py -m "webull_write"` | Webull trading endpoint + network + market hours | No (opt-in only) |

## Health Checks

Canonical commands:

```bash
python -m scripts.quality.run_full_matrix
python -m scripts.quality.run_full_matrix --skip-discord-live --skip-webull-prod-write --ai-scope sample
python -m scripts.quality.run_full_matrix --only webull_read_paper,webull_write_paper
python -m scripts.quality.run_confidence_suite
python -m scripts.quality.run_confidence_suite --webull-env paper
python -m scripts.quality.run_confidence_suite --webull-write 1
python -m scripts.quality.run_confidence_suite --mode local
pytest
pytest -m smoke
python -m scripts.quality.run_health_checks
TEST_MODE=strict python -m scripts.quality.run_health_checks
```

`python -m scripts.quality.run_health_checks` writes `artifacts/health_report.json` with:

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
- With `TEST_MODE=strict`, external check failures/skips are blocking.

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
- No write-path trading tests run unless explicitly enabled (`TEST_WEBULL_WRITE=1`).

## Environment Flags

- `TEST_MODE` (`local`, `smoke`, `strict`)
- `TEST_AI_LIVE`
- `TEST_AI_SCOPE` (`sample`, `full`)
- `TEST_DISCORD_LIVE`
- `TEST_WEBULL_READ`
- `TEST_WEBULL_WRITE`
- `TEST_WEBULL_ENV` (`paper`, `production`)
- `TEST_AI_PROVIDERS` (default: `openai,anthropic,google`)
- `TEST_BROKERS` (default: `webull`)

Runner defaults:

- `python -m scripts.quality.run_full_matrix` runs deterministic + AI live (full scope) + Webull paper/prod read/write + Discord live by default.
- Use `--skip-discord-live`, `--skip-webull-prod-write`, or `--ai-scope sample` for a faster subset.
- `python -m scripts.quality.run_confidence_suite` delegates execution to `python -m scripts.quality.run_health_checks` after setting env flags for the selected mode.
- `python -m scripts.quality.run_confidence_suite` defaults to `TEST_MODE=strict`.
- Default strict run uses production Webull target (`TEST_WEBULL_ENV=production`) with write smoke off.
- Enable write smoke explicitly with `--webull-write 1`.
