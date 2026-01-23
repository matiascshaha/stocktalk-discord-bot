# API Reference

## Module: `src.discord_client`

### Class: `StockMonitorClient`

Discord client for monitoring stock picks.

#### `__init__(self, trader=None)`

Initialize the stock monitor client.

**Parameters:**
- `trader` (WebullTrader, optional): Trader instance for auto-trading. If None, runs in monitor-only mode.

#### `run(self)`

Start the Discord client and begin monitoring.

**Raises:**
- `discord.LoginFailure`: If Discord token is invalid
- `discord.ConnectionClosed`: If connection is lost

---

## Module: `src.ai_parser`

### Class: `AIParser`

AI-powered stock pick parser using Claude.

#### `__init__(self)`

Initialize the AI parser with Anthropic API client.

**Raises:**
- `ValueError`: If `ANTHROPIC_API_KEY` is not set

#### `parse(self, message_text, author_name)`

Parse stock picks from a message using AI.

**Parameters:**
- `message_text` (str): The Discord message content
- `author_name` (str): The author's username

**Returns:**
- `list`: Array of pick dictionaries, or empty list if none found

**Pick Dictionary Structure:**
```python
{
    'ticker': str,           # Stock symbol (e.g., 'AAPL')
    'action': str,           # 'BUY', 'SELL', or 'HOLD'
    'confidence': float,     # 0.0-1.0 confidence score
    'weight': float|None,   # Portfolio allocation percentage
    'strike': float|None,    # Options strike price
    'option_type': str,      # 'STOCK', 'CALL', or 'PUT'
    'expiry': str|None,      # Options expiry date
    'reasoning': str,        # AI explanation
    'urgency': str,          # 'LOW', 'MEDIUM', or 'HIGH'
    'sentiment': str         # 'BULLISH', 'BEARISH', or 'NEUTRAL'
}
```

**Raises:**
- Falls back to regex parser on any error

---

## Module: `src.webull_trader`

### Class: `WebullTrader`

Webull trading integration.

#### `__init__(self, config)`

Initialize Webull trader.

**Parameters:**
- `config` (dict): Webull configuration dictionary with keys:
  - `username` (str): Webull account email
  - `password` (str): Webull account password
  - `trading_pin` (str): Trading PIN for order execution
  - `device_name` (str): Device identifier

#### `login(self)`

Authenticate with Webull.

**Returns:**
- `bool`: True if login successful, False otherwise

**Raises:**
- Logs errors but doesn't raise exceptions

#### `execute_trade(self, pick)`

Execute a trade based on a stock pick.

**Parameters:**
- `pick` (dict): Stock pick dictionary (see `AIParser.parse()`)

**Returns:**
- `None`: Always returns None (logs errors internally)

**Behavior:**
- Only executes BUY orders automatically
- SELL orders are logged but not executed
- Options are not supported
- Validates confidence threshold
- Checks sufficient funds

---

## Module: `src.notifier`

### Class: `Notifier`

Handle notifications for stock picks.

#### `__init__(self)`

Initialize notifier with configuration.

#### `notify(self, picks, author)`

Send all configured notifications for picks.

**Parameters:**
- `picks` (list): Array of pick dictionaries
- `author` (str): Message author username

**Behavior:**
- Sends desktop notification if enabled
- Prints formatted console output
- Copies tickers to clipboard if enabled
- Plays sound alert if enabled

---

## Module: `src.utils.validators`

### `validate_ticker(ticker)`

Validate stock ticker format.

**Parameters:**
- `ticker` (str): Stock symbol to validate

**Returns:**
- `bool`: True if valid (1-5 uppercase letters)

### `validate_confidence(confidence)`

Validate confidence score.

**Parameters:**
- `confidence` (float|str): Confidence value

**Returns:**
- `bool`: True if 0.0-1.0

### `validate_weight(weight)`

Validate portfolio weight percentage.

