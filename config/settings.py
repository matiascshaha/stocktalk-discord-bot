import json
import os
from pathlib import Path
from typing import Any, Optional, Dict

from dotenv import load_dotenv

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None

load_dotenv()

CONFIG_DATA = {}


def _load_config() -> dict:
    path = Path(_config_path())
    if not path.exists():
        return {}

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}

    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        if not yaml:
            return {}
        try:
            data = yaml.safe_load(text) or {}
        except Exception:
            return {}
    elif suffix == ".json":
        try:
            data = json.loads(text) or {}
        except Exception:
            return {}
    else:
        return {}

    return data if isinstance(data, dict) else {}


def _config_path() -> str:
    env_override = os.getenv("CONFIG_PATH")
    if env_override:
        return str(Path(env_override).expanduser())
    return str(Path.cwd() / "config" / "trading.yaml")


def _cfg(path: str, default: Optional[Any] = None) -> Any:
    current: Any = CONFIG_DATA
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    if current is None:
        return default
    if isinstance(current, str) and current.strip() == "":
        return default
    return current


CONFIG_DATA = _load_config()


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on"}
    return bool(value)


def _as_float(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = _as_int(_cfg('discord.channel_id', os.getenv('CHANNEL_ID')))

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Google Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# AI Configuration (non-secret)
AI_PROVIDER = _cfg('ai.provider', os.getenv('AI_PROVIDER'))
AI_CONFIG = {
    'provider': AI_PROVIDER,
    'fallback_to_available_provider': _as_bool(
        _cfg('ai.fallback_to_available_provider', os.getenv('AI_FALLBACK_TO_AVAILABLE_PROVIDER', 'true')),
        True,
    ),
    'prompt_file': _cfg('ai.prompt.file', os.getenv('AI_PROMPT_FILE', 'config/ai_parser.prompt')),
    'openai': {
        'model': _cfg('ai.openai.model', os.getenv('OPENAI_MODEL', 'gpt-4o')),
        'max_tokens': _as_int(_cfg('ai.openai.max_tokens', os.getenv('OPENAI_MAX_TOKENS')), 2000),
        'temperature': _as_float(_cfg('ai.openai.temperature', os.getenv('OPENAI_TEMPERATURE')), 0.2),
    },
    'anthropic': {
        'model': _cfg('ai.anthropic.model', os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5')),
        'max_tokens': _as_int(_cfg('ai.anthropic.max_tokens', os.getenv('ANTHROPIC_MAX_TOKENS')), 2000),
        'temperature': _as_float(_cfg('ai.anthropic.temperature', os.getenv('ANTHROPIC_TEMPERATURE')), 0.2),
    },
    'google': {
        'model': _cfg('ai.google.model', os.getenv('GOOGLE_MODEL', 'gemini-3-pro-preview')),
        'temperature': _as_float(_cfg('ai.google.temperature', os.getenv('GOOGLE_TEMPERATURE')), 0.2),
    },
}

# Webull Configuration (OpenAPI)
WEBULL_CONFIG = {
    'app_key': os.getenv('WEBULL_APP_KEY'),
    'app_secret': os.getenv('WEBULL_APP_SECRET'),
    'test_app_key': _cfg('webull.test_app_key'),
    'test_app_secret': _cfg('webull.test_app_secret'),
    'region': _cfg('webull.region', os.getenv('WEBULL_REGION', 'US')),
    'api_endpoint': _cfg('webull.api_endpoint', os.getenv('WEBULL_API_ENDPOINT')),
    'account_id': _cfg('webull.account_id'),
    'test_account_id': _cfg('webull.test_account_id', os.getenv('WEBULL_TEST_ACCOUNT_ID')),
    'currency': _cfg('webull.currency', os.getenv('WEBULL_CURRENCY', 'USD')),
    'account_tax_type': _cfg('webull.account_tax_type', os.getenv('WEBULL_ACCOUNT_TAX_TYPE', 'GENERAL')),
}

# Trading Settings
TRADING_CONFIG = {
    'auto_trade': _as_bool(_cfg('trading.auto_trade', os.getenv('AUTO_TRADE', 'false')), False),
    'paper_trade': _as_bool(_cfg('trading.paper_trade', os.getenv('PAPER_TRADE', 'False')), False),
    'min_confidence': _as_float(_cfg('trading.min_confidence', os.getenv('MIN_CONFIDENCE', 0.7)), 0.7),
    'default_amount': _as_float(_cfg('trading.default_amount', os.getenv('DEFAULT_AMOUNT', 1000)), 1000.0),
    'use_market_orders': _as_bool(_cfg('trading.use_market_orders', os.getenv('USE_MARKET_ORDERS', 'true')), True),
    'extended_hours_trading': _as_bool(_cfg('trading.extended_hours_trading', os.getenv('EXTENDED_HOURS_TRADING', 'false')), False),
    'time_in_force': _cfg('trading.time_in_force', os.getenv('TIME_IN_FORCE', 'DAY')),
}

# Notification Settings
NOTIFICATION_CONFIG = {
    'desktop_notifications': _as_bool(_cfg('notifications.desktop_notifications', os.getenv('DESKTOP_NOTIFICATIONS', 'true')), True),
    'sound_alert': _as_bool(_cfg('notifications.sound_alert', os.getenv('SOUND_ALERT', 'true')), True),
    'copy_to_clipboard': _as_bool(_cfg('notifications.copy_to_clipboard', os.getenv('COPY_TO_CLIPBOARD', 'true')), True),
}

# Validate required settings
def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not DISCORD_TOKEN:
        errors.append("DISCORD_TOKEN is required")
    
    if not CHANNEL_ID:
        errors.append("CHANNEL_ID is required")
    
    provider = (AI_PROVIDER or '').lower()
    if provider in ('', 'auto'):
        if not ANTHROPIC_API_KEY and not OPENAI_API_KEY and not GOOGLE_API_KEY:
            if not ANTHROPIC_API_KEY:
                errors.append("ANTHROPIC_API_KEY is required")
            if not OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY is required")
            if not GOOGLE_API_KEY:
                errors.append("GOOGLE_API_KEY is required")
    elif provider == 'openai':
        if not OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when AI_PROVIDER=openai")
    elif provider == 'anthropic':
        if not ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required when AI_PROVIDER=anthropic")
    elif provider == 'google':
        if not GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is required when AI_PROVIDER=google")
    elif provider == 'none':
        pass
    else:
        errors.append(f"AI_PROVIDER '{AI_PROVIDER}' is invalid (use openai, anthropic, google, none, auto)")
    
    if TRADING_CONFIG['auto_trade']:
        if not WEBULL_CONFIG['app_key']:
            errors.append("WEBULL_APP_KEY is required when AUTO_TRADE is enabled")
        if not WEBULL_CONFIG['app_secret']:
            errors.append("WEBULL_APP_SECRET is required when AUTO_TRADE is enabled")
    
    return errors


def get_account_constraints() -> str:
    """
    Get natural language account constraints from config.
    These constraints are passed to the AI parser to enforce rules automatically.
    
    Returns:
        str: Natural language constraints string
    """
    constraints = _cfg('account_constraints', '')
    if isinstance(constraints, str):
        return constraints.strip()
    return ''


def get_analyst_for_channel(channel_id: int) -> Optional[Dict[str, Any]]:
    """
    Get analyst profile for a given Discord channel ID.
    
    Args:
        channel_id: Discord channel ID (int or str)
    
    Returns:
        Dict with analyst config (name, multipliers, preferences) or None if not configured
    """
    channel_str = str(channel_id)
    analyst_channels = _cfg('analyst_channels', {})
    
    if not isinstance(analyst_channels, dict):
        return None
    
    return analyst_channels.get(channel_str)
