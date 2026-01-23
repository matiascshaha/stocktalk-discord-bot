# Discord Stock Monitor 📊

An intelligent stock monitoring and auto-trading system that watches Discord channels for stock picks and optionally executes trades on Webull using AI-powered message interpretation.

## 🎯 What It Does

This application monitors a specific Discord channel for stock trading signals and:

1. **Monitors Discord** - Listens to messages in real-time
2. **AI Analysis** - Uses Claude AI to intelligently parse stock picks from natural language
3. **Smart Detection** - Identifies tickers, actions (BUY/SELL/HOLD), confidence levels, and urgency
4. **Notifications** - Sends desktop alerts and copies tickers to clipboard
5. **Auto-Trading** - Optionally executes trades automatically on Webull
6. **Complete Logging** - Records all picks and trades for analysis

## 🏗️ Architecture
┌─────────────────┐
│  Discord API    │ ← Monitors channel for messages
└────────┬────────┘
│
▼
┌─────────────────┐
│  AI Parser      │ ← Claude AI analyzes message content
│  (Anthropic)    │   - Extracts tickers
└────────┬────────┘   - Determines action (BUY/SELL/HOLD)
│            - Calculates confidence
│            - Assesses urgency & sentiment
▼
┌─────────────────┐
│  Decision       │ ← Validates pick against thresholds
│  Engine         │   - Confidence > MIN_CONFIDENCE?
└────────┬────────┘   - AUTO_TRADE enabled?
│            - Sufficient funds?
│
├──────────────┐
│              │
▼              ▼
┌─────────────────┐  ┌─────────────────┐
│  Notifier       │  │  Webull Trader  │
│  - Desktop alert│  │  - Place order  │
│  - Sound        │  │  - Log trade    │
│  - Clipboard    │  └─────────────────┘
└─────────────────┘

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Discord account (with access to target channel)
- Anthropic API key
- Webull account (optional, for trading)

### Installation

**Quick Setup (Recommended):**

**Windows:**
```bash
git clone https://github.com/yourusername/discord-stock-monitor.git
cd discord-stock-monitor
scripts\setup.bat
```

**Linux/macOS:**
```bash
git clone https://github.com/yourusername/discord-stock-monitor.git
cd discord-stock-monitor
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The setup script will automatically:
- Create virtual environment
- Install all dependencies
- Create `.env` file from template
- Set up data directory

**Manual Setup (Alternative):**
```bash
# Clone the repository
git clone https://github.com/yourusername/discord-stock-monitor.git
cd discord-stock-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # Or use your preferred editor
```

### Configuration

Edit `.env` file:
```env
# Discord
DISCORD_TOKEN=your_discord_token_here
CHANNEL_ID=1234567890

# Anthropic AI
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Webull (optional)
WEBULL_USERNAME=your_email@example.com
WEBULL_PASSWORD=your_password
WEBULL_TRADING_PIN=123456

# Trading Settings
AUTO_TRADE=false
MIN_CONFIDENCE=0.7
DEFAULT_AMOUNT=1000
USE_MARKET_ORDERS=true
```

### Run
```bash
python src/main.py
```

## 📋 Features

### AI-Powered Parsing

The system uses Claude AI to understand natural language:

**Example Messages:**
- "Loading up on AAPL 20%, TSLA 15%" → BUY signals with allocations
- "Taking profits on NVDA" → SELL signal
- "SPY 450C 12/29 looking juicy" → Options call detection
- "All in on MSFT now!!!" → HIGH urgency BUY

**AI Extracts:**
- **Ticker**: Stock symbol
- **Action**: BUY, SELL, or HOLD
- **Confidence**: 0.0-1.0 (how certain the AI is)
- **Weight**: Portfolio allocation percentage
- **Urgency**: LOW, MEDIUM, or HIGH
- **Sentiment**: BULLISH, BEARISH, or NEUTRAL
- **Reasoning**: Why it identified this as a pick

### Smart Trading Logic

Only executes trades when:
- ✅ `AUTO_TRADE` is enabled
- ✅ AI confidence ≥ `MIN_CONFIDENCE` threshold
- ✅ Sufficient buying power available
- ✅ Action is BUY (SELL requires manual confirmation)
- ✅ Stock is supported (not options, for now)

### Comprehensive Logging

All activity logged to:
- `data/picks_log.jsonl` - Every detected pick
- `data/trades_log.jsonl` - Every executed trade

JSON format for easy analysis with pandas/Excel.

## ⚙️ Configuration

### Trading Parameters
```python
# config/settings.py

