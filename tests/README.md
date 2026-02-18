# Test Strategy & Confidence

## Mission Statement

Deliver deterministic confidence for parser behavior, Discord flow, and Webull integration with explicit pass/fail health signals.

## Reliability Contract

- `Green`: deterministic suite passes and smoke checks pass.
- `Yellow`: deterministic suite passes, but external smoke checks are partial/failing.
- `Red`: deterministic checks fail.

## How We Measure Validity

1. Deterministic checks (`unit` + `contract` + `integration` + tooling) must pass.
2. Feature regression subset (`-m feature_regression`) must pass.
3. Smoke checks verify external integrations and report drift/non-determinism.

If deterministic checks fail, confidence is low regardless of smoke status.

## Directory Layout

- `tests/unit`: deterministic logic checks (organized by domain subfolders).
- `tests/contract`: parser/broker contract checks (organized by domain subfolders).
- `tests/integration`: deterministic cross-component behavior (organized by domain subfolders).
- `tests/smoke`: live/read-only environment checks plus opt-in write-path smoke tests.
- `tests/tooling`: deterministic tests for quality runners and helper scripts.
- `tests/support`: shared fixtures, fakes, factories, payloads, and case catalogs.

Use `tests/TEST_INDEX.md` to find tests by behavior domain quickly.

## Test File Purity Policy

- Test modules must contain tests only.
- Shared setup/helpers/fakes belong in `tests/support/` or `conftest.py`.
- CI enforces this via `python -m scripts.check_test_file_purity`.

## Test Matrix

| Layer | Purpose | Command | External deps | Blocking? |
|---|---|---|---|---|
| Paths/Config contracts | Verify path resolution + config loading contract | `pytest tests/unit/config/test_paths.py` | None | Yes |
| Parser deterministic contracts | Validate parser output normalization and shape | `pytest tests/contract/parser/test_ai_parser_contract.py tests/unit/parser/test_parser_schema.py` | None | Yes |
| Tooling runner tests | Validate confidence/matrix/flag runner behavior | `pytest tests/tooling` | None | Yes |
| Discord mocked integration | Verify filtering + notifier/trader behavior deterministically | `pytest tests/integration/discord_flow -m integration` | None | Yes |
| Feature regression subset | Verify high-confidence end-to-end deterministic scenarios | `pytest -m feature_regression` | None | Yes |
| Webull SDK contracts | Verify adapter compatibility + payload builders | `pytest tests/contract/brokerage/test_webull_contract.py` | None | Yes |
| AI live smoke | Validate real provider behavior for enabled provider matrix | `TEST_AI_LIVE=1 pytest tests/smoke/ai/test_ai_live_smoke.py -m "smoke and live"` | AI key + network | No |
| AI->Trader live pipeline | Validate live AI parse + trader wiring | `TEST_AI_LIVE=1 TEST_AI_SCOPE=sample pytest tests/smoke/ai/test_ai_pipeline_live_smoke.py -m "smoke and live"` | AI key + network | No |
| Webull read smoke | Validate login/account/balance/instrument with real endpoint | `TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production pytest tests/smoke/webull/test_webull_smoke.py -m "smoke and live and not webull_write"` | Webull credentials + network | No (initially) |
| Discord live smoke | Validate real Discord connectivity and channel access | `TEST_DISCORD_LIVE=1 pytest tests/smoke/discord/test_discord_live_smoke.py -m "discord_live"` | Discord token + network | No |
| Webull write smoke | Opt-in stock/options write-path checks | `TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=paper pytest tests/smoke/webull/test_webull_smoke.py -m "webull_write"` | Webull trading endpoint + network + market hours | No (opt-in only) |

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
pytest -m feature_regression
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

- markers: `unit`, `contract`, `integration`, `feature_regression`, `smoke`, `live`, `webull_write`, `discord_live`
- default run excludes: `live`, `webull_write`, `discord_live`

## Safety Defaults

- Default `pytest` run excludes live and write-path markers.
- No write-path trading smoke tests run unless explicitly enabled (`TEST_WEBULL_WRITE=1`).
