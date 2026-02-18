"""Webull brokerage adapter for runtime order execution."""

from typing import Any, Dict, Optional

from src.models.webull_models import StockOrderRequest
from src.brokerages.webull.quote_service import resolve_stock_quote
from src.webull_trader import WebullTrader


class WebullBroker:
    """Thin adapter exposing the Brokerage interface over WebullTrader."""

    def __init__(self, trader: WebullTrader):
        self._trader = trader

    def place_stock_order(self, order: StockOrderRequest, weighting: Optional[float] = None) -> Dict[str, Any]:
        return self._trader.place_stock_order(order, weighting=weighting)

    def get_current_stock_quote(self, symbol: str) -> Optional[float]:
        return resolve_stock_quote(self._trader, symbol)
