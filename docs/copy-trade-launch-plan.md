# Copy Trade Launch Plan

## Goal
- Prove 1 full E2E copy trade in paper.
- Then execute 1 micro live trade.

## Success Criteria
- Discord message is detected.
- AI returns an actionable stock signal.
- Webull order submit is acknowledged.
- `data/picks_log.jsonl` gets a new line.
- Kill switch is confirmed.

## Required Config  
- `trading.auto_trade: true`
- `trading.broker: webull`
- `trading.options_enabled: false`
- Phase 1: `trading.paper_trade: true`
- Phase 2: `trading.paper_trade: false`

## Frozen Message
- Use: `New position: Apple $AAPL - 3% weight @ $190 avg on shares`

## Deterministic E2E Preflight
1. Run: `pytest tests/brokers/webull/integration/test_paper_trade_discord_flow.py`
2. Confirm pass for:
   - common shares recommendation
   - options-only recommendation
   - mixed commons+options recommendation
   - no-action payload
   - weighted recommendation
   - default dollar-sizing path
3. Run account-context guards: `pytest tests/brokers/webull/integration/test_paper_trade_account_context.py`

## Phase 1 (Paper E2E)
1. Start app: `python -m src.main`
2. Post frozen message in the configured Discord channel.
3. Verify logs show parse + order submit attempt.
4. Verify `tail -n 1 data/picks_log.jsonl`.
5. Verify Webull paper order event.
6. Repeat until 3/3 successful runs.

## Phase 2 (Live Micro Trade)
1. Set `trading.paper_trade: false`.
2. Start app: `python -m src.main`
3. Post one frozen message.
4. Success = submit acknowledged (fill not required).
5. Immediately disable auto-trade after success.

## Kill Switch
1. Set `trading.auto_trade: false`.
2. Restart app.

## Out Of Scope
- Option fixed-notional sizing strategy.
- Multi-analyst support.
- New strategy features.
