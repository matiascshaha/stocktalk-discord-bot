"""Broker interface used by runtime order execution."""

from typing import Optional, Protocol

from src.trading.orders.contracts import (
    AccountBalanceSnapshot,
    BrokerageCapabilities,
    OptionOrderRequest,
    OrderPreviewResult,
    OrderSubmissionResult,
    PositionSnapshot,
    StockOrderRequest,
)


class Brokerage(Protocol):
    """Brokerage contract used by runtime order routing."""

    def get_capabilities(self) -> BrokerageCapabilities:
        ...

    def place_stock_order(self, order: StockOrderRequest, weighting: Optional[float] = None) -> OrderSubmissionResult:
        ...

    def preview_stock_order(self, order: StockOrderRequest) -> OrderPreviewResult:
        ...

    def place_option_order(self, order: OptionOrderRequest) -> OrderSubmissionResult:
        ...

    def preview_option_order(self, order: OptionOrderRequest) -> OrderPreviewResult:
        ...

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        ...

    def get_account_balance(self) -> AccountBalanceSnapshot:
        ...

    def get_positions(self) -> list[PositionSnapshot]:
        ...
