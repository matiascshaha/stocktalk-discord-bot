"""
Production-Ready Webull OpenAPI Trading Integration

Simplified, clean, and maintainable implementation.
"""

import uuid
from typing import Any, Dict, Optional, List

from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient

from src.utils.logger import setup_logger
from src.models import *

from config.settings import WEBULL_CONFIG
logger = setup_logger("webull_trader")


class WebullTrader:
    """
    Simplified Webull OpenAPI trader.
    
    Example:
        trader = WebullTrader(
            app_key="key",
            app_secret="secret",
            paper_trade=True
        )
        
        order = StockOrderRequest(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.LIMIT,
            limit_price=150.0
        )
        
        preview = trader.preview_stock_order(order)
        if preview.valid:
            result = trader.place_stock_order(order)
    """

    ENDPOINTS = {
        'us': {'production': 'api.webull.com', 'uat': 'us-openapi-alb.uat.webullbroker.com'},
        'hk': {'production': 'api.webull.hk', 'uat': 'api.sandbox.webull.hk'},
        'jp': {'production': 'api.webull.co.jp', 'uat': 'jp-openapi-alb.uat.webullbroker.com'},
    }

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        region: str = "US",
        paper_trade: bool = True,
        account_id: Optional[str] = None,
    ):
        """Initialize trader"""
        self.app_key = app_key
        self.app_secret = app_secret
        self.region = region.lower()
        self.paper_trade = paper_trade
        self._account_id = account_id
        
        self._validate_config()
        self._init_api_client()

    def _validate_config(self):
        """Validate configuration"""
        if not self.app_key or not self.app_secret:
            raise ValueError("app_key and app_secret required")
        if self.region not in self.ENDPOINTS:
            raise ValueError(f"Invalid region: {self.region}")

    def _init_api_client(self):
        """Initialize API client"""
        endpoint = self._get_endpoint()
        env = "UAT/PAPER" if self.paper_trade else "PRODUCTION/LIVE"
        
        logger.info(f"Init Webull API: {env} mode, region: {self.region.upper()}, endpoint: {endpoint}")
        
        self.api_client = ApiClient(self.app_key, self.app_secret, self.region)
        self.api_client.add_endpoint(self.region, endpoint)
        self._account_id =  WEBULL_CONFIG.get('test_account_id') if self.paper_trade else self._account_id
        self.trade_client = TradeClient(self.api_client)

    def _get_endpoint(self) -> str:
        """Get API endpoint"""
        env_type = "uat" if self.paper_trade else "production"
        return self.ENDPOINTS[self.region][env_type]

    # ============================================================================
    # Account Management
    # ============================================================================

    def resolve_account_id(self) -> str:
        """Get account ID"""
        if self._account_id:
            logger.info(f"Using provided account ID: {self._mask_id(self._account_id)}")
            return self._account_id

        res = self.trade_client.account_v2.get_account_list()
        self._check_response(res, "get_account_list")
        
        data = res.json()
        accounts = self._extract_accounts(data)
        
        if not accounts:
            raise RuntimeError(f"No accounts found: {data}")

        account_id = accounts[0].get('account_id') or accounts[0].get('accountId')
        if not account_id:
            raise RuntimeError(f"No account_id in: {accounts[0]}")

        self._account_id = str(account_id)
        logger.info(f"Resolved account: {self._mask_id(self._account_id)}")
        return self._account_id

    def _extract_accounts(self, data: Any) -> List[Dict]:
        """Extract accounts list from various response formats"""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get('accounts') or data.get('data') or data.get('list', [])
        return []

    def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        account_id = self.resolve_account_id()
        res = self.trade_client.account_v2.get_account_balance(account_id)
        self._check_response(res, "get_account_balance")
        return res.json()

    def get_account_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        account_id = self.resolve_account_id()
        res = self.trade_client.account_v2.get_account_position(account_id)
        self._check_response(res, "get_account_position")
        return res.json()

    def login(self) -> bool:
        """Validate credentials"""
        try:
            self.resolve_account_id()
            env = "UAT/PAPER" if self.paper_trade else "PRODUCTION/LIVE"
            logger.info(f"Authenticated in {env} mode")
            return True
        except Exception as exc:
            logger.error(f"Login failed: {exc}")
            return False

    # ============================================================================
    # Order Preview
    # ============================================================================


    def preview_stock_order(self, order: StockOrderRequest) -> Dict[str, Any]:
        """
        Preview stock order using Webull's API.
        Returns raw response from Webull.
        """
        account_id = self.resolve_account_id()
        payload = self._build_stock_payload(order)
        
        logger.info(f"Previewing {order.side} {order.quantity} {order.symbol}...")
        
        res = self.trade_client.order_v2.preview_order(account_id, [payload])
        self._check_response(res, "preview_order")
        
        preview_data = res.json()
        logger.info(f"Preview response: {preview_data}")
        
        # Best practice: use model_validate
        return OrderPreviewResponse.model_validate(preview_data)

    def preview_option_order(self, order: OptionOrderRequest) -> OrderPreviewResponse:
        """Preview option order using Webull's preview_option API"""
        account_id = self.resolve_account_id()
        
        # Convert Pydantic model to dict for API
        payload = order.model_dump(exclude_none=True)
        logger.info(f"Formatted option payload: {payload}")
        
        logger.info(f"Previewing option {order.side} {order.quantity} {order.legs[0].symbol}...")
        
        res = self.trade_client.order_v2.preview_option(account_id, [payload])
        self._check_response(res, "preview_option")
        
        preview_data = res.json()
        logger.info(f"Option preview response: {preview_data}")
        
        return OrderPreviewResponse.model_validate(preview_data)

    def _get_buying_power(self) -> Optional[float]:
        """Get buying power (returns None if fails)"""
        try:
            balance = self.get_account_balance()
            return float(balance.get('buying_power', 0))
        except:
            return None

    # ============================================================================
    # Order Placement - Stocks
    # ============================================================================

    def place_stock_order(self, order: StockOrderRequest, skip_preview: bool = False) -> Dict[str, Any]:
        """Place stock order"""
        # Preview first (unless skipped)
        if not skip_preview:
            preview = self.preview_stock_order(order)
            if not preview:
                raise ValueError(f"Preview failed: {preview.errors}")
            logger.info(f"estimated cost: {preview.estimated_cost}, fee: {preview.estimated_transaction_fee}")
        
        # Build and send
        payload = self._build_stock_payload(order)
        return self._execute_order(payload, f"{order.side} {order.quantity} {order.symbol}")

    def _build_stock_payload(self, order: StockOrderRequest) -> Dict[str, Any]:
        """Build stock order payload"""
        payload = {
            "client_order_id": uuid.uuid4().hex,
            "symbol": order.symbol,
            "instrument_type": "EQUITY",
            "market": "US",
            "order_type": order.order_type,
            "quantity": self._format_quantity(order.quantity),
            "side": order.side,
            "time_in_force": order.time_in_force,
            "entrust_type": "QTY",
            "combo_type": "NORMAL",
            "support_trading_session": order.trading_session,
        }
        
        if order.order_type == OrderType.LIMIT:
            payload["limit_price"] = str(order.limit_price)
        
        return payload

    # ============================================================================
    # Order Placement - Options
    # ============================================================================

    def place_option_order(self, order: OptionOrderRequest, skip_preview: bool = False) -> Dict[str, Any]:
        """Place option order using Webull's place_option API"""
        if not skip_preview:
            preview = self.preview_option_order(order)
            if not preview:
                raise ValueError(f"Option preview failed: {preview.errors}")
            logger.info(f"Preview: ${preview.estimated_cost} {preview.currency}")
        
        account_id = self.resolve_account_id()
        
        # Convert Pydantic model to dict for API
        payload = order.model_dump(exclude_none=True)
        
        env = "UAT/PAPER" if self.paper_trade else "PRODUCTION/LIVE"
        symbol = order.legs[0].symbol if order.legs else "unknown"
        logger.info(f"Placing option {order.side} {order.quantity} {symbol} in {env}...")
        
        res = self.trade_client.order_v2.place_option(account_id, [payload])
        self._check_response(res, "place_option")
        
        response = res.json()
        logger.info(f"Option order placed: {response}")
        return response

    def _build_option_payload(self, order: OptionOrderRequest) -> Dict[str, Any]:
        """Build option order payload"""
        option_symbol = self._format_option_symbol(order)
        
        payload = {
            "client_order_id": uuid.uuid4().hex,
            "symbol": option_symbol,
            "instrument_type": "OPTION",
            "market": "US",
            "order_type": order.order_type,
            "quantity": str(order.quantity),
            "side": order.side,
            "time_in_force": order.time_in_force,
            "entrust_type": "QTY",
            "combo_type": "NORMAL",
            "support_trading_session": "CORE",
        }
        
        if order.order_type == OrderType.LIMIT:
            payload["limit_price"] = str(order.limit_price)
        
        return payload

    def _format_option_symbol(self, order: OptionOrderRequest) -> str:
        """Format option symbol (e.g., AAPL250117C00150000)"""
        expiry = order.expiry_date.replace("-", "")[2:]  # YYMMDD
        option_code = order.option_type[0]  # C or P
        strike = f"{int(order.strike_price * 1000):08d}"
        return f"{order.symbol}{expiry}{option_code}{strike}"

    # ============================================================================
    # Batch Orders
    # ============================================================================

    def place_batch_orders(
        self,
        stock_orders: Optional[List[StockOrderRequest]] = None,
        option_orders: Optional[List[OptionOrderRequest]] = None,
        skip_preview: bool = False
    ) -> Dict[str, Any]:
        """Place batch orders (up to 50)"""
        payloads = []
        
        # Add stock orders
        if stock_orders:
            payloads.extend(self._build_batch_stock_orders(stock_orders, skip_preview))
        
        # Add option orders
        if option_orders:
            payloads.extend(self._build_batch_option_orders(option_orders, skip_preview))
        
        if not payloads:
            logger.warning("No valid orders to place")
            return {}
        
        if len(payloads) > 50:
            raise ValueError(f"Max 50 orders per batch, got {len(payloads)}")
        
        env = "UAT/PAPER" if self.paper_trade else "PRODUCTION/LIVE"
        logger.info(f"Placing batch of {len(payloads)} orders in {env}...")
        
        account_id = self.resolve_account_id()
        res = self.trade_client.order_v2.place_order(account_id=account_id, new_orders=payloads)
        self._check_response(res, "batch_place_order")
        
        response = res.json()
        logger.info(f"Batch complete: {response}")
        return response

    def _build_batch_stock_orders(self, orders: List[StockOrderRequest], skip_preview: bool) -> List[Dict]:
        """Build stock order payloads for batch"""
        payloads = []
        for order in orders:
            if not skip_preview:
                preview = self.preview_stock_order(order)
                if not preview.valid:
                    logger.error(f"Skipping {order.symbol}: {preview.errors}")
                    continue
            payloads.append(self._build_stock_payload(order))
        return payloads

    def _build_batch_option_orders(self, orders: List[OptionOrderRequest], skip_preview: bool) -> List[Dict]:
        """Build option order payloads for batch"""
        payloads = []
        for order in orders:
            if not skip_preview:
                preview = self.preview_option_order(order)
                if not preview.valid:
                    logger.error(f"Skipping {order.symbol} option: {preview.errors}")
                    continue
            payloads.append(self._build_option_payload(order))
        return payloads

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _execute_order(self, payload: Dict[str, Any], description: str) -> Dict[str, Any]:
        """Execute order (common logic for stocks and options)"""
        account_id = self.resolve_account_id()
        env = "UAT/PAPER" if self.paper_trade else "PRODUCTION/LIVE"
        
        logger.info(f"Placing {description} in {env}...")
        
        res = self.trade_client.order_v2.place_order(account_id=account_id, new_orders=[payload])
        self._check_response(res, "place_order")
        
        response = res.json()
        logger.info(f"Order placed: {response}")
        return response

    def _check_response(self, response: Any, operation: str):
        """Check API response status"""
        if response.status_code != 200:
            raise RuntimeError(f"{operation} failed ({response.status_code}): {response.text}")

    def _format_quantity(self, quantity: float) -> str:
        """Format quantity as string"""
        return str(int(quantity)) if quantity.is_integer() else str(quantity)

    def _mask_id(self, account_id: str) -> str:
        """Mask account ID for logging"""
        return account_id[-4:].rjust(len(account_id), "•")