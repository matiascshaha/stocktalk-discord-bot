import json
import logging
import os
from typing import Any, Optional, Dict

from dotenv import load_dotenv

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None

load_dotenv()

from src.utils.paths import resolve_config_path


logger = logging.getLogger(__name__)
CONFIG_DATA = {}


def _load_config() -> dict:
    path = resolve_config_path()
    logger.info("Loading configuration from %s", path)

    if not path.exists():
        logger.warning("Configuration file not found at %s", path)
        return {}

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Failed reading configuration file %s: %s", path, exc)
        return {}

    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        if not yaml:
            logger.warning("PyYAML is unavailable; cannot parse %s", path)
            return {}
        try:
            data = yaml.safe_load(text) or {}
        except Exception as exc:
            logger.warning("Failed parsing YAML configuration %s: %s", path, exc)
            return {}
    elif suffix == ".json":
        try:
            data = json.loads(text) or {}
        except Exception as exc:
            logger.warning("Failed parsing JSON configuration %s: %s", path, exc)
            return {}
    else:
        logger.warning("Unsupported configuration extension for %s", path)
        return {}

    return data if isinstance(data, dict) else {}


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
CHANNEL_ID = _as_int(_cfg('discord.channel_id'), None)

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Google Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# AI Configuration (non-secret)
AI_PROVIDER = _cfg('ai.provider', 'auto')
AI_CONFIG = {
    'provider': AI_PROVIDER,
    'fallback_to_available_provider': _as_bool(
        _cfg('ai.fallback_to_available_provider', True),
        True,
    ),
    'prompt_file': _cfg('ai.prompt.file', 'config/ai_parser.prompt'),
    'openai': {
        'model': _cfg('ai.openai.model', 'gpt-4o'),
        'max_tokens': _as_int(_cfg('ai.openai.max_tokens', 2000), 2000),
        'temperature': _as_float(_cfg('ai.openai.temperature', 0.2), 0.2),
    },
    'anthropic': {
        'model': _cfg('ai.anthropic.model', 'claude-sonnet-4-5'),
        'max_tokens': _as_int(_cfg('ai.anthropic.max_tokens', 2000), 2000),
        'temperature': _as_float(_cfg('ai.anthropic.temperature', 0.2), 0.2),
    },
    'google': {
        'model': _cfg('ai.google.model', 'gemini-3-pro-preview'),
        'temperature': _as_float(_cfg('ai.google.temperature', 0.2), 0.2),
    },
}

# Webull Configuration (OpenAPI)
WEBULL_CONFIG = {
    'app_key': os.getenv('WEBULL_APP_KEY'),
    'app_secret': os.getenv('WEBULL_APP_SECRET'),
    'test_app_key': _cfg('webull.test_app_key'),
    'test_app_secret': _cfg('webull.test_app_secret'),
    'region': _cfg('webull.region', 'US'),
    'api_endpoint': _cfg('webull.api_endpoint'),
    # account IDs are credential-like and may live in env when users prefer
    'account_id': _cfg('webull.account_id', os.getenv('WEBULL_ACCOUNT_ID')),
    'test_account_id': _cfg('webull.test_account_id', os.getenv('WEBULL_TEST_ACCOUNT_ID')),
    'currency': _cfg('webull.currency', 'USD'),
    'account_tax_type': _cfg('webull.account_tax_type', 'GENERAL'),
}

# Trading Settings
TRADING_CONFIG = {
    'auto_trade': _as_bool(_cfg('trading.auto_trade', False), False),
    'paper_trade': _as_bool(_cfg('trading.paper_trade', False), False),
    'options_enabled': _as_bool(_cfg('trading.options_enabled', False), False),
    'min_confidence': _as_float(_cfg('trading.min_confidence', 0.7), 0.7),
    'default_amount': _as_float(_cfg('trading.default_amount', 1000), 1000.0),
    'use_market_orders': _as_bool(_cfg('trading.use_market_orders', True), True),
    'extended_hours_trading': _as_bool(_cfg('trading.extended_hours_trading', False), False),
    'time_in_force': _cfg('trading.time_in_force', 'DAY'),
    'queue_when_closed': _as_bool(_cfg('trading.queue_when_closed', True), True),
    'queue_time_in_force': _cfg('trading.queue_time_in_force', 'GTC'),
    'out_of_hours_limit_buffer_bps': _as_float(_cfg('trading.out_of_hours_limit_buffer_bps', 50.0), 50.0),
}

# Notification Settings
NOTIFICATION_CONFIG = {
    'desktop_notifications': _as_bool(_cfg('notifications.desktop_notifications', True), True),
    'sound_alert': _as_bool(_cfg('notifications.sound_alert', True), True),
    'copy_to_clipboard': _as_bool(_cfg('notifications.copy_to_clipboard', True), True),
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
