"""Broker interface used by runtime order execution."""

from typing import Any, Dict, Optional, Protocol

from src.models.webull_models import StockOrderRequest


class Brokerage(Protocol):
    """Minimal brokerage contract required for stock execution routing."""

    def place_stock_order(
        self,
        order: StockOrderRequest,
        weighting: Optional[float] = None,
        notional_dollar_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        ...

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        ...
