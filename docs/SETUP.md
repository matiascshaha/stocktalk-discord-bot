# Setup Guide

## Prerequisites

Before setting up the Discord Stock Monitor, ensure you have:

1. **Python 3.8+** installed
2. **Discord account** with access to the target channel
3. **Anthropic API key** (for Claude AI)
4. **Webull account** (optional, only if using auto-trading)

## Step-by-Step Setup

### 1. Clone or Download the Repository

```bash
git clone https://github.com/yourusername/discord-stock-monitor.git
cd discord-stock-monitor
```

### 2. Automated Setup (Recommended)

**Windows:**
```bash
scripts\setup.bat
```

**Linux/macOS:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Or use Python script (cross-platform):**
```bash
python scripts/setup.py
```

This will automatically:
- Create virtual environment
- Install all dependencies
- Create `.env` file from `.env.example`
- Set up data directory

### 3. Manual Setup (Alternative)

If you prefer manual setup:

**Create Virtual Environment:**

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

### 4. Get Credentials

**See [CREDENTIALS_SETUP.md](CREDENTIALS_SETUP.md) for detailed step-by-step instructions.**

Quick summary:
- **Discord Token**: Extract from browser console (see CREDENTIALS_SETUP.md section 1)
- **Discord Channel ID**: Enable Developer Mode, right-click channel → "Copy Channel ID"
- **AI API Key**: Choose provider (OpenAI recommended - see [AI_PROVIDER_COMPARISON.md](AI_PROVIDER_COMPARISON.md))
- **Webull OpenAPI Credentials**: Optional, only needed if `AUTO_TRADE=true`

**Quick Test**: After setting up credentials, test them with:
```bash
python scripts/test_credentials.py
```

### 8. Create Environment File

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
# Windows: notepad .env
# macOS/Linux: nano .env
```

### 8b. Configure (no-code)

Edit these files to control AI, trading, and notifications without touching Python:

- `config/config.yaml`
- `config/ai_parser.prompt`

Fill in your `.env` file:

```env
# Discord Configuration
DISCORD_TOKEN=your_actual_token_here
CHANNEL_ID=123456789012345678

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# Webull OpenAPI Configuration (Optional)
WEBULL_APP_KEY=your_webull_app_key
WEBULL_APP_SECRET=your_webull_app_secret
WEBULL_REGION=US
# WEBULL_ACCOUNT_ID=your_account_id

# Trading Settings
AUTO_TRADE=false
MIN_CONFIDENCE=0.7
DEFAULT_AMOUNT=1000
USE_MARKET_ORDERS=true

# Notification Settings
DESKTOP_NOTIFICATIONS=true
SOUND_ALERT=true
COPY_TO_CLIPBOARD=true
```

### 9. Create Data Directory

```bash
# Ensure data directory exists
mkdir -p data
```

The `.gitkeep` file should already be there.

### 10. Test Configuration

**Recommended: Use the credential testing script:**
```bash
python scripts/test_credentials.py
```

This will test all your credentials (Discord, AI API, Webull) and verify they work correctly.

**Alternative: Quick validation:**
```bash
python -c "from config.settings import validate_config; errors = validate_config(); print('✅ Valid' if not errors else f'❌ Errors: {errors}')"
```

See [SCRIPTS.md](SCRIPTS.md) for more information about helper scripts.

### 11. Run the Monitor

**Monitor-Only Mode (Safest):**
```bash
python src/main.py
```

You should see:
```
╔═══════════════════════════════════════════════════════════╗
║   AI-Powered Discord Stock Monitor + Webull Trading      ║
║   Powered by Claude AI for intelligent message parsing   ║
╚═══════════════════════════════════════════════════════════╝

