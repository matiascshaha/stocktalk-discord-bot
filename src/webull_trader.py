"""
Production-Ready Webull OpenAPI Trading Integration

Simplified, clean, and maintainable implementation.
"""

import uuid
from typing import Any, Dict, Optional, List

import webull
from webull.core.client import ApiClient
from webull.core import __version__ as webull_core_version
from webull.core.common.region import Region
from webull.data.quotes.instrument import Instrument
from webull.data.quotes.market_data import MarketData
from webull.trade.common.currency import Currency
from webull.trade.trade.account_info import Account
from webull.trade.trade.order_operation import OrderOperation
from webull.trade.trade.v2.account_info_v2 import AccountV2
from webull.trade.trade.v2.order_operation_v2 import OrderOperationV2

from src.utils.logger import setup_logger
from src.brokerages.webull.stock_payload_builder import (
    WebullStockPayloadBuilder,
    normalize_stock_quantity,
)
from src.models.webull_models import (
    AccountBalanceResponse,
    OptionOrderRequest,
    OrderPreviewResponse,
    OrderType,
    StockOrderRequest,
)
from src.trading.buying_power import assert_margin_equity_buffer, resolve_effective_buying_power
from src.trading.orders.sizing import resolve_stock_sizing_decision

from config.settings import TRADING_CONFIG, WEBULL_CONFIG
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
        region: str = Region.US.value,
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
        
        if not hasattr(webull, "__version__"):
            webull.__version__ = webull_core_version

        self.api_client = ApiClient(self.app_key, self.app_secret, self.region)
        self.api_client.add_endpoint(self.region, endpoint)
        self._account_id = WEBULL_CONFIG.get('test_account_id') if self.paper_trade else self._account_id
        self._init_service_clients()

    def _init_service_clients(self) -> None:
        """Initialize explicit SDK clients used by this trader."""
        self.account_api = Account(self.api_client)
        self.account_v2_api = AccountV2(self.api_client)
        self.order_api = OrderOperation(self.api_client)
        self.order_v2_api = OrderOperationV2(self.api_client)
        self.instrument_api = Instrument(self.api_client)
        self.market_data_api = MarketData(self.api_client)

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

        res = self.account_v2_api.get_account_list()
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

    def get_account_balance(self, currency: str = Currency.USD.name) -> Dict[str, Any]:
        """Get account balance"""
        account_id = self.resolve_account_id()

        res = self.account_api.get_account_balance(account_id, currency)
        self._check_response(res, "get_account_balance")
        return res.json()

    def get_account_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        account_id = self.resolve_account_id()
        res = self.account_v2_api.get_account_position(account_id)
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


    def preview_stock_order(self, order: StockOrderRequest) -> OrderPreviewResponse:
        """
        Build a local stock order estimate.
        The installed SDK does not expose a stock preview endpoint like options do.
        """
        instrument = self.get_instrument(order.symbol)
        if not instrument:
            raise ValueError(f"Instrument not found for symbol: {order.symbol}")

        market_price = instrument[0].get("last_price")
        if market_price is None:
            raise ValueError(f"Instrument missing last_price for symbol: {order.symbol}")

        unit_price = float(order.limit_price) if order.order_type == OrderType.LIMIT else float(market_price)
        estimated_cost = unit_price * float(order.quantity)
        preview = OrderPreviewResponse(
            estimated_cost=f"{estimated_cost:.2f}",
            estimated_transaction_fee="0.00",
            currency=WEBULL_CONFIG.get("currency", "USD"),
        )
        logger.info(
            "Local stock preview: %s %s %s @ %.4f (estimated_cost=%s)",
            order.side,
            order.quantity,
            order.symbol,
            unit_price,
            preview.estimated_cost,
        )
        return preview

    def preview_option_order(self, order: OptionOrderRequest) -> OrderPreviewResponse:
        """Preview option order using Webull's preview_option API"""
        account_id = self.resolve_account_id()
        
        # Convert Pydantic model to dict for API
        payload = order.model_dump(exclude_none=True)
        logger.info(f"Formatted option payload: {payload}")
        
        logger.info(f"Previewing option {order.side} {order.quantity} {order.legs[0].symbol}...")
        
        res = self.order_v2_api.preview_option(account_id, [payload])
        self._check_response(res, "preview_option")
        
        preview_data = res.json()
        logger.info(f"Option preview response: {preview_data}")
        
        return OrderPreviewResponse.model_validate(preview_data)

    def _get_account_balance_contract(self) -> Optional[AccountBalanceResponse]:
        """Fetch and validate Webull account-balance payload."""
        try:
            return AccountBalanceResponse.model_validate(self.get_account_balance())
        except Exception as exc:
            logger.warning("Unable to parse account balance payload: %s", exc)
            return None

    def _get_buying_power(self, balance: Optional[AccountBalanceResponse] = None) -> Optional[float]:
        """Resolve effective buying power from Webull account payload."""
        resolved_balance = balance or self._get_account_balance_contract()
        if resolved_balance is None:
            return None
        return self._resolve_effective_buying_power(resolved_balance)

    def _resolve_effective_buying_power(self, balance: AccountBalanceResponse) -> Optional[float]:
        return resolve_effective_buying_power(balance)

    def _enforce_margin_buffer(self, balance: Optional[AccountBalanceResponse], estimated_trade_notional: float) -> None:
        """Reject sizing decisions that violate configured margin-equity floor."""
        threshold = TRADING_CONFIG.get("min_margin_equity_pct")
        try:
            threshold_value = float(threshold)
        except (TypeError, ValueError):
            logger.warning("Ignoring invalid trading.min_margin_equity_pct=%r", threshold)
            return

        if threshold_value <= 0:
            return
        if balance is None:
            raise ValueError("Unable to enforce margin buffer: account balance unavailable")
        assert_margin_equity_buffer(
            balance=balance,
            min_margin_equity_pct=threshold_value,
            estimated_trade_notional=estimated_trade_notional,
        )

    # ============================================================================
    # Order Placement - Stocks
    # ============================================================================

    def place_stock_order(self, order: StockOrderRequest, notional_dollar_amount: float = None, weighting: float = None) -> Dict[str, Any]:
        """Place stock order"""
        sizing = resolve_stock_sizing_decision(
            side=order.side,
            explicit_notional=notional_dollar_amount,
            weighting=weighting,
            trading_config=TRADING_CONFIG,
        )
        if sizing.notional_dollar_amount is not None:
            payload = self._build_stock_payload(order, notional_dollar_amount=sizing.notional_dollar_amount)
        else:
            try:
                payload = self._build_stock_payload(order, weighting=sizing.weighting)
            except Exception as exc:
                if sizing.fallback_notional_on_weighting_error is None:
                    raise
                logger.warning(
                    "Weighting-based sizing failed for %s (%s); retrying with default_amount=%.2f",
                    order.symbol,
                    exc,
                    sizing.fallback_notional_on_weighting_error,
                )
                payload = self._build_stock_payload(
                    order,
                    notional_dollar_amount=sizing.fallback_notional_on_weighting_error,
                )

        qty = payload.get("qty", order.quantity)
        return self._execute_order(payload, f"{order.side} {qty} {order.symbol}")

    def _build_stock_payload(
        self,
        order: StockOrderRequest,
        notional_dollar_amount: float = None,
        weighting: float = None,
    ) -> Dict[str, Any]:
        """Build stock payload via dedicated stock sizing/payload module."""
        builder = self._create_stock_payload_builder()
        return builder.build(
            order,
            notional_dollar_amount=notional_dollar_amount,
            weighting=weighting,
        )

    def _create_stock_payload_builder(self) -> WebullStockPayloadBuilder:
        return WebullStockPayloadBuilder(
            client_order_id_factory=lambda: uuid.uuid4().hex,
            get_instrument=self.get_instrument,
            get_account_balance_contract=self._get_account_balance_contract,
            get_buying_power=self._get_buying_power,
            get_current_stock_quote=self.get_current_stock_quote,
            enforce_margin_buffer=self._enforce_margin_buffer,
        )

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
        
        res = self.order_v2_api.place_option(account_id, [payload])
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
        res = self.order_api.place_order(account_id=account_id, new_orders=payloads)
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
    # Quotes Methods
    # ============================================================================

    def get_instrument(self, symbols: str, category: str = "US_STOCK") -> List[Dict[str, Any]]:
        response = self.instrument_api.get_instrument(symbols, category)
        self._check_response(response, "get_instrument")
        instruments = response.json()
        logger.info(f"Fetched {len(instruments)} instruments for symbols: {symbols}")
        return instruments

    def get_market_snapshot(self, symbols: str, category: str = "US_STOCK") -> List[Dict[str, Any]]:
        response = self.market_data_api.get_snapshot(symbols, category)
        self._check_response(response, "get_market_snapshot")
        snapshots = response.json()
        logger.info(f"Fetched {len(snapshots)} market snapshots for symbols: {symbols}")
        return snapshots

    def get_stock_quotes(self, symbol: str, category: str = "US_STOCK") -> Any:
        response = self.market_data_api.get_quotes(symbol, category)
        self._check_response(response, "get_stock_quotes")
        quotes = response.json()
        logger.info("Fetched stock quotes for symbol: %s", symbol)
        return quotes
    
    def get_current_stock_quote(self, symbol: str) -> Optional[float]:
        snapshots = self.get_market_snapshot(symbol, category="US_STOCK")
        if snapshots:
            return float(snapshots[0].get('price'))
        return None

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _execute_order(self, payload: Dict[str, Any], description: str) -> Dict[str, Any]:
        """Execute order (common logic for stocks and options)"""
        account_id = self.resolve_account_id()
        env = "UAT/PAPER" if self.paper_trade else "PRODUCTION/LIVE"
        
        logger.info(f"Placing {description} in {env}...")
        
        res = self.order_api.place_order(account_id=account_id, **payload)
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

    def _normalize_stock_quantity(self, quantity: float) -> int:
        return normalize_stock_quantity(quantity)

    def _mask_id(self, account_id: str) -> str:
        """Mask account ID for logging"""
        return account_id[-4:].rjust(len(account_id), "•")
