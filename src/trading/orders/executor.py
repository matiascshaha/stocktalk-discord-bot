"""Stock order executor that delegates broker calls after planning."""

from typing import Optional

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

    def execute(self, order: StockOrder, sizing_percent: Optional[float] = None) -> OrderResult:
        plan = self._planner.plan()
        final_order = self._build_order(order, plan)
        logger.info(
            "Executing %s %s qty=%s as %s (reason=%s, tif=%s, ext_hours=%s)",
            final_order.side.value,
            final_order.symbol,
            final_order.quantity,
            final_order.order_type.value,
            plan.reason,
            final_order.time_in_force.value,
            final_order.extended_hours_trading,
        )
        return self._broker.place_stock_order(final_order, sizing_percent=sizing_percent)

    def _build_order(self, order: StockOrder, plan: StockOrderExecutionPlan) -> StockOrder:
        if plan.order_type == OrderType.MARKET:
            return StockOrder(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                order_type=OrderType.MARKET,
                time_in_force=plan.time_in_force,
                extended_hours_trading=plan.extended_hours_trading,
                trading_session=order.trading_session,
            )

        quote = self._broker.get_limit_reference_price(order.symbol, order.side.value)
        if quote is None:
            raise ValueError(f"Unable to fetch executable reference price for symbol {order.symbol}")

        limit_price = compute_buffered_limit_price(order.side.value, float(quote), plan.limit_buffer_bps)
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