✅ Configuration valid
ℹ️  Auto-trading disabled - running in monitor-only mode
🚀 Starting Discord monitor...
🤖 DISCORD STOCK MONITOR ACTIVE
```

## Verification Steps

### 1. Test Discord Connection

- Bot should log in successfully
- Should show "Logged in as: YourUsername"
- Should display the channel ID being monitored

### 2. Test AI Parsing

Send a test message in the monitored channel:
```
Loading up on AAPL 20%
```

You should see:
- Console output showing the pick
- Desktop notification (if enabled)
- Entry in `data/picks_log.jsonl`

### 3. Test Notifications

Verify:
- Desktop notification appears
- Ticker copied to clipboard
- Sound plays (if enabled)
- Console shows formatted output

### 4. Test Auto-Trading (Advanced)

**⚠️ Start with small amounts and paper trading!**

1. Set `AUTO_TRADE=true` in `.env`
2. Set `DEFAULT_AMOUNT=100` (small test amount)
3. Set `MIN_CONFIDENCE=0.9` (very high threshold)
4. Restart the monitor
5. Send a high-confidence pick in the channel
6. Check `data/trades_log.jsonl` for executed trades

## Troubleshooting

### Discord Connection Issues

**Error: "Invalid token"**
- Verify token is correct (no extra spaces)
- Token should start with your user ID
- Make sure you copied the full token

**Error: "Connection closed"**
- Check internet connection
- Discord may be rate-limiting
- Try restarting the client

### AI Parsing Issues

**Error: "API key invalid"**
- Verify `ANTHROPIC_API_KEY` in `.env`
- Check API key has sufficient credits
- Ensure key starts with `sk-ant-`

**No picks detected:**
- AI may be too conservative
- Try lowering confidence threshold in prompt
- Check `data/picks_log.jsonl` for what was detected

### Webull Issues

**Login fails:**
- Verify credentials in `.env`
- Check if 2FA is enabled (may need to disable)
- Verify your Webull OpenAPI App Key/Secret are correct

**Order execution fails:**
- Check account has sufficient funds
- Verify trading PIN is correct
- Check if market is open (for market orders)
- Review Webull API documentation for changes

### Notification Issues

**Desktop notifications not working:**
- Windows: Check notification settings in Windows
- macOS: Check System Preferences → Notifications
- Linux: May need `libnotify` installed

**Sound not playing:**
- Windows: Check system volume
- macOS/Linux: May need additional packages

## Production Deployment

### Running as a Service

**Windows (Task Scheduler):**
1. Create a batch file: `start_monitor.bat`
2. Add to Task Scheduler to run on startup

**Linux (systemd):**
Create `/etc/systemd/system/stock-monitor.service`:
```ini
[Unit]
Description=Discord Stock Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/discord-stock-monitor
ExecStart=/path/to/venv/bin/python src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Monitoring and Logs

- Check `data/picks_log.jsonl` for all detected picks
- Check `data/trades_log.jsonl` for executed trades
- Monitor console output for errors
- Set up log rotation for long-running instances

### Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore`
2. **Use environment variables** in production (not `.env` file)
3. **Restrict file permissions**: `chmod 600 .env`
4. **Use paper trading** for initial testing
5. **Monitor first trades manually** before full automation
6. **Set up alerts** for unexpected behavior

## Next Steps

1. **Test Credentials**: Run `python scripts/test_credentials.py` to verify everything works
2. **Review AI Providers**: See [AI_PROVIDER_COMPARISON.md](AI_PROVIDER_COMPARISON.md) to choose the best provider
3. **Review Architecture**: Read `docs/ARCHITECTURE.md`
4. **Understand API**: Read `docs/API.md`
5. **Customize Settings**: Adjust thresholds in `.env`
6. **Test Thoroughly**: Run in monitor-only mode first
7. **Start Small**: Use small amounts when enabling auto-trade

## Getting Help

- Check existing GitHub issues
- Review documentation in `/docs`
- Test with monitor-only mode first
- Verify all credentials are correct

---

**Remember**: Start with `AUTO_TRADE=false` and test thoroughly before enabling automated trading!
