#!/usr/bin/env python3
"""
Main entry point for Discord Stock Monitor
"""

import sys
import os
import asyncio

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
    if TRADING_CONFIG['auto_trade']:
        logger.info("Initializing Webull trader.")
        trader = WebullTrader(WEBULL_CONFIG, TRADING_CONFIG)

        if trader.login():
            logger.info("Webull trader ready.")
        else:
            logger.warning("Webull login failed; continuing in monitor-only mode.")
            trader = None
    else:
        logger.info("Auto-trading disabled; running in monitor-only mode.")
    
    # Initialize and run Discord client
    logger.info("Starting Discord monitor.")
    client = StockMonitorClient(trader=trader)
    
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
