# Credentials Setup Guide

This guide walks you through obtaining all the credentials needed to run the Discord Stock Monitor. **Webull OpenAPI credentials are optional** and can be added later when your developer account is approved.

## Prerequisites

- Discord account with access to the target channel
- Email address for API account creation
- Browser with Developer Tools access

---

## 1. Discord Token

**⚠️ Security Warning:** Your Discord token is like a password. Anyone with it can access your account. Never share it or commit it to version control.

### Method 1: Browser Console (Recommended for 2025)

1. **Open Discord in your browser**
   - Go to [discord.com](https://discord.com) and log in
   - Or use the Discord web app

2. **Open Developer Tools**
   - Press `F12` (Windows/Linux) or `Cmd + Option + I` (macOS)
   - Or right-click → "Inspect" → "Console" tab

3. **Run the token extraction script**
   - Go to the **Console** tab
   - Paste this code and press Enter:

```javascript
let token;
webpackChunkdiscord_app.push([
 [Math.random()],
 {},
 (r) => {
 for (let m of Object.values(r.c)) {
 try {
 if (m?.exports?.default?.getToken !== undefined) {
 token = m.exports.default.getToken();
 break;
 }
 } catch (e) {}
 }
 }
]);
token;
```

4. **Copy the token**
   - The token will be displayed in the console
   - It should look like: `MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.ABC123.XYZ789`
   - Copy the entire token (it's long!)

5. **Paste into `.env` file**
   ```env
   DISCORD_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.ABC123.XYZ789
   ```

### Method 2: Local Storage (Alternative)

If Method 1 doesn't work:

1. Open Developer Tools (`F12`)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Enable mobile emulation: `Ctrl + Shift + M` (Windows) or `Cmd + Shift + M` (macOS)
4. Navigate to **Local Storage** → `https://discord.com`
5. Find the `token` key and copy its value

### Troubleshooting

- **Token not showing?** Try refreshing Discord and running the script again
- **Script error?** Make sure you're on the main Discord page, not a specific channel
- **Token expired?** Discord tokens can expire; you may need to regenerate

---

## 2. Discord Channel ID

The Channel ID identifies which Discord channel to monitor.

### Step-by-Step

1. **Enable Developer Mode**
   - Open Discord (desktop app or browser)
   - Click the **gear icon** ⚙️ (User Settings) at bottom-left
   - In the left sidebar, scroll to **Advanced**
   - Toggle **Developer Mode** to ON

2. **Get the Channel ID**
   - Navigate to the Discord server
   - Find the text channel you want to monitor
   - **Right-click** on the channel name (in the channel list)
   - Select **"Copy Channel ID"**

3. **Paste into `.env` file**
   ```env
   CHANNEL_ID=123456789012345678
   ```
   - The ID is a long number (usually 17-19 digits)

### Alternative Method: From URL

If you can't right-click:
1. Open the channel in Discord
2. Look at the URL: `https://discord.com/channels/SERVER_ID/CHANNEL_ID`
3. The last number in the URL is the Channel ID

### Troubleshooting

- **No "Copy Channel ID" option?** Make sure Developer Mode is enabled
- **Wrong channel?** Double-check you're copying the ID of the text channel, not a voice channel or category

---

## 3. AI API Key

Choose your AI provider based on the [AI Provider Comparison](AI_PROVIDER_COMPARISON.md). Instructions for each:

### Option A: OpenAI (GPT-4o mini) - Recommended

**Why:** Best cost/performance ratio for this use case.

1. **Create an OpenAI Account**
   - Go to [platform.openai.com](https://platform.openai.com)
   - Click "Sign Up" or "Log In"
   - Complete account setup (may require phone verification)

2. **Navigate to API Keys**
   - Once logged in, click your profile icon (top-right)
   - Select **"API keys"** from the dropdown
   - Or go directly to: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

3. **Create a New API Key**
   - Click **"+ Create new secret key"**
   - Give it a name (e.g., "Discord Stock Monitor")
   - Click **"Create secret key"**
   - **⚠️ IMPORTANT:** Copy the key immediately - you won't see it again!
   - It starts with `sk-` and looks like: `sk-proj-ABC123...`

4. **Add Billing Information** (if required)
   - OpenAI may require payment method for API access
   - Go to Billing section and add a payment method
   - Free tier may have limited credits

5. **Paste into `.env` file**
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=sk-proj-ABC123...
   ```

### Option B: Anthropic (Claude Sonnet 4.5)

**Why:** Best quality for structured extraction, especially with prompt caching.

1. **Create an Anthropic Account**
   - Go to [console.anthropic.com](https://console.anthropic.com)
   - Click "Sign Up" or "Log In"
   - You can sign in with Google, email, or SSO
   - Agree to Anthropic's Commercial Terms

2. **Navigate to API Keys**
   - Once logged in, go to: [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)
   - Or click your profile → "Settings" → "API Keys"

3. **Create a New API Key**
   - Click **"Create Key"** or **"+ New Key"**
   - Give it a name (e.g., "Discord Stock Monitor")
   - Click **"Create Key"**
   - **⚠️ IMPORTANT:** Copy the key immediately!
   - It starts with `sk-ant-` and looks like: `sk-ant-api03-ABC123...`

4. **Add Billing Information** (if required)
   - Anthropic may require payment method
   - Go to Billing section if prompted

5. **Paste into `.env` file**
   ```env
   AI_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-api03-ABC123...
   ```

### Option C: Google (Gemini 3 Pro)

**Why:** Good middle ground, especially with batch processing.

1. **Create a Google Cloud Account**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Sign in with your Google account
   - Complete account setup (may require credit card)

2. **Enable Gemini API**
   - In Google Cloud Console, search for "Gemini API"
   - Click "Enable API"
   - Wait for activation (usually instant)

3. **Create an API Key**
   - Go to "APIs & Services" → "Credentials"
   - Click **"+ Create Credentials"** → **"API Key"**
   - Copy the generated key
   - **Optional:** Restrict the key to Gemini API only (recommended)

4. **Paste into `.env` file**
   ```env
   AI_PROVIDER=google
   GOOGLE_API_KEY=AIzaSyABC123...
   ```

### Troubleshooting API Keys

- **Key not working?** Make sure billing is enabled (most providers require this)
- **Rate limit errors?** Check your account tier/limits
- **Invalid key format?** Double-check you copied the entire key (they're long!)

---

## 4. Webull OpenAPI Credentials (Optional - Skip for Now)

**Status:** Your developer account is under review. Skip this section for now.

When your account is approved, you'll need Webull OpenAPI credentials:

- `WEBULL_APP_KEY` - Your Webull OpenAPI App Key
- `WEBULL_APP_SECRET` - Your Webull OpenAPI App Secret
- `WEBULL_REGION` - Region for your account (`US`, `HK`, or `JP`)
- `WEBULL_ACCOUNT_ID` - Optional; if omitted, the first account is used

**Note:** Leave these blank or commented out in `.env` until your account is approved.

---

## 5. Configuration Settings

These are not credentials, just configuration values. You can use the defaults or adjust.
Preferred: edit `config/trading.yaml` (no-code). The `.env` values still work as overrides.

### Trading Settings

```env
AUTO_TRADE=false              # Set to true when ready (start with false!)
MIN_CONFIDENCE=0.7            # AI confidence threshold (0.0-1.0)
DEFAULT_AMOUNT=1000           # Default trade size in USD
USE_MARKET_ORDERS=true        # true = market orders, false = limit orders
```

### Notification Settings

```env
DESKTOP_NOTIFICATIONS=true    # Show desktop popup alerts
SOUND_ALERT=true              # Play sound on new pick
COPY_TO_CLIPBOARD=true        # Auto-copy ticker to clipboard
```

---

## Complete .env File Example

Here's what your `.env` file should look like (with OpenAI as example):

```env
# Discord Configuration
DISCORD_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.ABC123.XYZ789
CHANNEL_ID=123456789012345678

# AI Provider Configuration
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-ABC123...

# OR if using Anthropic:
# AI_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-api03-ABC123...

# OR if using Google:
# AI_PROVIDER=google
# GOOGLE_API_KEY=AIzaSyABC123...

# Webull Configuration (Optional - Skip until account approved)
# WEBULL_APP_KEY=your_webull_app_key
# WEBULL_APP_SECRET=your_webull_app_secret
# WEBULL_REGION=US
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

---

## Verification Steps

After setting up your `.env` file:

1. **Check file location**
   - Make sure `.env` is in the project root (same folder as `src/`)
   - Not in `src/` or any subfolder

2. **Verify format**
   - No quotes around values (unless the value itself contains spaces)
   - No spaces around the `=` sign
   - One variable per line

3. **Test all credentials** (Recommended)
   ```bash
   python -m scripts.diagnostics.verify_credentials
   ```
   This script will test:
   - Discord token validity
   - Discord channel ID format
   - AI API key (OpenAI/Anthropic/Google)
   - Webull OpenAPI credentials (if provided)
   
   See [SCRIPTS.md](SCRIPTS.md) for more details.

4. **Quick configuration validation** (Alternative)
   ```bash
   python -c "from config.settings import validate_config; errors = validate_config(); print('✅ Valid' if not errors else f'❌ Errors: {errors}')"
   ```

5. **Run the monitor** (monitor-only mode)
   ```bash
   python -m src.main
   ```

---

## Security Best Practices

1. **Never commit `.env` to git** - It's already in `.gitignore`
2. **Don't share your tokens** - Treat them like passwords
3. **Rotate keys periodically** - Regenerate API keys if compromised
4. **Use environment variables in production** - Don't rely on `.env` files
5. **Restrict API keys** - If your provider supports it, restrict keys to specific IPs/domains

---

## Troubleshooting

### "DISCORD_TOKEN is required" error
- Check that `.env` file exists in project root
- Verify token is on one line with no extra spaces
- Make sure token starts with correct prefix (varies by Discord version)

### "CHANNEL_ID is required" error
- Verify Developer Mode is enabled
- Make sure you copied the Channel ID, not Server ID
- Check that the ID is a number (no letters)

### "API key invalid" error
- Verify you copied the entire key (they're very long)
- Check that billing is enabled on your API account
- Make sure you're using the correct key format for your provider

### "Configuration errors found"
- Run the validation command above to see specific errors
- Check `.env` file format (no quotes, correct spacing)
- Verify all required fields are present

---

## Next Steps

Once your credentials are set up:

1. ✅ Test the configuration (validation command above)
2. ✅ Run in monitor-only mode first (`AUTO_TRADE=false`)
3. ✅ Verify Discord connection works
4. ✅ Test AI parsing with sample messages
5. ✅ When Webull account is approved, add those credentials
6. ✅ Enable auto-trading only after thorough testing

For more setup details, see [SETUP.md](SETUP.md).