**Parameters:**
- `weight` (float|None): Weight value

**Returns:**
- `bool`: True if None or 0.0-100.0

### `validate_pick(pick)`

Validate a complete stock pick dictionary.

**Parameters:**
- `pick` (dict): Pick dictionary to validate

**Returns:**
- `tuple`: (is_valid: bool, error: str|None)

---

## Module: `config.settings`

### Configuration Variables

#### Discord
- `DISCORD_TOKEN` (str): Discord bot/user token
- `CHANNEL_ID` (int): Target channel ID to monitor

#### Anthropic
- `ANTHROPIC_API_KEY` (str): API key for Claude AI

#### Webull
- `WEBULL_CONFIG` (dict): Configuration dictionary

#### Trading
- `TRADING_CONFIG` (dict): Trading parameters:
  - `auto_trade` (bool): Enable auto-trading
  - `min_confidence` (float): Minimum confidence threshold
  - `default_amount` (float): Default trade size in USD
  - `use_market_orders` (bool): Use market vs limit orders

#### Notifications
- `NOTIFICATION_CONFIG` (dict): Notification settings:
  - `desktop_notifications` (bool): Enable desktop alerts
  - `sound_alert` (bool): Enable sound alerts
  - `copy_to_clipboard` (bool): Auto-copy tickers

### Functions

#### `validate_config()`

Validate that required configuration is present.

**Returns:**
- `list`: Array of error messages (empty if valid)

**Checks:**
- Required: `DISCORD_TOKEN`, `CHANNEL_ID`, `ANTHROPIC_API_KEY`
- If `AUTO_TRADE=true`: Requires Webull credentials

---

## Module: `src.utils.logger`

### `setup_logger(name, level=logging.INFO)`

Setup and return a logger instance.

**Parameters:**
- `name` (str): Logger name (typically module name)
- `level` (int): Logging level (default: INFO)

**Returns:**
- `logging.Logger`: Configured logger instance

**Features:**
- Console output handler
- Timestamp formatting
- Prevents duplicate handlers

---

## Error Handling

### Common Exceptions

1. **Configuration Errors**: Handled in `main.py`, exits with error message
2. **Discord Errors**: Logged, may cause client restart
3. **AI Parsing Errors**: Falls back to regex parser
4. **Webull Errors**: Logged, continues in monitor-only mode
5. **Notification Errors**: Logged, doesn't interrupt processing

### Logging Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages (non-critical issues)
- **ERROR**: Error messages (operation failures)

---

## Usage Examples

### Basic Setup

```python
from src.discord_client import StockMonitorClient
from config.settings import validate_config

# Validate configuration
errors = validate_config()
if errors:
    print("Configuration errors:", errors)
    exit(1)

# Start monitoring (monitor-only mode)
client = StockMonitorClient()
client.run()
```

### With Auto-Trading

```python
from src.discord_client import StockMonitorClient
from src.webull_trader import WebullTrader
from config.settings import WEBULL_CONFIG, TRADING_CONFIG

# Initialize trader
trader = WebullTrader(WEBULL_CONFIG)
if trader.login():
    # Start monitoring with trading enabled
    client = StockMonitorClient(trader=trader)
    client.run()
```

### Custom Parser

```python
from src.ai_parser import AIParser

parser = AIParser()
picks = parser.parse("Loading up on AAPL 20%", "Trader123")

for pick in picks:
    print(f"{pick['ticker']}: {pick['action']} ({pick['confidence']*100}% confidence)")
```

### Manual Trade Execution

```python
from src.webull_trader import WebullTrader
from config.settings import WEBULL_CONFIG

trader = WebullTrader(WEBULL_CONFIG)
if trader.login():
    pick = {
        'ticker': 'AAPL',
        'action': 'BUY',
        'confidence': 0.9,
        'weight': 20.0,
        'option_type': 'STOCK',
        # ... other required fields
    }
    trader.execute_trade(pick)
```
