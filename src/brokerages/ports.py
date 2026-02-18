"""Broker ports used by trading execution."""

from typing import Optional, Protocol

from src.trading.contracts import OrderResult, StockOrder


class StockOrderBrokerPort(Protocol):
    """Stock execution operations required by order routing."""

    def place_stock_order(self, order: StockOrder, weighting: Optional[float] = None) -> OrderResult:
        ...


class MarketDataPort(Protocol):
    """Market-data operations required to build executable limit orders."""

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        ...


class TradingBrokerPort(StockOrderBrokerPort, MarketDataPort, Protocol):
    """Composed broker contract for stock execution flow."""
