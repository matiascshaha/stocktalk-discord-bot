# Helper Scripts Documentation

This project includes helper scripts to make setup and testing easier.

## Available Scripts

### `scripts/setup.py` / `scripts/setup.bat` / `scripts/setup.sh`

**Automated setup script** that handles the entire project setup process.

#### Usage

**Windows:**
```bash
# Option 1: Run the batch script (easiest)
scripts\setup.bat

# Option 2: Run the Python script
python scripts\setup.py
```

**Linux/macOS:**
```bash
# Option 1: Run the shell script (easiest)
chmod +x scripts/setup.sh
./scripts/setup.sh

# Option 2: Run the Python script
python3 scripts/setup.py
```

#### What It Does

1. **Checks Python version** (requires 3.8+)
2. **Creates virtual environment** (`venv/` directory)
3. **Installs all dependencies** from `requirements.txt`
4. **Creates `.env` file** from `.env.example` (if it doesn't exist)
5. **Creates data directory** for logs

#### Features

- Cross-platform (Windows, Linux, macOS)
- Handles existing virtual environments gracefully
- Upgrades pip automatically
- Provides clear next steps after setup

#### Example Output

```
╔═══════════════════════════════════════════════════════════╗
║     Discord Stock Monitor - Automated Setup Script        ║
╚═══════════════════════════════════════════════════════════╝

============================================================
Step 1: Checking Python Version
============================================================
Python version: 3.10.5
✅ Python version is compatible

============================================================
Step 2: Creating Virtual Environment
============================================================
Creating virtual environment at: C:\...\venv
✅ Virtual environment created successfully

============================================================
Step 3: Installing Dependencies
============================================================
Upgrading pip...
Installing packages from requirements.txt...
✅ All dependencies installed successfully
```

---

### `scripts/test_credentials.py`

Tests all configured credentials to ensure they're valid before running the monitor.

#### Usage

```bash
python scripts/test_credentials.py
```

#### What It Tests

1. **Discord Token** - Validates your Discord token by attempting to log in
2. **Discord Channel ID** - Verifies the channel ID format is correct
3. **AI API Key** - Tests the configured AI provider's API key:
   - OpenAI (if `AI_PROVIDER=openai`)
   - Anthropic (if `AI_PROVIDER=anthropic`)
   - Google (if `AI_PROVIDER=google`)
4. **Webull Credentials** - Tests Webull login (optional, only if credentials are provided)

#### Output Example

```
╔═══════════════════════════════════════════════════════════╗
║        Discord Stock Monitor - Credential Tester          ║
╚═══════════════════════════════════════════════════════════╝

============================================================
Testing Discord Token...
============================================================
✅ Discord token is valid!
   Logged in as: YourUsername#1234
   User ID: 123456789012345678

============================================================
Testing Discord Channel ID...
============================================================
✅ Channel ID format is valid: 987654321098765432
   Note: Cannot verify channel exists without valid Discord token

============================================================
Testing OpenAI API Key...
============================================================
✅ OpenAI API key is valid!
   Model: gpt-4o-mini
   Response: test

============================================================
Test Summary
============================================================
  Discord Token: ✅ Passed
  Discord Channel: ✅ Passed
  Openai: ✅ Passed
  Webull: ⏭️  Skipped

============================================================
✅ All required credentials are valid!
   You can now run: python src/main.py
============================================================
```

#### When to Use

- **After setting up `.env`** - Verify all credentials work before running the monitor
- **After changing credentials** - Test new API keys or tokens
- **Troubleshooting** - If the monitor isn't working, run this to identify credential issues

#### Requirements

The script will automatically test credentials based on what's in your `.env` file. Make sure:

1. `.env` file exists in the project root
2. Required credentials are filled in
3. Dependencies are installed: `pip install -r requirements.txt`

#### Error Messages

- **"DISCORD_TOKEN not found"** - Add your Discord token to `.env`
- **"Invalid Discord token"** - Token is incorrect or expired, get a new one
- **"API key test failed"** - Check your API key and billing status
- **"Package not installed"** - Install missing dependencies

---

## Running Scripts

### From Project Root

```bash
# Make sure you're in the project root directory
cd discord-stock-monitor

# Run the credential tester
python scripts/test_credentials.py
```

### With Virtual Environment

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# Then run scripts
python scripts/test_credentials.py
```

---

## Adding New Scripts

To add new helper scripts:

1. Create the script in `scripts/` directory
2. Add a shebang line: `#!/usr/bin/env python3`
3. Add project root to path (see `test_credentials.py` for example)
4. Document the script in this file
5. Make it executable (optional): `chmod +x scripts/your_script.py`

---

## Troubleshooting

### Script Won't Run

**Error: "No module named 'config'"**
- Make sure you're running from project root
- Check that `scripts/` directory exists
- Verify Python path setup in script

**Error: "ModuleNotFoundError"**
- Install dependencies: `pip install -r requirements.txt`
- Check that virtual environment is activated

### Script Runs But Tests Fail

- Check `.env` file exists and has correct values
- Verify credentials are valid (not expired)
- Ensure billing is enabled on API accounts
- Check internet connection

---

## Security Notes

- Scripts read from `.env` file (never commit this file!)
- Scripts may log credentials in error messages - be careful
- Test scripts make real API calls (may incur small costs)
- Discord token test logs you into Discord (safe, but be aware)

---

## Future Scripts

Potential scripts to add:

- `scripts/setup_wizard.py` - Interactive setup guide
- `scripts/analyze_logs.py` - Analyze picks_log.jsonl and trades_log.jsonl
- `scripts/backup_config.py` - Backup and restore configuration
- `scripts/monitor_status.py` - Check if monitor is running
