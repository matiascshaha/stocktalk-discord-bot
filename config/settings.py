import os
from dotenv import load_dotenv

load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Webull Configuration
WEBULL_CONFIG = {
    'username': os.getenv('WEBULL_USERNAME'),
    'password': os.getenv('WEBULL_PASSWORD'),
    'trading_pin': os.getenv('WEBULL_TRADING_PIN'),
    'device_name': os.getenv('WEBULL_DEVICE_NAME', 'stock_monitor'),
    'app_key': os.getenv('WEBULL_APP_KEY'),
    'app_secret': os.getenv('WEBULL_APP_SECRET'),
    'region': os.getenv('WEBULL_REGION', 'US'),
}

# Trading Settings
TRADING_CONFIG = {
    'auto_trade': os.getenv('AUTO_TRADE', 'false').lower() == 'true',
    'paper_trade': os.getenv('PAPER_TRADE', 'true').lower() == 'true',
    'min_confidence': float(os.getenv('MIN_CONFIDENCE', 0.7)),
    'default_amount': float(os.getenv('DEFAULT_AMOUNT', 1000)),
    'use_market_orders': os.getenv('USE_MARKET_ORDERS', 'true').lower() == 'true',
}

# Notification Settings
NOTIFICATION_CONFIG = {
    'desktop_notifications': os.getenv('DESKTOP_NOTIFICATIONS', 'true').lower() == 'true',
    'sound_alert': os.getenv('SOUND_ALERT', 'true').lower() == 'true',
    'copy_to_clipboard': os.getenv('COPY_TO_CLIPBOARD', 'true').lower() == 'true',
}

# Validate required settings
def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not DISCORD_TOKEN:
        errors.append("DISCORD_TOKEN is required")
    
    if not CHANNEL_ID:
        errors.append("CHANNEL_ID is required")
    
    if not ANTHROPIC_API_KEY and not OPENAI_API_KEY:
        if not ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required")
        if not OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
    
    if TRADING_CONFIG['auto_trade']:
        if not WEBULL_CONFIG['username']:
            errors.append("WEBULL_USERNAME is required when AUTO_TRADE is enabled")
        if not WEBULL_CONFIG['password']:
            errors.append("WEBULL_PASSWORD is required when AUTO_TRADE is enabled")
        if not WEBULL_CONFIG['trading_pin']:
            errors.append("WEBULL_TRADING_PIN is required when AUTO_TRADE is enabled")
    
    return errors
