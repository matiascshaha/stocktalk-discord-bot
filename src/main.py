#!/usr/bin/env python3
"""
Main entry point for Discord Stock Monitor
"""

import sys
import os

from src.brokerages.factory import build_brokerage
from src.discord_client import StockMonitorClient
from src.webull_trader import WebullTrader
from config.settings import (
    validate_config,
    TRADING_CONFIG,
    WEBULL_CONFIG
)
from src.utils.logger import setup_logger
from src.utils.logging_format import format_mode_summary

logger = setup_logger('main')

def print_banner():
    """Print application banner"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   AI-Powered Discord Stock Monitor + Webull Trading      ║
    ║   Powered by Claude AI for intelligent message parsing   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

def main():
    """Main application entry point"""
    print_banner()
    
    # Validate configuration
    logger.info("Validating configuration.")
    config_errors = validate_config()
    
    if config_errors:
        logger.error("Configuration errors found:")
        for error in config_errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease check your .env file and try again.")
        sys.exit(1)
    
    logger.info("Configuration valid.")
    logger.info(format_mode_summary(TRADING_CONFIG))
    
    # Initialize Webull trader if auto-trading enabled
    trader = None
    broker = None
    if TRADING_CONFIG['auto_trade']:
        paper_trade = TRADING_CONFIG['paper_trade']
        app_key = WEBULL_CONFIG.get('test_app_key') if paper_trade else os.getenv('WEBULL_APP_KEY')
        app_secret = WEBULL_CONFIG.get('test_app_secret') if paper_trade else os.getenv('WEBULL_APP_SECRET')
        account_id = WEBULL_CONFIG.get('test_account_id') if paper_trade else os.getenv('WEBULL_ACCOUNT_ID')
        logger.info("Initializing Webull trader.")
        trader = WebullTrader(
            app_key=app_key,
            app_secret=app_secret,
            paper_trade=paper_trade,
            region="US",
            account_id=account_id
        )

        if trader.login():
            logger.info("Webull trader ready.")
            broker = build_brokerage(TRADING_CONFIG.get("broker", "webull"), trader)
        else:
            logger.warning("Webull login failed; continuing in monitor-only mode.")
            trader = None
    else:
        logger.info("Auto-trading disabled; running in monitor-only mode.")
    
    # Initialize and run Discord client
    logger.info("Starting Discord monitor.")
    client = StockMonitorClient(trader=trader, broker=broker)
    
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
