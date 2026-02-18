"""Stock order executor that delegates broker calls after planning."""

from typing import Any, Optional

from src.brokerages.ports import TradingBrokerPort
from src.trading.contracts import OrderResult, OrderType, StockOrder
from src.trading.orders.planner import StockOrderExecutionPlan, StockOrderExecutionPlanner
from src.trading.orders.pricing import compute_buffered_limit_price
from src.utils.logger import setup_logger


logger = setup_logger("stock_order_executor")


class StockOrderExecutor:
    """Execute stock orders using a single pre-submit plan."""

    def __init__(self, broker: TradingBrokerPort, planner: StockOrderExecutionPlanner):
        self._broker = broker
        self._planner = planner

    def execute(
        self,
        order: Any,
        weighting: Optional[float] = None,
        sizing_percent: Optional[float] = None,
    ) -> OrderResult:
        if weighting is not None and sizing_percent is not None:
            raise ValueError("Pass only one of weighting or sizing_percent")

        effective_weighting = weighting if weighting is not None else sizing_percent
        normalized_order = self._normalize_order(order)
        plan = self._planner.plan()
        final_order = self._build_order(normalized_order, plan)
        logger.info(
            "Executing %s %s qty=%s as %s (reason=%s, tif=%s, ext_hours=%s)",
            _enum_value(final_order.side),
            final_order.symbol,
            final_order.quantity,
            _enum_value(final_order.order_type),
            plan.reason,
            _enum_value(final_order.time_in_force),
            final_order.extended_hours_trading,
        )
        return self._broker.place_stock_order(final_order, weighting=effective_weighting)

    def _build_order(self, order: StockOrder, plan: StockOrderExecutionPlan) -> StockOrder:
        if _enum_value(plan.order_type) == OrderType.MARKET.value:
            return StockOrder(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                order_type=OrderType.MARKET,
                time_in_force=plan.time_in_force,
                extended_hours_trading=plan.extended_hours_trading,
                trading_session=order.trading_session,
            )

        side = _enum_value(order.side)
        quote = self._broker.get_limit_reference_price(order.symbol, side)
        if quote is None:
            raise ValueError(f"Unable to fetch executable reference price for symbol {order.symbol}")

        limit_price = compute_buffered_limit_price(side, float(quote), plan.limit_buffer_bps)
        return StockOrder(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            order_type=OrderType.LIMIT,
            limit_price=limit_price,
            time_in_force=plan.time_in_force,
            extended_hours_trading=plan.extended_hours_trading,
            trading_session=order.trading_session,
        )

    def _normalize_order(self, order: Any) -> StockOrder:
        if isinstance(order, StockOrder):
            return order
        if isinstance(order, dict):
            return StockOrder.model_validate(order)
        if hasattr(order, "model_dump"):
            return StockOrder.model_validate(order.model_dump(exclude_none=True))

        payload = {
            "symbol": getattr(order, "symbol", None),
            "side": getattr(order, "side", None),
            "quantity": getattr(order, "quantity", None),
            "order_type": getattr(order, "order_type", None),
            "limit_price": getattr(order, "limit_price", None),
            "time_in_force": getattr(order, "time_in_force", None),
            "trading_session": getattr(order, "trading_session", None),
            "extended_hours_trading": getattr(order, "extended_hours_trading", False),
        }
        return StockOrder.model_validate(payload)


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value or "")).upper().strip()
