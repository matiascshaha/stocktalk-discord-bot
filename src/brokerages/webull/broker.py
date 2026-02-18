"""Webull brokerage adapter for runtime order execution."""

from typing import Any, Dict, Optional

from src.models.webull_models import StockOrderRequest
from src.brokerages.webull.quote_service import resolve_limit_reference_price
from src.webull_trader import WebullTrader


class WebullBroker:
    """Thin adapter exposing the Brokerage interface over WebullTrader."""

    def __init__(self, trader: WebullTrader):
        self._trader = trader

    def place_stock_order(
        self,
        order: StockOrderRequest,
        weighting: Optional[float] = None,
        notional_dollar_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        return self._trader.place_stock_order(
            order,
            weighting=weighting,
            notional_dollar_amount=notional_dollar_amount,
        )

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        return resolve_limit_reference_price(self._trader, symbol, side)
