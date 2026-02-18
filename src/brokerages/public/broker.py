"""Public brokerage adapter scaffold."""

from typing import Any, Dict, Optional

from src.trading.contracts import OrderResult, StockOrder


class PublicBroker:
    """Public adapter placeholder implementing the common trading broker interface."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}

    def place_stock_order(self, order: StockOrder, weighting: Optional[float] = None) -> OrderResult:
        _ = order
        _ = weighting
        raise NotImplementedError("Public broker stock execution is not implemented yet.")

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        _ = symbol
        _ = side
        raise NotImplementedError("Public broker quote resolution is not implemented yet.")
