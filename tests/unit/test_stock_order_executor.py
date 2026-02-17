from src.models.webull_models import OrderSide, OrderType, StockOrderRequest, TimeInForce
from src.trading.orders.executor import StockOrderExecutor
from src.trading.orders.planner import StockOrderExecutionPlan
from tests.support.fakes.broker_probe import BrokerProbe


class FixedPlanner:
    def __init__(self, plan):
        self._plan = plan

    def plan(self):
        return self._plan


def test_executor_submits_market_order_once():
    broker = BrokerProbe(quote=100.0)
    planner = FixedPlanner(
        StockOrderExecutionPlan(
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            extended_hours_trading=False,
            limit_buffer_bps=50.0,
            reason="regular_session_market_order",
        )
    )
    executor = StockOrderExecutor(broker, planner)
    base_order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    executor.execute(base_order, weighting=None)

    assert len(broker.orders) == 1
    submitted = broker.orders[0][0]
    assert submitted.order_type == "MARKET"
    assert submitted.time_in_force == "DAY"


def test_executor_submits_buffered_limit_order_once():
    broker = BrokerProbe(quote=100.0)
    planner = FixedPlanner(
        StockOrderExecutionPlan(
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            extended_hours_trading=False,
            limit_buffer_bps=50.0,
            reason="off_hours_queued_limit_order",
        )
    )
    executor = StockOrderExecutor(broker, planner)
    base_order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    executor.execute(base_order, weighting=None)

    assert len(broker.orders) == 1
    submitted = broker.orders[0][0]
    assert submitted.order_type == "LIMIT"
    assert submitted.time_in_force == "GTC"
    assert submitted.limit_price == 100.5

