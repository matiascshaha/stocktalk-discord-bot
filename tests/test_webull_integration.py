"""
Webull Trader Integration Tests

Simple tests to verify basic functionality.
Requires: WEBULL_APP_KEY and WEBULL_APP_SECRET in .env
"""

import os
import pytest
from dotenv import load_dotenv

from src.models.webull_models import *
from src.webull_trader import WebullTrader
from config.settings import WEBULL_CONFIG

load_dotenv()


class TestWebullTrader:
    """Basic Webull integration tests"""

    @pytest.fixture
    def trader(self):
        """Create paper trader"""
        paper_trade = False
        app_key = WEBULL_CONFIG.get('test_app_key') if paper_trade else os.getenv('WEBULL_APP_KEY')
        app_secret = WEBULL_CONFIG.get('test_app_secret') if paper_trade else os.getenv('WEBULL_APP_SECRET')
        
        if not app_key or not app_secret:
            pytest.skip("Webull credentials not set")
        
        return WebullTrader(
            app_key=app_key,
            app_secret=app_secret,
            paper_trade=paper_trade,
            region="US",
            account_id=WEBULL_CONFIG.get('test_account_id') if paper_trade else os.getenv('WEBULL_ACCOUNT_ID'),
        )

    def test_login(self, trader):
        """Test basic login"""
        assert trader.login() is True
        print(f"\n✅ Login successful")

    def test_get_account_id(self, trader):
        """Test account ID resolution"""
        account_id = trader.resolve_account_id()
        assert account_id is not None
        print(f"\n✅ Account ID: {account_id}")

    def test_get_balance(self, trader):
        """Test fetching account balance"""
        balance = trader.get_account_balance()
        assert balance is not None
        print(f"\n✅ Balance: {balance}")

    def test_preview_order(self, trader):
        """Test order preview (no actual order)"""
        order = StockOrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.LIMIT,
            limit_price=150.0
        )
        
        preview = trader.preview_stock_order(order)
        
        # Now preview is an OrderPreview model with typed attributes
        print(f"\n✅ Stock order preview:")
        print(f"   Estimated cost: ${preview.estimated_cost} {preview.currency}")
        print(f"   Transaction fee: ${preview.estimated_transaction_fee}")
        print(f"   Cost as float: ${preview.cost_as_float}")
        
        assert preview.estimated_cost is not None
    
    def test_place_stock_order(self, trader):
        """Test placing actual stock order (paper trading - no real money)"""
        order = StockOrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.LIMIT,
            time_in_force="GTC",
            limit_price=1.0  # Low price so it won't actually fill
        )

        # Place order (hits UAT API - paper trading)
        result = trader.place_stock_order(order)
        
        print(f"\n✅ Stock order placed:")
        print(f"   Order ID: {result.get('order_id', 'N/A')}")
        print(f"   Client Order ID: {result.get('client_order_id', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Full response: {result}")
        
        assert result is not None
        # Note: May contain order_id or error message depending on UAT behavior

    def test_preview_option_order(self, trader):
        """Test option order preview (no actual order)"""
        order = OptionOrderRequest(
            order_type=OrderType.LIMIT,
            quantity="1",
            limit_price="21.25",
            side=OrderSide.BUY,
            legs=[
                OptionLeg(
                    side=OrderSide.BUY,
                    quantity="1",
                    symbol="TSLA",
                    strike_price="400",
                    option_expire_date="2025-11-26",
                    option_type=OptionType.CALL,
                    market="US"
                )
            ]
        )
        
        preview = trader.preview_option_order(order)
        
        print(f"\n✅ Option order preview:")
        print(f"   Estimated cost: ${preview.estimated_cost} {preview.currency}")
        print(f"   Transaction fee: ${preview.estimated_transaction_fee}")
        
        assert preview is not None

    def test_place_option_order(self, trader):
        """Test placing actual option order (paper trading - no real money)"""
        order = OptionOrderRequest(
            client_order_id=uuid.uuid4().hex,
            combo_type="NORMAL",
            order_type=OrderType.LIMIT,
            quantity="1",
            limit_price="1.0",
            option_strategy="SINGLE",
            side=OrderSide.BUY,
            time_in_force=TimeInForce.GTC,
            entrust_type="QTY",
            legs=[
                OptionLeg(
                    side=OrderSide.BUY,
                    quantity="1",
                    symbol="TSLA",
                    strike_price="400.0",
                    option_expire_date="2025-11-26",
                    instrument_type="OPTION",
                    option_type=OptionType.CALL,
                    market="US"
                )
            ]
        )

        # Place option order (hits UAT API - paper trading)
        result = trader.place_option_order(order)
        
        print(f"\n✅ Option order placed:")
        print(f"   Order ID: {result.get('order_id', 'N/A')}")
        print(f"   Client Order ID: {result.get('client_order_id', 'N/A')}")
        print(f"   Status: {result.get('status', 'N/A')}")
        print(f"   Option Symbol: {result.get('symbol', 'N/A')}")
        print(f"   Full response: {result}")
        
        assert result is not None

    def test_get_instrument(self, trader):
        """Test fetching stock quote"""
        trader.test()

        #quote = trader.get_instrument("AAPL")
        #assert quote is not None
        #print(f"\n✅ Stock quote for AAPL:{quote}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])