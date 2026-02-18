"""Webull brokerage adapter for runtime order execution."""

from typing import Optional

from src.brokerages.webull.quote_service import resolve_limit_reference_price
from src.brokerages.webull.mapper import to_order_result, to_webull_stock_order
from src.trading.contracts import OrderResult, StockOrder
from src.webull_trader import WebullTrader


class WebullBroker:
    """Thin adapter exposing the Brokerage interface over WebullTrader."""

    def __init__(self, trader: WebullTrader):
        self._trader = trader

    def place_stock_order(self, order: StockOrder, weighting: Optional[float] = None) -> OrderResult:
        webull_order = to_webull_stock_order(order)
        response = self._trader.place_stock_order(webull_order, weighting=weighting)
        return to_order_result(response)

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        return resolve_limit_reference_price(self._trader, symbol, side)
