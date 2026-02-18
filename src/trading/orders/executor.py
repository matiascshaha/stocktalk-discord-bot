"""Stock order executor that delegates broker calls after planning."""

from typing import Any, Dict, Optional

from src.brokerages.base import Brokerage
from src.models.webull_models import OrderType, StockOrderRequest
from src.trading.orders.planner import StockOrderExecutionPlan, StockOrderExecutionPlanner
from src.trading.orders.pricing import compute_buffered_limit_price
from src.utils.logger import setup_logger


logger = setup_logger("stock_order_executor")


class StockOrderExecutor:
    """Execute stock orders using a single pre-submit plan."""

    def __init__(self, broker: Brokerage, planner: StockOrderExecutionPlanner):
        self._broker = broker
        self._planner = planner

    def execute(
        self,
        order: StockOrderRequest,
        weighting: Optional[float] = None,
        notional_dollar_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        plan = self._planner.plan()
        final_order = self._build_order(order, plan)
        logger.info(
            "Executing %s %s qty=%s as %s (reason=%s, tif=%s, ext_hours=%s)",
            final_order.side,
            final_order.symbol,
            final_order.quantity,
            final_order.order_type,
            plan.reason,
            final_order.time_in_force,
            final_order.extended_hours_trading,
        )
        if notional_dollar_amount is None:
            return self._broker.place_stock_order(final_order, weighting=weighting)

        try:
            return self._broker.place_stock_order(
                final_order,
                weighting=weighting,
                notional_dollar_amount=notional_dollar_amount,
            )
        except TypeError:
            logger.warning("Broker does not accept notional_dollar_amount; falling back to weighting-only call")
            return self._broker.place_stock_order(final_order, weighting=weighting)

    def _build_order(self, order: StockOrderRequest, plan: StockOrderExecutionPlan) -> StockOrderRequest:
        if plan.order_type == OrderType.MARKET:
            return StockOrderRequest(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                order_type=OrderType.MARKET,
                time_in_force=plan.time_in_force,
                extended_hours_trading=plan.extended_hours_trading,
                trading_session=order.trading_session,
            )

        quote = self._broker.get_limit_reference_price(order.symbol, str(order.side))
        if quote is None:
            raise ValueError(f"Unable to fetch executable reference price for symbol {order.symbol}")

        limit_price = compute_buffered_limit_price(str(order.side), float(quote), plan.limit_buffer_bps)
        return StockOrderRequest(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            order_type=OrderType.LIMIT,
            limit_price=limit_price,
            time_in_force=plan.time_in_force,
            extended_hours_trading=plan.extended_hours_trading,
            trading_session=order.trading_session,
        )
