"""Stock order planning based on runtime config and market session."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from src.trading.contracts import OrderType, TimeInForce
from src.trading.orders.market_hours import is_regular_market_session


@dataclass(frozen=True)
class StockOrderExecutionPlan:
    order_type: OrderType
    time_in_force: TimeInForce
    extended_hours_trading: bool
    limit_buffer_bps: float
    reason: str
    buy_limit_price_without_quote: Optional[float] = None


class StockOrderExecutionPlanner:
    """Choose order type (market/limit) before execution in a single pass."""

    def __init__(
        self,
        trading_config: Dict[str, Any],
        now_provider: Optional[Callable[[], datetime]] = None,
    ):
        self._config = trading_config
        self._now_provider = now_provider or datetime.now

    def plan(self) -> StockOrderExecutionPlan:
        use_market_orders = bool(self._config.get("use_market_orders", True))
        queue_when_closed = bool(self._config.get("queue_when_closed", True))
        extended_hours = bool(self._config.get("extended_hours_trading", False))
        limit_buffer_bps = self._resolve_buffer_bps(self._config.get("out_of_hours_limit_buffer_bps"), default=50.0)
        buy_limit_price_without_quote = self._resolve_positive_float(
            self._config.get("buy_limit_price_without_quote"),
            default=1.0,
        )

        regular_tif = self._resolve_time_in_force(self._config.get("time_in_force"), TimeInForce.DAY)
        queue_tif = self._resolve_time_in_force(self._config.get("queue_time_in_force"), TimeInForce.GTC)

        market_open = is_regular_market_session(self._now_provider())

        if use_market_orders and market_open:
            return StockOrderExecutionPlan(
                order_type=OrderType.MARKET,
                time_in_force=regular_tif,
                extended_hours_trading=extended_hours,
                limit_buffer_bps=limit_buffer_bps,
                buy_limit_price_without_quote=buy_limit_price_without_quote,
                reason="regular_session_market_order",
            )

        if use_market_orders and queue_when_closed:
            return StockOrderExecutionPlan(
                order_type=OrderType.LIMIT,
                time_in_force=queue_tif,
                extended_hours_trading=extended_hours,
                limit_buffer_bps=limit_buffer_bps,
                buy_limit_price_without_quote=buy_limit_price_without_quote,
                reason="off_hours_queued_limit_order",
            )

        if not use_market_orders:
            return StockOrderExecutionPlan(
                order_type=OrderType.LIMIT,
                time_in_force=regular_tif,
                extended_hours_trading=extended_hours,
                limit_buffer_bps=limit_buffer_bps,
                buy_limit_price_without_quote=buy_limit_price_without_quote,
                reason="config_forced_limit_order",
            )

        return StockOrderExecutionPlan(
            order_type=OrderType.MARKET,
            time_in_force=regular_tif,
            extended_hours_trading=extended_hours,
            limit_buffer_bps=limit_buffer_bps,
            buy_limit_price_without_quote=buy_limit_price_without_quote,
            reason="off_hours_queue_disabled_market_order",
        )

    @staticmethod
    def _resolve_time_in_force(raw_value: Any, default: TimeInForce) -> TimeInForce:
        value = str(raw_value or "").strip().upper()
        valid = {
            TimeInForce.DAY.value,
            TimeInForce.GTC.value,
            TimeInForce.IOC.value,
            TimeInForce.FOK.value,
        }
        if value in valid:
            return TimeInForce(value)
        return default

    @staticmethod
    def _resolve_buffer_bps(raw_value: Any, default: float = 50.0) -> float:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return default
        return max(0.0, value)

    @staticmethod
    def _resolve_positive_float(raw_value: Any, default: Optional[float] = None) -> Optional[float]:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return default
        if value <= 0:
            return default
        return value
