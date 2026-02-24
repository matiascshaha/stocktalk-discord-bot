"""Webull stock-order payload construction and sizing policy."""

from typing import Any, Callable, Dict, List, Mapping, Optional

from src.models.webull_models import AccountBalanceResponse, OrderType, StockOrderRequest


class WebullStockPayloadBuilder:
    """Build stock order payloads without mutating the input order."""

    def __init__(
        self,
        *,
        client_order_id_factory: Callable[[], str],
        get_instrument: Callable[[str], List[Dict[str, Any]]],
        get_account_balance_contract: Callable[[], Optional[AccountBalanceResponse]],
        get_buying_power: Callable[..., Optional[float]],
        get_current_stock_quote: Callable[[str], Optional[float]],
        enforce_margin_buffer: Callable[[Optional[AccountBalanceResponse], float], None],
    ):
        self._client_order_id_factory = client_order_id_factory
        self._get_instrument = get_instrument
        self._get_account_balance_contract = get_account_balance_contract
        self._get_buying_power = get_buying_power
        self._get_current_stock_quote = get_current_stock_quote
        self._enforce_margin_buffer = enforce_margin_buffer

    def build(
        self,
        order: StockOrderRequest,
        *,
        notional_dollar_amount: Optional[float] = None,
        weighting: Optional[float] = None,
    ) -> Dict[str, Any]:
        instruments = self._get_instrument(order.symbol)
        if not instruments:
            raise ValueError(f"Instrument not found for symbol: {order.symbol}")

        instrument = instruments[0]
        instrument_id = instrument.get("instrument_id")
        quantity = self._resolve_quantity(
            order,
            instrument=instrument,
            notional_dollar_amount=notional_dollar_amount,
            weighting=weighting,
        )
        qty = normalize_stock_quantity(quantity)

        payload: Dict[str, Any] = {
            "client_order_id": self._client_order_id_factory(),
            "instrument_id": instrument_id,
            "order_type": order.order_type,
            "qty": qty,
            "side": order.side,
            "tif": order.time_in_force,
            "extended_hours_trading": order.extended_hours_trading,
        }
        if order.order_type == OrderType.LIMIT:
            payload["limit_price"] = str(order.limit_price)
        return payload

    def _resolve_quantity(
        self,
        order: StockOrderRequest,
        *,
        instrument: Mapping[str, Any],
        notional_dollar_amount: Optional[float],
        weighting: Optional[float],
    ) -> float:
        if notional_dollar_amount is not None:
            price = resolve_notional_sizing_price(order, instrument)
            if price is None or price <= 0:
                raise ValueError(f"Invalid price for symbol {order.symbol}: {price}")
            balance = self._get_account_balance_contract()
            self._enforce_margin_buffer(balance, estimated_trade_notional=float(notional_dollar_amount))
            return float(notional_dollar_amount) / float(price)

        if weighting is not None:
            balance = self._get_account_balance_contract()
            buying_power = self._get_buying_power(balance=balance)
            if buying_power is None:
                raise ValueError("Unable to fetch buying power for weighting calculation")

            stock_price = self._get_current_stock_quote(order.symbol)
            if stock_price is None or stock_price <= 0:
                raise ValueError(f"Unable to fetch current price for symbol {order.symbol}")

            weighting_decimal = float(weighting) / 100.0
            dollar_amount = float(buying_power) * weighting_decimal
            self._enforce_margin_buffer(balance, estimated_trade_notional=dollar_amount)
            return dollar_amount / float(stock_price)

        return float(order.quantity)


def normalize_stock_quantity(quantity: float) -> int:
    """
    Webull stock orders require whole-share quantity for this flow.
    Round down fractional inputs and reject non-positive results.
    """
    qty = int(float(quantity))
    if qty < 1:
        raise ValueError(f"Computed stock quantity must be >= 1 share, got {quantity}")
    return qty


def resolve_instrument_price(instrument: Mapping[str, Any]) -> Optional[float]:
    for key in ("last_price", "price", "close", "pre_close", "ask_price", "bid_price", "ask", "bid"):
        value = instrument.get(key)
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return parsed
    return None


def resolve_notional_sizing_price(order: StockOrderRequest, instrument: Mapping[str, Any]) -> Optional[float]:
    if order.limit_price is not None:
        try:
            limit_price = float(order.limit_price)
        except (TypeError, ValueError):
            limit_price = None
        if limit_price is not None and limit_price > 0:
            return limit_price
    return resolve_instrument_price(instrument)
