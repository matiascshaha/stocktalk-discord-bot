from typing import Any, Dict, List, Optional, Tuple


class QuoteAwareTraderProbe:
    """Fake trader with controllable quote sources and order-capture hooks."""

    def __init__(
        self,
        *,
        quote_payload: Any = None,
        quote_error: Optional[Exception] = None,
        snapshot_price: Optional[float] = None,
        snapshot_error: Optional[Exception] = None,
        instrument_payload: Optional[List[Dict[str, Any]]] = None,
        instrument_error: Optional[Exception] = None,
        place_response: Optional[Dict[str, Any]] = None,
    ):
        self.quote_payload = quote_payload if quote_payload is not None else []
        self.quote_error = quote_error
        self.snapshot_price = snapshot_price
        self.snapshot_error = snapshot_error
        self.instrument_payload = instrument_payload if instrument_payload is not None else []
        self.instrument_error = instrument_error
        self.place_response = place_response or {"client_order_id": "probe-order-1"}

        self.calls: List[Tuple[str, str]] = []
        self.placed_orders: List[Tuple[Any, Optional[float]]] = []

    def get_stock_quotes(self, symbol: str, category: str = "US_STOCK") -> Any:
        _ = category
        self.calls.append(("get_stock_quotes", symbol))
        if self.quote_error is not None:
            raise self.quote_error
        return self.quote_payload

    def get_current_stock_quote(self, symbol: str) -> Optional[float]:
        self.calls.append(("get_current_stock_quote", symbol))
        if self.snapshot_error is not None:
            raise self.snapshot_error
        return self.snapshot_price

    def get_instrument(self, symbols: str, category: str = "US_STOCK") -> List[Dict[str, Any]]:
        _ = category
        self.calls.append(("get_instrument", symbols))
        if self.instrument_error is not None:
            raise self.instrument_error
        return self.instrument_payload

    def place_stock_order(self, order, weighting=None):
        self.calls.append(("place_stock_order", order.symbol))
        self.placed_orders.append((order, weighting))
        return self.place_response
