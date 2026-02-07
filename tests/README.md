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

## Test Matrix

| Layer | Purpose | Command | External deps | Blocking? |
|---|---|---|---|---|
| Paths/Config contracts | Verify path resolution + config loading contract | `pytest tests/test_paths.py` | None | Yes |
| Parser deterministic contracts | Validate parser output shape and normalization | `pytest tests/test_gpt_integration.py -m "not live"` | None | Yes |
| Parser schema contract | Guarantee downstream-required fields for Discord/trading | `pytest tests/test_parser_schema.py` | None | Yes |
| Discord mocked flow | Verify filtering + notifier/trader behavior deterministically | `pytest tests/test_discord_integration.py` | None | Yes |
| Webull SDK contracts | Verify adapter compatibility + payload builders | `pytest tests/test_webull_contract.py` | None | Yes |
| Webull read smoke | Validate login/account/balance/instrument with real endpoint | `RUN_WEBULL_READ_SMOKE=1 pytest tests/test_webull_smoke.py -m "smoke and live and not webull_write"` | Webull credentials + network | No (initially) |
| Discord live smoke | Validate real Discord connectivity and channel access | `RUN_DISCORD_LIVE_SMOKE=1 pytest tests/test_discord_live_smoke.py -m "discord_live"` | Discord token + network | No |
| Webull write smoke | Opt-in stock/options write-path checks | `RUN_WEBULL_WRITE_TESTS=1 pytest tests/test_webull_smoke.py -m "webull_write"` | Webull trading endpoint + network | No (opt-in only) |

## Health Checks

Canonical commands:

```bash
pytest
pytest -m smoke
python -m scripts.healthcheck
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
- `RUN_DISCORD_LIVE_SMOKE`
- `RUN_WEBULL_READ_SMOKE`
- `RUN_WEBULL_WRITE_TESTS`
- `WEBULL_PAPER_REQUIRED`
