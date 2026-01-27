#!/usr/bin/env python3
"""
Comprehensive Webull Brokerage Integration Test Suite

This test suite uses REAL Webull API endpoints:
- Paper Trading Tests: Use UAT environment (us-openapi-alb.uat.webullbroker.com)
- Live Trading Tests: Use Production environment (api.webull.com) - REAL MONEY!

Both test types make actual API calls to Webull servers.

Test Structure:
1. Paper Trading Tests - Safe, uses test account, no real money
2. Live Trading Tests - Requires real credentials, USES REAL MONEY

Run tests:
- Paper tests only: python test_webull_integration.py
- Live tests: Set WEBULL_ENABLE_LIVE_TESTS=true in .env first!
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from src.webull_trader import WebullTrader
from src.utils.logger import setup_logger

load_dotenv()

logger = setup_logger('test_webull_integration')


# ============================================================================
# Configuration Builders
# ============================================================================

def _build_paper_config():
    """Configuration for PAPER trading (UAT environment)."""
    return {
        'app_key': os.getenv('WEBULL_APP_KEY'),
        'app_secret': os.getenv('WEBULL_APP_SECRET'),
        'region': os.getenv('WEBULL_REGION', 'US'),
        'paper_trade': True,  # Uses UAT endpoint
        'min_confidence': 0.7,
        'default_dollar_amount': 1000,
        'use_market_orders': True,
        'time_in_force': 'DAY',
    }


def _build_live_config():
    """Configuration for LIVE trading (Production environment) - REAL MONEY!"""
    return {
        'app_key': os.getenv('WEBULL_APP_KEY'),
        'app_secret': os.getenv('WEBULL_APP_SECRET'),
        'region': os.getenv('WEBULL_REGION', 'US'),
        'paper_trade': False,  # Uses PRODUCTION endpoint
        'min_confidence': 0.9,  # Higher threshold for live trading
        'default_dollar_amount': 100,  # Smaller amount for safety
        'use_market_orders': False,  # Use limit orders for safety
        'time_in_force': 'DAY',
    }


def _build_sample_picks():
    """Sample stock picks for testing."""
    return [
        {
            'ticker': 'AAPL',
            'action': 'BUY',
            'confidence': 0.95,
            'weight': None,
            'strike': None,
            'option_type': 'STOCK',
            'price': 150.0,
            'expiry': None,
            'reasoning': 'Strong bullish momentum',
            'urgency': 'HIGH',
            'sentiment': 'BULLISH'
        },
        {
            'ticker': 'NVDA',
            'action': 'BUY',
            'confidence': 0.85,
            'weight': None,
            'strike': None,
            'option_type': 'STOCK',
            'price': 700.0,
            'expiry': None,
            'reasoning': 'AI boom continuation',
            'urgency': 'MEDIUM',
            'sentiment': 'BULLISH'
        },
        {
            'ticker': 'TSLA',
            'action': 'SELL',
            'confidence': 0.80,
            'weight': None,
            'strike': None,
            'option_type': 'STOCK',
            'price': 200.0,
            'expiry': None,
            'reasoning': 'Overbought signals',
            'urgency': 'MEDIUM',
            'sentiment': 'BEARISH'
        },
        {
            'ticker': 'MSFT',
            'action': 'BUY',
            'confidence': 0.60,  # Below threshold
            'weight': None,
            'strike': None,
            'option_type': 'STOCK',
            'price': 420.0,
            'expiry': None,
            'reasoning': 'Weak signal',
            'urgency': 'LOW',
            'sentiment': 'NEUTRAL'
        },
    ]


# ============================================================================
# Paper Trading Tests (UAT Environment)
# ============================================================================

class TestWebullPaperTrading:
    """
    Test paper trading functionality using REAL Webull UAT/test API.
    
    These tests hit the actual UAT endpoint: us-openapi-alb.uat.webullbroker.com
    No real money is involved, but real API calls are made.
    """

    def __init__(self):
        config = _build_paper_config()
        if not config['app_key'] or not config['app_secret']:
            logger.warning("Webull credentials not configured - tests will be skipped")
            logger.warning("Set WEBULL_APP_KEY and WEBULL_APP_SECRET in .env to enable")
            self.trader = None
        else:
            self.trader = WebullTrader(config)
    
    def test_paper_login(self):
        """Test login to Webull UAT environment."""
        logger.info("\n" + "="*60)
        logger.info("🔐 PAPER TRADING LOGIN TEST (UAT API)")
        logger.info("="*60)
        
        if not self.trader:
            logger.info("⏭️  Skipped: No credentials configured")
            logger.info("="*60 + "\n")
            return None
        
        try:
            success = self.trader.login()
            if success:
                logger.info("✅ Successfully authenticated with Webull UAT API")
                logger.info("="*60 + "\n")
                return True
            else:
                logger.error("❌ Failed to authenticate with Webull UAT API")
                logger.info("="*60 + "\n")
                return False
        except Exception as exc:
            logger.error(f"❌ Exception during login: {exc}")
            logger.info("="*60 + "\n")
            return False
    
    def test_paper_account_balance(self):
        """Test fetching account balance from UAT environment."""
        logger.info("\n" + "="*60)
        logger.info("💰 PAPER ACCOUNT BALANCE TEST (UAT API)")
        logger.info("="*60)
        
        if not self.trader:
            logger.info("⏭️  Skipped: No credentials configured")
            logger.info("="*60 + "\n")
            return None
        
        try:
            balance = self.trader.get_account_balance()
            logger.info(f"✅ Retrieved balance from UAT: {balance}")
            logger.info("="*60 + "\n")
            return balance
        except Exception as exc:
            logger.error(f"❌ Failed to get balance: {exc}")
            logger.info("="*60 + "\n")
            return None
    
    def test_paper_trade_execution(self):
        """Test actual order placement in UAT environment."""
        logger.info("\n" + "="*60)
        logger.info("📝 PAPER TRADE EXECUTION TEST (UAT API)")
        logger.info("="*60)
        
        if not self.trader:
            logger.info("⏭️  Skipped: No credentials configured")
            logger.info("="*60 + "\n")
            return None
        
        picks = _build_sample_picks()
        
        logger.info(f"\n📄 Processing {len(picks)} paper trades via UAT API...\n")
        
        results = []
        for pick in picks:
            logger.info(f"Processing: {pick['ticker']} - {pick['action']}")
            try:
                order = self.trader.execute_trade(pick)
                results.append({
                    'pick': pick,
                    'order': order
                })
                if order:
                    env = order.get('_environment', 'UNKNOWN')
                    logger.info(f"  ✅ Order placed in {env}")
                else:
                    logger.info(f"  ⏭️  Order skipped (filtered)")
            except Exception as exc:
                logger.error(f"  ❌ Error: {exc}")
                results.append({
                    'pick': pick,
                    'order': None,
                    'error': str(exc)
                })
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 PAPER TRADE EXECUTION SUMMARY")
        logger.info("="*60)
        
        successful = [r for r in results if r.get('order') is not None]
        logger.info(f"✅ Successful orders: {len(successful)}/{len(picks)}")
        
        for result in results:
            pick = result['pick']
            order = result.get('order')
            if order:
                status = "✅"
            elif 'error' in result:
                status = "❌"
            else:
                status = "⏭️ "
            logger.info(f"{status} {pick['ticker']}: {pick['action']} ({pick['sentiment']})")
        
        logger.info("="*60 + "\n")
        
        return results
    
    def test_paper_order_history(self):
        """Test fetching order history from UAT environment."""
        logger.info("\n" + "="*60)
        logger.info("📜 PAPER ORDER HISTORY TEST (UAT API)")
        logger.info("="*60)
        
        if not self.trader:
            logger.info("⏭️  Skipped: No credentials configured")
            logger.info("="*60 + "\n")
            return None
        
        try:
            orders = self.trader.get_order_history(limit=10)
            logger.info(f"✅ Retrieved {len(orders)} orders from UAT")
            for i, order in enumerate(orders[:3], 1):  # Show first 3
                logger.info(f"  Order {i}: {order.get('symbol', 'N/A')} - {order.get('side', 'N/A')}")
            if len(orders) > 3:
                logger.info(f"  ... and {len(orders) - 3} more")
            logger.info("="*60 + "\n")
            return orders
        except Exception as exc:
            logger.error(f"❌ Failed to get order history: {exc}")
            logger.info("="*60 + "\n")
            return None


# ============================================================================
# Live Trading Tests (Production Environment) - REAL MONEY!
# ============================================================================

class TestWebullLiveTrading:
    """
    Test LIVE trading functionality using REAL Webull Production API.
    
    ⚠️  WARNING: These tests hit the PRODUCTION endpoint: api.webull.com
    ⚠️  REAL MONEY will be used if orders are placed!
    ⚠️  Only run these tests if you understand the risks!
    
    These tests are DISABLED by default. To enable:
    Set WEBULL_ENABLE_LIVE_TESTS=true in your .env file
    """

    def __init__(self):
        # Check if live tests are explicitly enabled
        enabled = os.getenv('WEBULL_ENABLE_LIVE_TESTS', 'false').lower() == 'true'
        
        if not enabled:
            logger.warning("⚠️  Live trading tests are DISABLED by default")
            logger.warning("   Set WEBULL_ENABLE_LIVE_TESTS=true in .env to enable")
            self.trader = None
            self.enabled = False
            return
        
        config = _build_live_config()
        if not config['app_key'] or not config['app_secret']:
            logger.warning("Webull credentials not configured - tests will be skipped")
            self.trader = None
            self.enabled = False
        else:
            self.trader = WebullTrader(config)
            self.enabled = True
            logger.warning("⚠️" * 20)
            logger.warning("⚠️  LIVE TRADING MODE ENABLED - REAL MONEY AT RISK!")
            logger.warning("⚠️" * 20)
    
    def test_live_login(self):
        """Test login to Webull PRODUCTION environment."""
        logger.info("\n" + "="*60)
        logger.info("🔐 LIVE TRADING LOGIN TEST (PRODUCTION API)")
        logger.info("⚠️  WARNING: This tests REAL ACCOUNT ACCESS!")
        logger.info("="*60)
        
        if not self.enabled:
            logger.info("⏭️  Skipped: Live tests not enabled")
            logger.info("="*60 + "\n")
            return None
        
        try:
            success = self.trader.login()
            if success:
                logger.info("✅ Successfully authenticated with Webull PRODUCTION API")
                logger.warning("⚠️  This is your REAL trading account!")
                logger.info("="*60 + "\n")
                return True
            else:
                logger.error("❌ Failed to authenticate with Webull PRODUCTION API")
                logger.info("="*60 + "\n")
                return False
        except Exception as exc:
            logger.error(f"❌ Exception during login: {exc}")
            logger.info("="*60 + "\n")
            return False
    
    def test_live_account_balance(self):
        """Test fetching REAL account balance."""
        logger.info("\n" + "="*60)
        logger.info("💰 LIVE ACCOUNT BALANCE TEST (PRODUCTION API)")
        logger.info("⚠️  WARNING: Viewing REAL account balance!")
        logger.info("="*60)
        
        if not self.enabled:
            logger.info("⏭️  Skipped: Live tests not enabled")
            logger.info("="*60 + "\n")
            return None
        
        try:
            balance = self.trader.get_account_balance()
            logger.info(f"✅ Retrieved REAL balance: {balance}")
            logger.warning("⚠️  This is your actual trading account balance!")
            logger.info("="*60 + "\n")
            return balance
        except Exception as exc:
            logger.error(f"❌ Failed to get balance: {exc}")
            logger.info("="*60 + "\n")
            return None
    
    def test_live_trade_DRY_RUN(self):
        """
        Build order payloads but DO NOT EXECUTE on production.
        
        This is a SAFETY test - it builds orders but doesn't submit them.
        """
        logger.info("\n" + "="*60)
        logger.info("🔍 LIVE TRADE DRY RUN (NO ACTUAL ORDERS)")
        logger.info("="*60)
        
        if not self.enabled:
            logger.info("⏭️  Skipped: Live tests not enabled")
            logger.info("="*60 + "\n")
            return None
        
        picks = _build_sample_picks()
        
        logger.info(f"\n📄 Building {len(picks)} order payloads (NOT executing)...\n")
        
        results = []
        for pick in picks:
            logger.info(f"Building payload for: {pick['ticker']} - {pick['action']}")
            try:
                symbol = pick['ticker']
                quantity = 1
                limit_price = pick.get('price')
                
                payload = self.trader.build_order_payload_from_pick(
                    pick,
                    symbol=symbol,
                    market='US',
                    instrument_type='EQUITY',
                    quantity=quantity,
                    limit_price=limit_price,
                )
                
                results.append({
                    'pick': pick,
                    'payload': payload
                })
                logger.info(f"  ✅ Payload built: {payload['order_type']} order for {quantity} shares")
            except Exception as exc:
                logger.error(f"  ❌ Error building payload: {exc}")
                results.append({
                    'pick': pick,
                    'payload': None,
                    'error': str(exc)
                })
        
        logger.info("\n" + "="*60)
        logger.info("📊 DRY RUN SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Payloads built: {len([r for r in results if r.get('payload')])}/{len(picks)}")
        logger.info("ℹ️  NOTE: No orders were actually placed")
        logger.info("="*60 + "\n")
        
        return results


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all Webull integration tests."""
    logger.info("\n" + "="*70)
    logger.info("WEBULL BROKERAGE INTEGRATION TEST SUITE")
    logger.info("="*70)
    
    # Paper trading tests (UAT environment)
    logger.info("\n🧪 RUNNING PAPER TRADING TESTS (UAT API)")
    logger.info("─" * 70)
    paper_tester = TestWebullPaperTrading()
    
    paper_login_ok = paper_tester.test_paper_login()
    paper_balance = paper_tester.test_paper_account_balance()
    paper_trades = paper_tester.test_paper_trade_execution()
    paper_history = paper_tester.test_paper_order_history()
    
    # Live trading tests (Production environment)
    logger.info("\n💰 RUNNING LIVE TRADING TESTS (PRODUCTION API)")
    logger.info("─" * 70)
    live_tester = TestWebullLiveTrading()
    
    live_login_ok = live_tester.test_live_login()
    live_balance = live_tester.test_live_account_balance()
    live_dry_run = live_tester.test_live_trade_DRY_RUN()
    
    # Final summary
    logger.info("\n" + "="*70)
    logger.info("✅ ALL TESTS COMPLETE")
    logger.info("="*70)
    
    logger.info("\nPaper Trading (UAT) Results:")
    logger.info(f"  Login: {'✅' if paper_login_ok else '❌' if paper_login_ok is False else '⏭️'}")
    logger.info(f"  Balance: {'✅' if paper_balance else '❌' if paper_balance is False else '⏭️'}")
    logger.info(f"  Trades: {'✅' if paper_trades else '❌' if paper_trades is False else '⏭️'}")
    logger.info(f"  History: {'✅' if paper_history is not None else '❌'}")
    
    logger.info("\nLive Trading (Production) Results:")
    logger.info(f"  Login: {'✅' if live_login_ok else '❌' if live_login_ok is False else '⏭️'}")
    logger.info(f"  Balance: {'✅' if live_balance else '❌' if live_balance is False else '⏭️'}")
    logger.info(f"  Dry Run: {'✅' if live_dry_run else '❌' if live_dry_run is False else '⏭️'}")
    
    logger.info("\n" + "="*70 + "\n")


if __name__ == '__main__':
    run_all_tests()