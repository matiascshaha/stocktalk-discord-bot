# Testing Commands

Simple command surface for daily testing.

## Preferred Runner

```bash
./scripts/testing/run.sh
./scripts/testing/run.sh list
```

### Fast local confidence

```bash
./scripts/testing/run.sh quick
```

### Live read-only checks (no production writes)

```bash
./scripts/testing/run.sh live
```

## Domain Commands

### Webull

Contract checks:

```bash
./scripts/testing/run.sh webull contract
```

Live read smoke (paper):

```bash
./scripts/testing/run.sh webull read-paper
```

Live read smoke (production):

```bash
./scripts/testing/run.sh webull read-production
```

Live write smoke (paper only):

```bash
./scripts/testing/run.sh webull write-paper
```

Production night write probe (manual + cleanup):

```bash
./scripts/testing/run.sh webull night-probe YES_IM_LIVE
```

Shortcut:

```bash
./scripts/testing/run.sh night YES_IM_LIVE
```

### Discord

Deterministic flow:

```bash
./scripts/testing/run.sh discord deterministic
```

Live smoke:

```bash
./scripts/testing/run.sh discord live
```

### AI Parser

Deterministic contract checks:

```bash
./scripts/testing/run.sh ai deterministic
```

Live smoke:

```bash
./scripts/testing/run.sh ai live
```

## Safety Rules

- `pytest` defaults to `-m "not live and not write"` (`pytest.ini`).
- Production write checks are manual only.
- Night probe requires explicit ack: `YES_IM_LIVE`.
- Night probe sends a tiny non-fillable limit order and immediately cancels it.

## Raw Pytest Equivalents

If you do not want the runner, use these directly:

```bash
python -m scripts.check_test_file_purity
python -m pytest tests -m "not smoke and not live and not write"
TEST_WEBULL_READ=1 TEST_WEBULL_ENV=production pytest tests/brokers/webull/smoke/test_webull_live.py -m "smoke and live and not write"
TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=paper pytest tests/brokers/webull/smoke/test_webull_live.py -m "smoke and live and write"
TEST_WEBULL_WRITE=1 TEST_WEBULL_ENV=production TEST_WEBULL_NIGHT_PROBE=1 TEST_WEBULL_PROD_ACK=YES_IM_LIVE pytest tests/brokers/webull/smoke/test_webull_live.py -k "night_probe_production_manual_cleanup" -m "smoke and live and write"
TEST_DISCORD_LIVE=1 pytest tests/channels/discord/smoke/test_discord_live.py -m "smoke and live and channel and source_discord"
TEST_AI_LIVE=1 pytest tests/parser/smoke/test_ai_live.py -m "smoke and live"
```
