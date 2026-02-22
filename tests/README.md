# Test Strategy & Confidence

## Mission Statement

Deliver deterministic confidence for parser behavior, channel flow, and broker integration with explicit pass/fail health signals.

## Reliability Contract

- `Green`: deterministic suite passes and smoke checks pass.
- `Yellow`: deterministic suite passes, but external smoke checks are partial/failing.
- `Red`: deterministic checks fail.

## How We Measure Validity

1. Deterministic checks (`unit` + `contract` + `integration`) must pass.
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
| Paths/Config contracts | Verify path resolution + config loading contract | `pytest tests/unit/test_paths.py` | None | Yes |
| Parser deterministic contracts | Validate parser output shape and normalization | `pytest tests/parser/contract/test_parser_contract.py tests/unit/test_parser_schema.py` | None | Yes |
| System/tooling integration | Validate matrix/confidence/flags script behavior | `pytest tests/system/integration` | None | Yes |
| Discord mocked flow | Verify filtering + notifier/trader behavior deterministically | `pytest tests/channels/discord/integration/test_message_flow.py -k "not live_ai_pipeline_message_to_trader"` | None | Yes |
| Message-to-trader deterministic pipeline | Verify real message fixtures through parser shape into trader order calls | `pytest tests/channels/discord/integration/test_message_flow.py -k "real_message_pipeline_fake_ai_to_trader"` | None | Yes |
| Webull SDK contracts | Verify adapter compatibility + payload builders | `pytest tests/brokers/webull/contract/test_webull_contract.py` | None | Yes |
| AI live smoke | Validate real provider behavior for enabled provider matrix | `TEST_AI_LIVE=1 pytest tests/parser/smoke/test_ai_live.py -m "smoke and live"` | AI key + network | No |
| AI->Trader live pipeline | Validate live AI parsing and trader routing path | `TEST_AI_LIVE=1 TEST_AI_SCOPE=sample pytest tests/channels/discord/integration/test_message_flow.py -k "live_ai_pipeline_message_to_trader" -m "smoke and live"` | AI key + network | No |
| Webull read smoke | Validate login/account/balance/instrument with real endpoint | `TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production pytest tests/brokers/webull/smoke/test_webull_live.py -m "smoke and live and not write"` | Webull credentials + network | No (initially) |
| Discord live smoke | Validate real Discord connectivity and channel access | `TEST_DISCORD_LIVE=1 pytest tests/channels/discord/smoke/test_discord_live.py -m "smoke and live and channel and source_discord"` | Discord token + network | No |
| Webull write smoke | Opt-in stock/options write-path checks | `TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=paper pytest tests/brokers/webull/smoke/test_webull_live.py -m "smoke and live and write"` | Webull trading endpoint + network + market hours | No (opt-in only) |

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
python -m scripts.check_test_file_purity
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

## Safety Defaults

- Default `pytest` run excludes `live` and `write` markers.
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
