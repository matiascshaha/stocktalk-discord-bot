"""Webull brokerage adapter for runtime order execution."""

from typing import Optional

from src.brokerages.webull.quote_service import resolve_limit_reference_price
from src.brokerages.webull.capabilities import WEBULL_CAPABILITIES
from src.brokerages.webull.mappers import (
    map_balance_snapshot,
    map_positions,
    map_preview_result,
    map_submission_result,
    to_webull_option_order,
    to_webull_stock_order,
)
from src.trading.orders.contracts import (
    AccountBalanceSnapshot,
    BrokerageCapabilities,
    OptionOrderRequest,
    OrderPreviewResult,
    OrderSubmissionResult,
    PositionSnapshot,
    StockOrderRequest,
    VehicleAssetType,
)
from src.webull_trader import WebullTrader


class WebullBroker:
    """Thin adapter exposing the Brokerage interface over WebullTrader."""

    def __init__(self, trader: WebullTrader):
        self._trader = trader

    def get_capabilities(self) -> BrokerageCapabilities:
        return WEBULL_CAPABILITIES

    def place_stock_order(self, order: StockOrderRequest, weighting: Optional[float] = None) -> OrderSubmissionResult:
        payload = self._trader.place_stock_order(to_webull_stock_order(order), weighting=weighting)
        return map_submission_result(payload, broker="webull", asset_type=VehicleAssetType.STOCK)

    def preview_stock_order(self, order: StockOrderRequest) -> OrderPreviewResult:
        preview = self._trader.preview_stock_order(to_webull_stock_order(order))
        payload = preview.model_dump(exclude_none=True) if hasattr(preview, "model_dump") else {}
        return map_preview_result(payload, broker="webull", asset_type=VehicleAssetType.STOCK)

    def place_option_order(self, order: OptionOrderRequest) -> OrderSubmissionResult:
        payload = self._trader.place_option_order(to_webull_option_order(order))
        return map_submission_result(payload, broker="webull", asset_type=VehicleAssetType.OPTION)

    def preview_option_order(self, order: OptionOrderRequest) -> OrderPreviewResult:
        preview = self._trader.preview_option_order(to_webull_option_order(order))
        payload = preview.model_dump(exclude_none=True) if hasattr(preview, "model_dump") else {}
        return map_preview_result(payload, broker="webull", asset_type=VehicleAssetType.OPTION)

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        return resolve_limit_reference_price(self._trader, symbol, side)

    def get_account_balance(self) -> AccountBalanceSnapshot:
        payload = self._trader.get_account_balance()
        return map_balance_snapshot(payload, broker="webull")

    def get_positions(self) -> list[PositionSnapshot]:
        payload = self._trader.get_account_positions()
        return map_positions(payload, broker="webull")
