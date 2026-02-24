# Manual Prod E2E Check

Use this when you need confidence that production flow works end-to-end.

## 1) Broker Read (Prod)

```bash
PYTHON_BIN=.venv/bin/python ./scripts/testing/run.sh webull read-production
```

Pass: `2 passed` (login + balance/instrument checks).

## 2) Safe Broker Write Probe (Prod)

```bash
PYTHON_BIN=.venv/bin/python ./scripts/testing/run.sh night YES_IM_LIVE
```

Pass: `1 passed` (tiny limit order path + cleanup cancel).

## 3) Full App Flow (Prod)

Start bot:

```bash
DISCORD_ALLOW_ALL_CHANNELS=0 DISCORD_ALLOW_SELF_MESSAGES=0 .venv/bin/python -m src.main
```

Post one frozen message in monitored channel:

```text
New position: Apple $AAPL - 3% weight @ $190 avg on shares
```

Pass (logs):
- `New message from ...`
- `AI analyzing message.`
- `Detected 1 signal(s).`
- `Executing BUY AAPL ...`
- no `Trade execution failed ...`
