"""Composite trading broker that splits execution and quote providers."""

from typing import Optional

from src.brokerages.ports import MarketDataPort, StockOrderBrokerPort
from src.trading.contracts import OrderResult, StockOrder


class CompositeTradingBroker:
    """Compose distinct execution and quote providers into one broker port."""

    def __init__(self, execution_broker: StockOrderBrokerPort, quote_provider: MarketDataPort):
        self._execution_broker = execution_broker
        self._quote_provider = quote_provider

    def place_stock_order(self, order: StockOrder, weighting: Optional[float] = None) -> OrderResult:
        return self._execution_broker.place_stock_order(order, weighting=weighting)

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        return self._quote_provider.get_limit_reference_price(symbol, side)
