# Manual Testing (Super Simple Happy Path)

This is the fastest way to verify the app works end-to-end:

Discord message -> AI parse -> local log entry -> Webull paper order attempt visible.

## 1) Quick setup

1. Use your virtual env and install deps.
```bash
source .venv/bin/activate
pip install -r requirements.txt
```
2. Set required secrets in `.env`:
- `DISCORD_TOKEN`
- `OPENAI_API_KEY` (or your chosen provider key)
- `WEBULL_APP_KEY`
- `WEBULL_APP_SECRET`
3. In `config/trading.yaml`, set:
- `discord.channel_id`: a test channel you can post in
- `trading.auto_trade: true`
- `trading.paper_trade: true`

## 2) Run one happy-path test

1. Start the app:
```bash
python src/main.py
```
2. In the configured Discord channel, send:
```text
Buy AAPL now
```

## 3) Verify success

1. In terminal logs, confirm:
- message was detected
- signal was parsed
- trade placement was attempted
2. In local data, confirm a new line was appended:
```bash
tail -n 1 data/picks_log.jsonl
```
3. In Webull paper/UAT Orders/Activity, confirm an AAPL order event appears.
- Accepted or rejected both count as pipeline success.
- Rejections like buying-power or market-hours still prove end-to-end flow is working.

## 4) Fast troubleshooting

- Nothing happens after message: check `discord.channel_id` matches your test channel.
- No trade attempt: check `trading.auto_trade: true`.
- Safety check: keep `trading.paper_trade: true` for manual testing.

## 5) Done checklist

- [ ] App starts with no config validation errors
- [ ] Message in test channel is detected
- [ ] Parser returns an actionable signal
- [ ] `data/picks_log.jsonl` gets a new entry
- [ ] Webull paper/UAT shows an AAPL order attempt
