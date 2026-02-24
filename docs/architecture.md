# System Architecture (High-Level)

## Purpose

This file gives agents a fast end-to-end mental model of how the runtime works.
For deep details, use `docs/system-context/`.

## E2E Runtime Flow

1. `python -m src.main` starts app boot and runs `validate_config()` (`src/main.py`).
2. If `trading.auto_trade=true`, `create_broker_runtime(...)` selects broker runtime (`webull` or `public`) (`src/brokerages/factory.py`).
3. `StockMonitorClient` connects to Discord and filters messages by channel/self/length (`src/discord_client.py`).
4. `AIParser.parse(...)` sends prompt to selected provider (`openai`/`anthropic`/`google`) and normalizes output to parser contract (`src/ai_parser.py`).
5. Parsed payload is validated as `ParsedMessage` (`src/models/parser_models.py`).
6. Signals are notified and logged to `data/picks_log.jsonl` (`src/notifier.py`, `src/discord_client.py`).
7. If broker runtime exists, executable STOCK vehicles are converted into `StockOrder` and passed to `StockOrderExecutor` (`src/trading/orders/executor.py`).
8. Executor applies planner policy (market/limit, TIF, out-of-hours behavior) and calls broker adapter via `TradingBrokerPort` (`src/trading/orders/planner.py`, `src/brokerages/ports.py`).
9. Webull path routes through `WebullBroker` -> `WebullTrader` -> Webull OpenAPI (`src/brokerages/webull/broker.py`, `src/webull_trader.py`).

## Component Map

| Layer | Responsibility | Key files |
|---|---|---|
| Boot | Validate config, choose monitor-only vs auto-trade | `src/main.py`, `config/settings.py` |
| Ingestion | Discord events and message guards | `src/discord_client.py` |
| Parsing | Provider dispatch + contract normalization | `src/ai_parser.py`, `src/providers/*`, `src/models/parser_models.py` |
| Observability | Notifications + JSONL logging | `src/notifier.py`, `src/utils/logger.py` |
| Execution Policy | Build executable stock orders and choose order strategy | `src/trading/orders/planner.py`, `src/trading/orders/executor.py` |
| Broker Boundary | Stable execution/market-data port | `src/brokerages/ports.py` |
| Broker Adapters | Webull implementation, Public scaffold | `src/brokerages/webull/broker.py`, `src/brokerages/public/broker.py` |
| External API | Webull auth, account, quote, order placement | `src/webull_trader.py` |

## Core Contracts and Boundaries

- Parser contract: `ParsedMessage` -> `source`, `signals[]`, `meta` (`src/models/parser_models.py`).
- Execution gate is vehicle-based, not action-only:
  - `vehicles[].type == STOCK`
  - `vehicles[].enabled == true`
  - `vehicles[].intent == EXECUTE`
  - `vehicles[].side in {BUY, SELL}`
- Broker execution depends on `TradingBrokerPort` methods:
  - `place_stock_order(order, weighting)`
  - `get_limit_reference_price(symbol, side)`

## Runtime Modes

- Monitor-only:
  - `trading.auto_trade=false`, no broker runtime.
  - Messages are parsed, notified, and logged only.
- Auto-trade with Webull:
  - `trading.auto_trade=true` and `trading.broker=webull`.
  - Runtime builds `WebullBroker` after successful Webull login.
- Auto-trade with Public:
  - `trading.broker=public` initializes scaffold adapter.
  - Stock execution methods are not implemented yet.

## Failure Model (Important)

- Config validation failure: app exits at boot (`src/main.py`).
- Broker runtime creation error: app exits.
- Webull login failure: factory returns `None` runtime and app continues monitor-only.
- Parser provider or JSON failure: parser returns contract-safe empty/no-action result.
- Order execution failure for one signal: logged and processing continues for later signals.

## Current Scope Limits

- Execution path is stock-focused; option execution is not wired in runtime.
- `trading.min_confidence` exists in config but is not currently enforced as a hard pre-trade gate.
- Default `public` broker adapter is a placeholder (`NotImplementedError`).

## Where To Look Next

- Deeper architecture and dependency views: `docs/system-context/architecture/`
- Contracts and operations: `docs/system-context/contracts/`, `docs/system-context/operations/`
- Test matrix and confidence model: `tests/README.md`
- Operator commands: `docs/runbook.md`
