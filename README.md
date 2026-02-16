# Discord Stock Monitor

Monitors one Discord channel, extracts trade signals with AI, notifies/logs picks, and can optionally place stock orders on Webull.

## Mission

Make Discord trade alerts operational with a clear, testable flow:
Discord message -> structured pick -> optional trade execution.

## What The App Does

1. Watches a configured Discord channel.
2. Sends each relevant message to your configured AI provider.
3. Normalizes AI output into a strict parser contract.
4. Sends notifications and appends logs.
5. Optionally places stock orders through Webull when `AUTO_TRADE=true`.

## System Design (Simplified)

```mermaid
flowchart LR
    D["Discord Channel"] --> C["StockMonitorClient"]
    F["config/ai_parser.prompt"] --> P["AIParser"]
    C --> P["AIParser"]
    P --> A["AI Provider API"]
    P --> M["ParsedMessage"]
    M --> C
    C --> N["Notifier"]
    C --> L1["data/picks_log.jsonl"]
    C -->|AUTO_TRADE=true| T["WebullTrader"]
    T --> W["Webull OpenAPI"]
    T --> L2["data/trades_log.jsonl"]
```

## Runtime Flow

1. `python -m src.main` starts the app and validates config.
2. If auto-trade is enabled, `WebullTrader` is initialized and login is attempted.
3. `StockMonitorClient` receives Discord messages.
4. Guard checks run (target channel, not self message, minimum content).
5. `AIParser.parse(...)` builds prompt context and calls provider (`openai`/`anthropic`/`google`).
6. AI output is normalized to `ParsedMessage`/`ParsedPick`.
7. Picks are notified/logged and mapped into stock orders (`BUY`/`SELL`; `HOLD` skipped).

## Core Components

| Component | Responsibility | File |
|---|---|---|
| Entrypoint | Bootstraps config, trader, and client | `src/main.py` |
| Discord client | Message handling and orchestration | `src/discord_client.py` |
| AI parser | Prompt rendering, provider call, output normalization | `src/ai_parser.py` |
| Parser models | Parser output contract | `src/models/parser_models.py` |
| Trader | Webull API integration and order placement | `src/webull_trader.py` |
| Config loader | Env + YAML config resolution | `config/settings.py` |

## Parser -> Trader Contract

`StockMonitorClient` only uses these parser fields for trading decisions:

| Parser field | Used for |
|---|---|
| `ticker` | Target symbol |
| `action` | `BUY` / `SELL` / `HOLD` routing |
| `weight_percent` | Optional sizing hint to trader |
| `meta.*` | Observability and debug context |

Other AI fields may exist but do not currently change order routing.

## AI Prompt Template (Rules + Variables)

Prompt template source: `config/ai_parser.prompt`.

Runtime variables currently injected by `AIParser`:

- Always: `CURRENT_TIME`, `AUTHOR_NAME`, `MESSAGE_TEXT`, `ANALYST_NAME`, `ANALYST_PREFERENCES`, `ACCOUNT_CONSTRAINTS`.
- When trader/account context exists: `ACCOUNT_BALANCE`, `MARGIN_POWER`, `CASH_POWER`, `MARGIN_EQUITY_PERCENTAGE`.
- Current gaps: placeholders like full live `OPTIONS_CHAIN` are not fully populated yet.

Core parsing rules from the template:

- Extract only clear action picks (`Added`, `Buying`, `Trimming`, `Exiting`, `Selling`).
- Ignore commentary/watchlist text with no explicit action.
- Apply the options-intent rule: intent language for calls/puts counts as actionable options BUY intent.
- Return structured JSON with `picks` and `summary`.

Contract boundary note:

- `AIParser` normalizes provider output through `ParsedMessage`/`ParsedPick`.
- Trading adapter currently routes only `ticker`, `action`, and optional `weight_percent`.
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

## Configuration Files

- Secrets: `.env`
- Main app settings: `config/trading.yaml`
- AI prompt template: `config/ai_parser.prompt`

## Testing And Confidence

Detailed confidence policy and suite organization live in:

- `tests/README.md`

Main commands:

```bash
pytest
pytest -m smoke
python -m scripts.quality.run_health_checks
python -m scripts.quality.run_confidence_suite
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
