#!/usr/bin/env python3
"""
Main entry point for Discord Stock Monitor
"""

import sys

from src.brokerages import create_broker_runtime
from src.discord_client import StockMonitorClient
from config.settings import (
    PUBLIC_CONFIG,
    validate_config,
    TRADING_CONFIG,
    WEBULL_CONFIG,
)
from src.utils.logger import setup_logger
from src.utils.logging_format import format_mode_summary

logger = setup_logger('main')

def print_banner():
    """Print application banner"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║   AI-Powered Discord Stock Monitor + Broker Trading      ║
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
    
    broker_runtime = None
    if TRADING_CONFIG['auto_trade']:
        try:
            broker_runtime = create_broker_runtime(
                trading_config=TRADING_CONFIG,
                webull_config=WEBULL_CONFIG,
                public_config=PUBLIC_CONFIG,
            )
        except Exception as exc:
            logger.error("Failed to initialize broker runtime: %s", exc)
            sys.exit(1)
    if broker_runtime is None:
        logger.info("No active broker runtime; running in monitor-only mode.")
    
    # Initialize and run Discord client
    logger.info("Starting Discord monitor.")
    client = StockMonitorClient(
        broker=broker_runtime.broker if broker_runtime else None,
        trading_account=broker_runtime.trading_account if broker_runtime else None,
    )
    
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
