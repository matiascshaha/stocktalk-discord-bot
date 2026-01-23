# Architecture Documentation

## Overview

The Discord Stock Monitor is a modular system that monitors Discord channels for stock trading signals, uses AI to parse natural language messages, and optionally executes trades on Webull.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Discord API                            │
│                  (discord.py-self)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              StockMonitorClient                             │
│  - Message filtering                                         │
│  - Event handling                                           │
│  - Orchestration                                            │
└───────────────┬─────────────────────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│  AIParser    │  │  Notifier    │
│  - Claude AI │  │  - Desktop   │
│  - Parsing   │  │  - Clipboard │
│  - Fallback  │  │  - Sound     │
└──────┬───────┘  └──────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│              Decision Engine                                 │
│  - Confidence threshold                                      │
│  - Trading rules                                            │
│  - Validation                                               │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              WebullTrader                                   │
│  - Authentication                                           │
│  - Order execution                                          │
│  - Trade logging                                            │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. StockMonitorClient (`src/discord_client.py`)

**Responsibilities:**
- Discord connection management
- Message filtering and routing
- Event handling (on_ready, on_message)
- Orchestrating parser, notifier, and trader

**Key Methods:**
- `on_ready()`: Initialization and status logging
- `on_message()`: Message processing pipeline
- `_log_picks()`: Persistence of detected picks

### 2. AIParser (`src/ai_parser.py`)

**Responsibilities:**
- Natural language understanding via Claude AI
- Stock pick extraction from messages
- Fallback regex parsing if AI fails

**Key Methods:**
- `parse()`: Main parsing interface
- `_build_prompt()`: AI prompt construction
- `_clean_json()`: Response sanitization
- `_fallback_parse()`: Regex-based backup parser

**AI Output Format:**
```json
[
  {
    "ticker": "AAPL",
    "action": "BUY",
    "confidence": 0.95,
    "weight": 20.0,
    "strike": null,
    "option_type": "STOCK",
    "expiry": null,
    "reasoning": "...",
    "urgency": "MEDIUM",
    "sentiment": "BULLISH"
  }
]
```

### 3. Notifier (`src/notifier.py`)

**Responsibilities:**
- Desktop notifications (cross-platform)
- Console output formatting
- Clipboard integration
- Sound alerts

**Key Methods:**
- `notify()`: Main notification interface
- `_send_desktop_notification()`: OS-specific notifications
- `_copy_to_clipboard()`: Ticker copying
- `_play_sound()`: System sound alerts

### 4. WebullTrader (`src/webull_trader.py`)

**Responsibilities:**
- Webull API authentication
- Order placement and execution
- Account balance checking
- Trade logging

**Key Methods:**
- `login()`: Webull authentication
- `execute_trade()`: Trade execution pipeline
- `_should_trade()`: Decision logic
- `_place_order()`: Order placement
- `_log_trade()`: Trade persistence

**Trading Rules:**
- Only executes BUY orders automatically
- SELL requires manual confirmation
- Options not supported (stocks only)
- Confidence threshold check
- Sufficient funds validation

### 5. Configuration (`config/settings.py`)

**Responsibilities:**
- Environment variable loading
- Configuration validation
- Settings organization

**Configuration Groups:**
- `DISCORD_TOKEN`, `CHANNEL_ID`: Discord settings
- `ANTHROPIC_API_KEY`: AI service
- `WEBULL_CONFIG`: Trading account
- `TRADING_CONFIG`: Trading parameters
- `NOTIFICATION_CONFIG`: Alert settings

### 6. Utilities (`src/utils/`)

**Logger (`logger.py`):**
- Centralized logging setup
- Consistent formatting
- Console output

**Validators (`validators.py`):**
- Ticker format validation
- Confidence score validation
- Pick structure validation

## Data Flow

### Message Processing Pipeline

1. **Message Received** → `on_message()` triggered
2. **Filtering** → Channel ID, author, length checks
3. **AI Parsing** → `AIParser.parse()` extracts picks
4. **Notification** → Desktop alert, console output, clipboard
5. **Logging** → Pick saved to `data/picks_log.jsonl`
6. **Trading Decision** → If trader available and conditions met
7. **Order Execution** → Webull order placed
8. **Trade Logging** → Trade saved to `data/trades_log.jsonl`

### Error Handling

- **AI Parsing Failure** → Falls back to regex parser
- **Webull Login Failure** → Continues in monitor-only mode
- **Order Execution Failure** → Logged, no crash
- **Notification Failure** → Logged, continues processing

## Data Persistence

### Picks Log (`data/picks_log.jsonl`)

JSONL format (one JSON object per line):
```json
{
  "timestamp": "2025-01-22T10:30:00",
  "author": "User#1234",
  "message": "Loading up on AAPL 20%",
  "message_url": "https://discord.com/...",
  "ai_parsed_picks": [...]
}
```

### Trades Log (`data/trades_log.jsonl`)

JSONL format:
```json
{
  "timestamp": "2025-01-22T10:30:05",
  "ticker": "AAPL",
  "action": "BUY",
  "quantity": 10,
  "price": 150.25,
  "total_cost": 1502.50,
  "confidence": 0.95,
  "reasoning": "...",
  "order": {...},
  "pick_details": {...}
}
```

## Security Considerations

1. **Environment Variables**: All secrets in `.env` (gitignored)
2. **Discord Token**: Full account access - keep secure
3. **Trading PIN**: Required for Webull trades
4. **API Keys**: Anthropic API key for AI parsing

## Extension Points

### Adding New Brokers

1. Create new trader class (e.g., `InteractiveBrokersTrader`)
2. Implement same interface as `WebullTrader`
3. Update `main.py` to support broker selection

### Adding New Notification Channels

1. Extend `Notifier` class
2. Add new methods (e.g., `_send_telegram()`)
3. Update `NOTIFICATION_CONFIG`

### Customizing AI Prompts

1. Modify `AIParser._build_prompt()`
2. Adjust extraction criteria
3. Test with sample messages

## Performance Considerations

- **AI API Calls**: Rate limits apply, consider caching
- **Discord Rate Limits**: Self-bot may have stricter limits
- **Webull API**: Order execution is synchronous
- **Logging**: File I/O is blocking (consider async for high volume)

## Future Enhancements

- Async/await throughout for better concurrency
- Database backend instead of JSONL files
- Web dashboard for monitoring
- Multi-channel support
- Options trading support
- Portfolio management features
