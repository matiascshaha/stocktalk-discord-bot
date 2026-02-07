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

### `scripts/healthcheck.py`

Reliability health check runner for deterministic checks and optional smoke checks.

#### Usage

```bash
python -m scripts.healthcheck
```

#### What It Runs

1. Config/path validation
2. Deterministic path/parser/Discord/Webull contract checks
3. AI live smoke (only when `RUN_LIVE_AI_TESTS=1`)
4. AI->trader live pipeline smoke (only when `RUN_LIVE_AI_TESTS=1`)
5. Discord live smoke (only when `RUN_DISCORD_LIVE_SMOKE=1`)
6. Webull read smoke (only when `RUN_WEBULL_READ_SMOKE=1`)
7. Webull write smoke (only when `RUN_WEBULL_WRITE_TESTS=1`)

#### Output

- Human-readable summary in terminal (`GREEN` / `YELLOW` / `RED`)
- JSON report written to:

```text
artifacts/health_report.json
```

Exit codes:

- `0` = green
- `1` = deterministic failure
- `2` = external-smoke-only failure

---

### `scripts/full_confidence.py`

One-command confidence runner for deterministic + full end-to-end profiles.

#### Usage

```bash
# strict full profile (default)
python -m scripts.full_confidence

# deterministic-only profile
python -m scripts.full_confidence --mode deterministic

# include Webull write-path smoke (opt-in)
python -m scripts.full_confidence --include-webull-write

# force Webull smoke against paper/UAT endpoint
python -m scripts.full_confidence --webull-smoke-paper-trade
```

#### What It Does

1. Loads `.env`
2. Applies profile flags (`FULL_CONFIDENCE_REQUIRED`, smoke env toggles)
3. Runs deterministic `pytest` first
4. Runs `python -m scripts.healthcheck`
5. Prints report path (`artifacts/health_report.json`)

Note:
- Default full profile uses production Webull read smoke (`WEBULL_SMOKE_PAPER_TRADE=0`).
- Write profile follows your configured `PAPER_TRADE` unless `--webull-smoke-paper-trade` is passed.
- Live AI pipeline uses one representative message by default for cost control; set `RUN_LIVE_AI_PIPELINE_FULL=1` to run all fixture messages.
- Production write smoke can fail outside market hours; this is expected and should be rerun during trading hours for full write-path validation.

#### Why Use It

- Single canonical command for confidence verification
- Preflight warnings for missing credentials
- Clear strict gate behavior in one place

---

### `scripts/test_credentials.py`

Tests all configured credentials to ensure they're valid before running the monitor.

#### Usage

```bash
python -m scripts.test_credentials
```

#### What It Tests

1. **Discord Token** - Validates your Discord token by attempting to log in
2. **Discord Channel ID** - Verifies the channel ID format is correct
3. **AI API Key** - Tests the configured AI provider's API key (from config/trading.yaml or .env):
   - OpenAI (if `AI_PROVIDER=openai`)
   - Anthropic (if `AI_PROVIDER=anthropic`)
   - Google (if `AI_PROVIDER=google`)
4. **Webull OpenAPI Credentials** - Tests Webull OpenAPI login (optional, only if credentials are provided)

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
   You can now run: python -m src.main
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
4. Project is installed in editable mode: `pip install -e .`

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
python -m scripts.test_credentials
```

### With Virtual Environment

```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# Then run scripts
python -m scripts.test_credentials
```

---

## Adding New Scripts

To add new helper scripts:

1. Create the script in `scripts/` directory
2. Add a shebang line: `#!/usr/bin/env python3`
3. Keep imports package-based (`src.*`, `config.*`) and run scripts with `python -m scripts.<name>`
4. Document the script in this file
5. Make it executable (optional): `chmod +x scripts/your_script.py`

---

## Troubleshooting

### Script Won't Run

**Error: "No module named 'config'"**
- Make sure you're running from project root
- Install project in editable mode: `pip install -e .`
- Check that `scripts/` directory exists
- Ensure the command uses module style: `python -m scripts.test_credentials`

**Error: "ModuleNotFoundError"**
- Install dependencies: `pip install -r requirements.txt`
- Install project package: `pip install -e .`
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
