# Configuration

This folder is your no-code control center. Edit these files to change behavior without touching Python.

## 1) Main config
Edit `config/trading.yaml`.

- Secrets live in `.env` (Discord token, API keys, Webull App Key/Secret).
- Non-secret settings live here (AI provider/model, trading toggles, notifications).

Common changes:
- Set Discord channel ID: `discord.channel_id`
- Enable auto-trading: set `trading.auto_trade: true`
- Enable option vehicle execution: set `trading.options_enabled: true`
- Force paper trading: set `trading.paper_trade: true`
- Switch AI provider: set `ai.provider: openai` (or `anthropic`, `google`, `none`, `auto`)
- Set a different AI model: change `ai.openai.model` / `ai.anthropic.model`
- Adjust confidence threshold: `trading.min_confidence`

## 2) AI prompt
Edit `config/ai_parser.prompt`.

Placeholders:
- `{{AUTHOR_NAME}}`
- `{{MESSAGE_TEXT}}`

These will be replaced automatically at runtime.

## 3) Optional override path
If you want to store the config elsewhere, set:

```
CONFIG_PATH=/full/path/to/config/trading.yaml
```

in `.env` (or your environment).

You can also override runtime output paths:

```
DATA_DIR=data
PICKS_LOG_PATH=data/picks_log.jsonl
```

Relative paths resolve from the repository root.

## Notes
- If `config/trading.yaml` is missing, the app falls back to `.env` and defaults.
- Keep secrets out of this folder if you plan to share the repo.