# Minimum AI confidence to execute trade (0.0-1.0)
MIN_CONFIDENCE = 0.7  # Only trade if 70%+ confident

# Default trade size if no weight specified
DEFAULT_AMOUNT = 1000  # $1000 per trade

# Order type
USE_MARKET_ORDERS = True  # False for limit orders

# Enable/disable auto-trading
AUTO_TRADE = False  # Start with False!
```

### Notification Settings
```python
DESKTOP_NOTIFICATIONS = True  # Popup alerts
SOUND_ALERT = True           # Beep on new pick
COPY_TO_CLIPBOARD = True     # Auto-copy ticker
```

## 🔐 Security

- **Never commit `.env`** - Contains sensitive credentials
- **Use paper trading** - Test with Webull paper account first
- **Start with `AUTO_TRADE=False`** - Verify picks manually initially
- **Keep API keys secret** - Your Discord token = full account access

## ⚠️ Warnings

### Discord Terms of Service

Using a self-bot (running as your user account) technically violates Discord's Terms of Service. However:
- This is **passive monitoring only** (not spamming/botting)
- Enforcement is typically focused on disruptive behavior
- Use at your own discretion and risk

### Trading Risks

- **Automated trading carries significant financial risk**
- **Start with small amounts** (`DEFAULT_AMOUNT = 100`)
- **Test thoroughly with paper trading**
- **Monitor the first several trades manually**
- **This is not financial advice**

## 📊 Usage Examples

### Monitor Only Mode (Safest)
```env
AUTO_TRADE=false
```

You'll get notifications but no trades execute. Perfect for:
- Testing the system
- Manually reviewing picks
- Learning the channel's patterns

### Semi-Automated Mode
```env
AUTO_TRADE=false
MIN_CONFIDENCE=0.8
```

High confidence picks notify you, but you manually execute trades.

### Full Auto Mode (Advanced)
```env
AUTO_TRADE=true
MIN_CONFIDENCE=0.85
DEFAULT_AMOUNT=500
```

System automatically trades picks with 85%+ confidence.

## 🧪 Testing
```bash
# Run tests
pytest tests/

# Test AI parser
python -m pytest tests/test_parser.py -v

# Test trader (paper trading mode)
python -m pytest tests/test_trader.py -v
```

## 📈 Monitoring Performance
```bash
# View recent picks
tail -f data/picks_log.jsonl | jq

# View executed trades
tail -f data/trades_log.jsonl | jq

# Analyze with Python
python scripts/analyze_performance.py
```

## 🛠️ Development

### Adding Custom Parsers

Edit `src/ai_parser.py` to customize AI prompts or add fallback logic.

### Adding New Brokers

Extend `src/webull_trader.py` or create new trader modules for other brokers.

### Custom Notifications

Modify `src/notifier.py` to add Telegram, Slack, or webhook integrations.

## 📚 Documentation

- [Setup Guide](docs/SETUP.md) - Quick start and installation
- [Credentials Setup](docs/CREDENTIALS_SETUP.md) - Detailed credential setup instructions
- [AI Provider Comparison](docs/AI_PROVIDER_COMPARISON.md) - Choose the best AI provider
- [Helper Scripts](docs/SCRIPTS.md) - Test credentials and utilities
- [Architecture Details](docs/ARCHITECTURE.md) - System design and data flow
- [API Reference](docs/API.md) - Code documentation

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Anthropic Claude AI for intelligent parsing
- Discord.py community
- Webull API contributors

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check existing discussions
- Review documentation in `/docs`

---

**Disclaimer**: This software is provided as-is. Use at your own risk. Always test with paper trading before real money. Not financial advice.
