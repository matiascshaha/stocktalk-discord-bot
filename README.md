# Discord Stock Monitor

Monitors one Discord channel, extracts trade signals with AI, notifies/logs signals, and can optionally place stock orders through the configured broker.

## Mission

Make Discord trade alerts operational with a clear, testable flow:
Discord message -> structured signal -> optional trade execution.

## What The App Does

1. Watches a configured Discord channel.
2. Sends each relevant message to your configured AI provider (OpenAI runs fast-stage first, then falls back to a stronger model when needed).
3. Normalizes AI output into a strict parser contract.
4. Sends notifications and appends logs.
5. Optionally places stock orders when `trading.auto_trade=true` (Webull execution path implemented).

## System Design (Runtime Architecture)

```mermaid
flowchart LR
    subgraph Boot["Boot + Runtime Wiring"]
        START["python -m src.main"] --> CFG["Config validation + mode selection"]
        CFG --> MODE{"auto_trade enabled?"}
        MODE -- "no" --> MON["Monitor-only runtime"]
        MODE -- "yes" --> RUNTIME["Broker runtime via factory"]
    end

    subgraph Pipeline["Message -> Signal Pipeline"]
        DISCORD["Discord message"] --> GUARDS["Channel/self/content guards"]
        GUARDS --> PARSER["Parser orchestrator"]
        PARSER --> CONTRACT["ParsedMessage contract"]
        CONTRACT --> OBS["Notify + log"]
    end

    subgraph Execution["Execution Pipeline (when eligible)"]
        CONTRACT --> GATE{"Executable STOCK vehicle?"}
        GATE -- "no" --> SKIP["No trade"]
        GATE -- "yes" --> ORDER["Build StockOrder"]
        ORDER --> POLICY["Execution policy + pricing planner"]
        POLICY --> PORT["TradingBrokerPort"]
        PORT --> ADAPTER["Broker adapter"]
        ADAPTER --> BROKER_API["External broker API"]
    end

    MON -.-> Pipeline
    RUNTIME -. broker context .-> Pipeline
    PROVIDERS["AI provider adapters"] -. extend parser path .-> PARSER
    QUOTES["Quote provider adapters"] -. extend pricing path .-> POLICY
```

Architecture stability rule:

- This diagram is intentionally boundary-first (contracts + responsibilities).
- Provider/model-level details belong in component docs/tests, not in this graph.
- New integrations should plug into existing ports/adapters without changing core flow.

## Runtime Flow

1. `python -m src.main` starts the app and validates config.
2. If auto-trade is enabled, `create_broker_runtime(...)` resolves broker runtime (`webull`/`public`).
3. `StockMonitorClient` receives Discord messages.
4. Guard checks run (target channel, not self message, minimum content).
5. `AIParser.parse(...)` calls provider flow:
   - OpenAI: fast-stage parse first, then stronger fallback when confidence is low/ambiguous.
   - Other providers: routed through the same parser contract boundary.
6. AI output is normalized to `ParsedMessage`/`ParsedSignal` and validated by the parser contract.
7. Signals are notified/logged, then only executable STOCK vehicles are mapped into `StockOrder`.
8. `StockOrderExecutor` applies planner rules (market session + config) and routes to broker adapter.

## Core Components

| Component | Responsibility | File |
|---|---|---|
| Entrypoint | Bootstraps config, broker runtime, and client | `src/main.py` |
| Broker runtime factory | Selects broker and builds runtime (`webull`/`public`) | `src/brokerages/factory.py` |
| Discord client | Message handling, parser orchestration, and execution routing | `src/discord_client.py` |
| AI parser | Prompt rendering, provider dispatch, output normalization | `src/ai_parser.py` |
| Parser contract models | Canonical parser output (`ParsedMessage`, `ParsedSignal`, `ParsedVehicle`) | `src/models/parser_models.py` |
| Order planner | Chooses market vs limit behavior from session/config | `src/trading/orders/planner.py` |
| Order executor | Builds executable order and calls broker port | `src/trading/orders/executor.py` |
| Broker interface | Execution + market-data contract for adapters | `src/brokerages/ports.py` |
| Webull adapter | Maps broker-port calls to `WebullTrader` | `src/brokerages/webull/broker.py` |
| Webull SDK wrapper | Webull OpenAPI auth, quotes, and order placement | `src/webull_trader.py` |
| Config loader | Env + YAML/JSON config resolution | `config/settings.py` |

## Parser -> Trader Contract

