"""Broker interface used by runtime order execution."""

from typing import Any, Dict, Optional, Protocol

from src.models.webull_models import StockOrderRequest


class Brokerage(Protocol):
    """Minimal brokerage contract required for stock execution routing."""

    def place_stock_order(self, order: StockOrderRequest, weighting: Optional[float] = None) -> Dict[str, Any]:
        ...

    def get_current_stock_quote(self, symbol: str) -> Optional[float]:
        ...

