"""Option order executor that delegates directly to brokerage adapters."""

from src.brokerages.base import Brokerage
from src.trading.orders.contracts import OptionOrderRequest, OrderSubmissionResult


class OptionOrderExecutor:
    """Execute option orders through the unified brokerage contract."""

    def __init__(self, broker: Brokerage):
        self._broker = broker

    def execute(self, order: OptionOrderRequest) -> OrderSubmissionResult:
        return self._broker.place_option_order(order)
