import uuid
from typing import Any, Dict, Optional, List

from webullsdkcore.client import ApiClient
from webullsdktrade.api import API

from src.utils.logger import setup_logger

logger = setup_logger("webull_trader")


class WebullTrader:
    """
    Webull OpenAPI trading integration with REAL paper trading support.
    
    Key Features:
    - Paper trading: Uses Webull's UAT/test environment (us-openapi-alb.uat.webullbroker.com)
    - Live trading: Uses production environment (api.webull.com)
    - Both modes hit REAL Webull APIs (not simulated locally)
    
    Environments:
    - Production: api.webull.com (REAL MONEY)
    - UAT/Test: us-openapi-alb.uat.webullbroker.com (PAPER TRADING)
    
    Configuration:
    - app_key, app_secret: Webull OpenAPI credentials
    - region: Trading region (US, HK, JP)
    - paper_trade: If True, uses UAT endpoint; if False, uses production
    - use_market_orders: If False, requires limit_price for orders
    """

    # Webull API Endpoints
    ENDPOINTS = {
        'us': {
            'production': 'api.webull.com',
            'uat': 'us-openapi-alb.uat.webullbroker.com',
        },
        'hk': {
            'production': 'api.webull.hk',
            'uat': 'api.sandbox.webull.hk',
        },
        'jp': {
            'production': 'api.webull.co.jp',
            'uat': 'jp-openapi-alb.uat.webullbroker.com',
        },
    }

    def __init__(self, config: Dict[str, Any], trading_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Webull trader.
        
        Args:
            config: Base configuration dict
            trading_config: Optional trading-specific overrides
        """
        raw = dict(config)

        # Merge trading_config overrides if provided
        if trading_config:
            raw = {
                **raw,
                "paper_trade": trading_config.get("paper_trade", raw.get("paper_trade")),
                "min_confidence": trading_config.get("min_confidence", raw.get("min_confidence")),
                "default_amount": trading_config.get("default_amount", raw.get("default_amount")),
                "default_dollar_amount": trading_config.get(
                    "default_amount",
                    raw.get("default_dollar_amount", raw.get("default_amount")),
                ),
                "use_market_orders": trading_config.get("use_market_orders", raw.get("use_market_orders")),
                "extended_hours_trading": trading_config.get("extended_hours_trading", raw.get("extended_hours_trading")),
                "time_in_force": trading_config.get("time_in_force", raw.get("time_in_force")),
            }

        self.config = self._normalize_config(raw)
        logger.info(f"Webull config: {self.config}")

        # Validate required credentials
        if not self.config.get("app_key") or not self.config.get("app_secret"):
            raise ValueError("WEBULL_APP_KEY and WEBULL_APP_SECRET are required for Webull OpenAPI.")

        # Initialize API client with appropriate endpoint
        region_id = self.config.get("region", "us").lower()
        
        # Determine endpoint based on paper_trade flag
        endpoint = self._get_endpoint(region_id, self.config.get("paper_trade"))
        
        # Log which environment we're using
        env_type = "UAT/PAPER" if self.config.get("paper_trade") else "PRODUCTION/LIVE"
        logger.info(f"Initializing Webull API in {env_type} mode: {endpoint}")
        
        # Initialize API client
        self.api_client = ApiClient(
            self.config.get("app_key"),
            self.config.get("app_secret"),
            region_id,
        )
        
        # Set the endpoint (UAT or Production)
        self.api_client.add_endpoint(region_id, endpoint)
        
        # Initialize API (this gives us access to account_v2, order_v2, etc.)
        self.api = API(self.api_client)
        
        # Cache account_id if provided
        self._account_id: Optional[str] = self.config.get("account_id")

    def _get_endpoint(self, region: str, paper_trade: bool) -> str:
        """
        Get the appropriate API endpoint based on region and paper_trade flag.
        
        Args:
            region: Region code (us, hk, jp)
            paper_trade: If True, return UAT endpoint; if False, return production
            
        Returns:
            str: API endpoint URL
        """
        region = region.lower()
        if region not in self.ENDPOINTS:
            raise ValueError(f"Unsupported region: {region}. Supported: {list(self.ENDPOINTS.keys())}")
        
        endpoint_type = 'uat' if paper_trade else 'production'
        return self.ENDPOINTS[region][endpoint_type]

    # ---------- Account Management ----------

    def resolve_account_id(self) -> str:
        """
        Get account_id (uses configured account_id if provided; else fetch first available).
        
        Returns:
            str: The account ID
            
        Raises:
            RuntimeError: If account list cannot be fetched or parsed
        """
        if self._account_id:
            return self._account_id

        # Fetch account list using v2 API
        res = self.api.account_v2.get_account_list()
        self._ensure_ok(res, "get_account_list")

        data = res.json()
        account_id = None

        # Handle various response formats
        if isinstance(data, dict):
            # Try common keys
            for key in ("accounts", "account_list", "data", "list"):
                if key in data and isinstance(data[key], list) and data[key]:
                    account_id = data[key][0].get("account_id") or data[key][0].get("accountId")
                    break
            if not account_id and "account_id" in data:
                account_id = data.get("account_id")
        elif isinstance(data, list) and data:
            account_id = data[0].get("account_id") or data[0].get("accountId")

        if not account_id:
            raise RuntimeError(f"Could not parse account_id from account list response: {data}")

        self._account_id = str(account_id)
        return self._account_id

    def get_account_balance(self) -> Dict[str, Any]:
        """
        Return raw account balance JSON.
        
        Returns:
            Dict: Account balance data
        """
        account_id = self.resolve_account_id()
        res = self.api.account_v2.get_account_balance(account_id)
        self._ensure_ok(res, "get_account_balance")
        return res.json()
    
    def get_account_positions(self) -> Dict[str, Any]:
        """
        Return raw account positions JSON.
        
        Returns:
            Dict: Account positions data
        """
        account_id = self.resolve_account_id()
        res = self.api.account_v2.get_account_position(account_id)
        self._ensure_ok(res, "get_account_position")
        return res.json()

    def login(self) -> bool:
        """
        Validate Webull OpenAPI credentials by resolving account_id.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            account_id = self.resolve_account_id()
            account_id_str = str(account_id)
            masked = account_id_str[-4:].rjust(len(account_id_str), "•") if account_id else "unknown"
            env_type = "UAT/PAPER" if self.config.get("paper_trade") else "PRODUCTION/LIVE"
            logger.info(f"Webull OpenAPI authenticated in {env_type} mode (account_id {masked})")
            return True
        except Exception as exc:
            logger.error("Webull OpenAPI login failed: %s", exc)
            return False

    # ---------- Order Building ----------

    def build_order_payload_from_pick(
        self,
        pick: Dict[str, Any],
        *,
        symbol: str,
        market: Optional[str] = None,
        instrument_type: str = "EQUITY",
        quantity: Optional[int] = None,
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Build a Webull OpenAPI order payload (v2 style) based on a parsed 'pick'.
        This does NOT place the trade; it just constructs the payload.

        Args:
            pick: Parsed pick dict with action, confidence, etc.
            symbol: Stock symbol
            market: Market (US, HK, JP)
            instrument_type: EQUITY, OPTION, etc.
            quantity: Number of shares
            limit_price: Limit price (required if not using market orders)
            
        Returns:
            Dict: Order payload ready for place_order_v2
            
        Raises:
            ValueError: If action unsupported or required fields missing
        """
        action = (pick.get("action") or "").upper()
        if action not in ("BUY", "SELL"):
            raise ValueError(f"Unsupported action for ordering: {action}")

        option_type = (pick.get("option_type") or "STOCK").upper()
        if option_type != "STOCK":
            raise ValueError("This payload builder currently supports STOCK only (option_type=STOCK).")

        if quantity is None:
            quantity = 1

        client_order_id = uuid.uuid4().hex

        if self.config.get("use_market_orders"):
            order_type = "MARKET"
        else:
            order_type = "LIMIT"

        payload: Dict[str, Any] = {
            "client_order_id": client_order_id,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "market": (market or self.config.get("default_market")),
            "order_type": order_type,
            "quantity": self._format_quantity(quantity),
            "side": action,
            "time_in_force": self.config.get("time_in_force"),
            "entrust_type": "QTY",
            "support_trading_session": "Y" if self.config.get("extended_hours_trading") else "N",
        }

        if self.config.get("account_tax_type"):
            payload["account_tax_type"] = self.config.get("account_tax_type")

        if order_type == "LIMIT":
            if limit_price is None:
                raise ValueError("limit_price is required when use_market_orders=False")
            payload["limit_price"] = str(limit_price)

        return payload

    # ---------- Order Placement ----------

    def place_order_v2(self, new_order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place an order using order_v2.place_order (official v2 API style).
        
        This ACTUALLY calls the Webull API:
        - If paper_trade=True: Calls UAT environment (test account, fake money)
        - If paper_trade=False: Calls production environment (REAL MONEY!)
        
        Args:
            new_order_payload: Order payload from build_order_payload_from_pick
            
        Returns:
            Dict: Order response from Webull API
        """
        account_id = self.resolve_account_id()
        env_type = "UAT/PAPER" if self.config.get("paper_trade") else "PRODUCTION/LIVE"
        
        logger.info(f"Placing order in {env_type} environment...")

        try:
            # Place order using v2 API (hits REAL Webull endpoint)
            res = self.api.order_v2.place_order(account_id=account_id, new_orders=new_order_payload)
            self._ensure_ok(res, "place_order_v2")
            response = res.json()
            
            # Add metadata to indicate which environment was used
            response['_environment'] = env_type
            response['_paper_trade'] = self.config.get("paper_trade")
            
            return response
        except Exception as exc:
            logger.error("Order placement failed in %s environment: %s", env_type, exc)
            raise

    def execute_trade(self, pick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a trade based on a parsed pick.
        
        Args:
            pick: Pick dict with ticker, action, confidence, price, etc.
            
        Returns:
            Dict: Order response on success, None otherwise
        """
        try:
            # Extract and validate symbol
            symbol = self._normalize_symbol(pick.get("ticker") or pick.get("symbol"))
            if not symbol:
                logger.warning("Skipping trade: missing ticker/symbol in pick %s", pick)
                return None

            # Validate action
            action = (pick.get("action") or "").upper()
            if action not in ("BUY", "SELL"):
                logger.warning("Skipping trade for %s: unsupported action %s", symbol, action)
                return None

            # Check confidence threshold
            confidence = float(pick.get("confidence") or 0.0)
            if confidence < self.config.get("min_confidence"):
                logger.info(
                    "Skipping %s: confidence %.2f below threshold %.2f",
                    symbol,
                    confidence,
                    self.config.get("min_confidence"),
                )
                return None

            # Check option type (only support STOCK for now)
            option_type = (pick.get("option_type") or "STOCK").upper()
            if option_type != "STOCK":
                logger.info("Skipping %s: options not supported (option_type=%s)", symbol, option_type)
                return None

            # Skip SELL orders (require manual review)
            if action == "SELL":
                logger.info("Skipping SELL for %s (manual review required)", symbol)
                return None

            # Calculate quantity
            quantity = self._calculate_quantity(pick)
            if not quantity:
                logger.warning("Skipping %s: unable to determine quantity", symbol)
                return None

            # Get limit price if needed
            limit_price = None
            if not self.config.get("use_market_orders"):
                limit_price = pick.get("price") or pick.get("limit_price")
                if limit_price is None:
                    logger.warning("Skipping %s: limit price required for limit orders", symbol)
                    return None

            # Build order payload
            payload = self.build_order_payload_from_pick(
                pick,
                symbol=symbol,
                market=(pick.get("market") or self.config.get("default_market")),
                instrument_type="EQUITY",
                quantity=quantity,
                limit_price=limit_price,
            )

            # Place order (hits REAL API)
            result = self.place_order_v2(payload)
            env_type = result.get('_environment', 'UNKNOWN')
            logger.info("Order submitted for %s (%s) in %s environment", symbol, action, env_type)
            return result
            
        except Exception as exc:
            logger.error("Trade execution failed: %s", exc, exc_info=True)
            return None

    # ---------- Query Methods ----------
    
    def get_order_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get order history.
        
        Args:
            limit: Maximum number of orders to return
            
        Returns:
            List of order dicts
        """
        account_id = self.resolve_account_id()
        res = self.api.order_v2.query_orders_v2(account_id=account_id)
        self._ensure_ok(res, "query_orders_v2")
        data = res.json()
        
        # Handle various response formats
        if isinstance(data, dict):
            return data.get("orders", data.get("data", []))[:limit]
        return data[:limit] if isinstance(data, list) else []

    # ---------- Internals ----------

    def _normalize_config(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate configuration."""
        def _first(*keys: str) -> Optional[Any]:
            for key in keys:
                if key in raw and raw[key] is not None:
                    return raw[key]
            return None

        default_amount = raw.get("default_amount", raw.get("default_dollar_amount", 250.0))
        if default_amount is None:
            default_amount = 250.0

        return {
            "app_key": _first("app_key", "appKey"),
            "app_secret": _first("app_secret", "appSecret"),
            "region": str(_first("region") or "US"),
            "account_id": _first("account_id", "accountId"),
            "currency": str(_first("currency") or "USD"),
            "account_tax_type": _first("account_tax_type", "accountTaxType") or "GENERAL",
            "default_market": str(_first("default_market") or "US"),
            "paper_trade": bool(raw.get("paper_trade", True)),
            "min_confidence": float(raw.get("min_confidence", 0.80)),
            "default_dollar_amount": float(default_amount),
            "use_market_orders": bool(raw.get("use_market_orders", True)),
            "extended_hours_trading": bool(raw.get("extended_hours_trading", False)),
            "time_in_force": str(raw.get("time_in_force", "DAY")),
        }

    def _calculate_quantity(self, pick: Dict[str, Any]) -> Optional[float]:
        """Calculate order quantity from pick."""
        quantity = pick.get("quantity")
        if quantity:
            try:
                return float(quantity)
            except (TypeError, ValueError):
                return None

        price = pick.get("price")
        if price:
            try:
                price_val = float(price)
                if price_val <= 0:
                    return None
                qty = max(1, int(self.config.get("default_dollar_amount") // price_val))
                return qty
            except (TypeError, ValueError):
                return None

        return 1

    def _format_quantity(self, quantity: Any) -> str:
        """Format quantity as string."""
        try:
            if float(quantity).is_integer():
                return str(int(quantity))
            return str(quantity)
        except Exception:
            return str(quantity)

    def _normalize_symbol(self, symbol: Optional[str]) -> str:
        """Normalize stock symbol."""
        if not symbol:
            return ""
        return str(symbol).strip().replace("$", "").upper()

    def _ensure_ok(self, response: Any, name: str) -> None:
        """Ensure API response is successful."""
        status = getattr(response, "status_code", None)
        if status != 200:
            body = None
            try:
                body = response.json()
            except Exception:
                body = getattr(response, "text", None)
            raise RuntimeError(f"{name} failed (status_code={status}): {body}")