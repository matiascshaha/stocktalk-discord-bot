import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from webullsdkcore.client import ApiClient
from webullsdkcore.common.region import Region
from webullsdktrade.api import API


@dataclass(frozen=True)
class TradingConfig:
    app_key: str
    app_secret: str
    region: str = "US"              # "US", "HK", "JP" (maps to Region.*.value)
    account_id: Optional[str] = None # if None, we fetch the first account
    currency: str = "USD"           # used for balance endpoint in some regions

    paper_trade: bool = True
    min_confidence: float = 0.80
    default_dollar_amount: float = 250.0

    use_market_orders: bool = True
    extended_hours_trading: bool = False
    time_in_force: str = "DAY"      # common: DAY / GTC, etc. (check region docs)


class WebullTrader:
    """
    Webull OpenAPI (official) trading integration.

    - Auth is via Webull OpenAPI App Key + App Secret (NOT username/password).
    - Account list example uses: api.account_v2.get_account_list()  :contentReference[oaicite:2]{index=2}
    - Balance example uses: api.account.get_account_balance(account_id, currency) :contentReference[oaicite:3]{index=3}
    - Place order v2 example uses: api.order_v2.place_order(account_id=..., new_orders=...) :contentReference[oaicite:4]{index=4}
    """

    def __init__(self, config: TradingConfig):
        self.config = config
        self.api_client = ApiClient(
            config['app_key'],
            config['app_secret'],
            self._region_value(config['region'])
        )
        self.api = API(self.api_client)

        self._account_id: Optional[str] = config.account_id

    # ---------- Public helpers ----------

    def resolve_account_id(self) -> str:
        """Get account_id (uses configured account_id if provided; else fetch first available)."""
        if self._account_id:
            return self._account_id

        # Official example uses account_v2.get_account_list() :contentReference[oaicite:5]{index=5}
        res = self.api.account_v2.get_account_list()
        self._ensure_ok(res, "get_account_list")

        data = res.json()
        # The exact schema can vary by region/account type; handle common shapes safely.
        # Expecting something like {"accounts":[{"account_id":"..."}]} or a list.
        account_id = None

        if isinstance(data, dict):
            # try common keys
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
        """Return raw account balance JSON."""
        account_id = self.resolve_account_id()

        # Official example: api.account.get_account_balance(account_id, currency) :contentReference[oaicite:6]{index=6}
        res = self.api.account.get_account_balance(account_id, self.config.currency)
        self._ensure_ok(res, "get_account_balance")
        return res.json()

    def build_order_payload_from_pick(
        self,
        pick: Dict[str, Any],
        *,
        symbol: str,
        market: str = "US",
        instrument_type: str = "EQUITY",
        quantity: Optional[int] = None,
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Build a Webull OpenAPI order payload (v2 style) based on a parsed 'pick'.
        This does NOT place the trade; it just constructs the payload you can log/test.

        v2 example fields: symbol, instrument_type, market, order_type, limit_price, quantity,
        side, time_in_force, entrust_type ... :contentReference[oaicite:7]{index=7}
        """
        action = (pick.get("action") or "").upper()
        if action not in ("BUY", "SELL"):
            raise ValueError(f"Unsupported action for ordering: {action}")

        option_type = (pick.get("option_type") or "STOCK").upper()
        if option_type != "STOCK":
            # You told me earlier you want options too, but Webull OpenAPI options endpoints/params
            # differ by market. Keep this strict so you don't accidentally send the wrong thing.
            raise ValueError("This payload builder currently supports STOCK only (option_type=STOCK).")

        if quantity is None:
            # Use weight if present, else default dollars. We avoid guessing cash/buying power here.
            # In your pipeline, you can inject a computed quantity from your risk model.
            quantity = 1

        client_order_id = uuid.uuid4().hex

        if self.config.use_market_orders:
            order_type = "MARKET"
        else:
            order_type = "LIMIT"

        payload: Dict[str, Any] = {
            "client_order_id": client_order_id,
            "symbol": symbol,
            "instrument_type": instrument_type,
            "market": market,
            "order_type": order_type,
            "quantity": str(int(quantity)),
            "side": action,
            "time_in_force": self.config.time_in_force,
            "entrust_type": "QTY",
            # v2 example includes this; some regions may require/ignore:
            "support_trading_session": "Y" if self.config.extended_hours_trading else "N",
        }

        if order_type == "LIMIT":
            if limit_price is None:
                raise ValueError("limit_price is required when use_market_orders=False")
            payload["limit_price"] = str(limit_price)

        return payload

    def place_order_v2(self, new_order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place an order using order_v2.place_order(...) (official v2 example style). :contentReference[oaicite:8]{index=8}
        """
        if self.config.paper_trade:
            return {
                "paper": True,
                "status": "SIMULATED",
                "new_order": new_order_payload,
            }

        account_id = self.resolve_account_id()

        # Official example call style :contentReference[oaicite:9]{index=9}
        res = self.api.order_v2.place_order(account_id=account_id, new_orders=new_order_payload)
        self._ensure_ok(res, "place_order_v2")
        return res.json()

    # ---------- Internals ----------

    def _ensure_ok(self, response: Any, name: str) -> None:
        # SDK responses look like requests.Response (status_code/json)
        status = getattr(response, "status_code", None)
        if status != 200:
            body = None
            try:
                body = response.json()
            except Exception:
                body = getattr(response, "text", None)
            raise RuntimeError(f"{name} failed (status_code={status}): {body}")

    def _region_value(self, region: str) -> str:
        region_norm = (region or "US").upper().strip()
        if region_norm == "US":
            return Region.US.value
        if region_norm == "HK":
            return Region.HK.value
        if region_norm == "JP":
            return Region.JP.value
        raise ValueError("region must be one of: US, HK, JP")