`StockMonitorClient` maps parser output to stock execution using these fields:

| Parser field | Used for |
|---|---|
| `ticker` | Target symbol |
| `vehicles[].type` | Only `STOCK` vehicles are execution candidates |
| `vehicles[].enabled` | Must be `true` to execute |
| `vehicles[].intent` | Must be `EXECUTE` to execute |
| `vehicles[].side` | `BUY`/`SELL` mapped to `StockOrder.side`; `NONE` skipped |
| `weight_percent` | Optional sizing hint to trader |
| `meta.*` | Observability and debug context |

Execution note:

- `action` is part of parser semantics but runtime stock execution gates on `vehicles[*]` plus `ticker`.
- Other AI fields may exist but do not currently change stock order routing.

## AI Prompt Templates (Rules + Variables)

Prompt template sources:

- Fast stage (OpenAI): `config/ai_parser_fast.prompt`
- Full parse stage: `config/ai_parser.prompt`

Runtime variables currently injected by `AIParser`:

- Always: `CURRENT_TIME`, `AUTHOR_NAME`, `MESSAGE_TEXT`, `ANALYST_NAME`, `ANALYST_PREFERENCES`, `ACCOUNT_CONSTRAINTS`.
- When trader/account context exists: `ACCOUNT_BALANCE`, `MARGIN_POWER`, `CASH_POWER`, `MARGIN_EQUITY_PERCENTAGE`.
- Current gaps: placeholders like full live `OPTIONS_CHAIN` are not fully populated yet.

Core parsing behavior:

- Fast stage returns compact intent fields (`status`, `confidence`, `primary_ticker`, `vehicle_hint`, `action`, `evidence_text`, `sizing_text`).
- If fast-stage confidence is insufficient, parser runs full structured extraction.
- OpenAI full parse model output is `signals` only; parser injects `source` and `meta` locally.

Contract boundary note:

- `AIParser` normalizes provider output through `ParsedMessage`/`ParsedSignal`/`ParsedVehicle`.
- Trading path currently routes executable STOCK vehicles (`type/enabled/intent/side`) plus optional `weight_percent`.
- Extra AI keys outside model contract are ignored for execution.

## Current Behavior Limits

- `MIN_CONFIDENCE` is configured but not currently enforced as a hard pre-trade gate.
- Auto-trading path places stock orders; option-specific execution is not wired yet.
- Some advanced prompt placeholders (like live options chain) are not fully populated yet.

## Quick Start

- Python 3.11.x is required (3.11.14 pinned via `.python-version`).

```bash
python scripts/bootstrap/project_setup.py
source .venv/bin/activate
python -m src.main
```

## Docker

Prepare env file:

```bash
cp .env.example .env
```

Build image:

```bash
docker build -t stocktalk-bot .
```

Run with secrets injected at runtime (do not copy `.env` into image):

```bash
docker run --rm --env-file .env stocktalk-bot
```

Or with Compose:

```bash
docker compose up --build
```

## Configuration Files

- Secrets: `.env`
- Main app settings: `config/trading.yaml`
- AI fast prompt template: `config/ai_parser_fast.prompt`
- AI fallback/full prompt template: `config/ai_parser.prompt`

## Testing And Confidence

Detailed confidence policy and suite organization live in:

- `tests/README.md`

Main commands:

```bash
./scripts/testing/run.sh list
./scripts/testing/run.sh critical
./scripts/testing/run.sh deterministic
./scripts/testing/run.sh live-read
./scripts/testing/run.sh all
./scripts/testing/run.sh ai-live --ai-scope sample
```

## Extensibility

- AI provider strategy is pluggable through `AI_PROVIDER` and parser/provider init logic.
- Brokerage integration can be extended by adding trader adapters alongside `src/webull_trader.py`.

## Agent Workflow Files

The repository includes agent-focused assets to standardize planning, execution, and review:

- `AGENTS.md`: rules and guardrails for agent-driven changes.
- `docs/conventions.md`: repository development conventions.
- `docs/testing.md` and `docs/test-standards.md`: testing policy and expectations.
- `docs/manual-testing.md`: 10-minute manual happy-path verification.
- `docs/runbook.md`: operational runbook/checklist for task execution.
- `docs/ai-memory.md`: durable implementation notes and decisions.
- `docs/system-context/`: deeper system context for architecture, contracts, and operations.
- `prompts/`: reusable prompt templates for coding and automation work.
- `mcp/`: MCP setup references and example server configuration.
