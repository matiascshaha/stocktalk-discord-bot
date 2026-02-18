from unittest.mock import MagicMock

from src.models.webull_models import OrderSide, OrderType, StockOrderRequest, TimeInForce
from src.trading.orders.executor import StockOrderExecutor
from src.trading.orders.planner import StockOrderExecutionPlan
from tests.support.fakes.broker_probe import BrokerProbe


def test_executor_passes_weighting_and_notional_to_broker():
    broker = BrokerProbe(quote=100.0)
    planner = MagicMock()
    planner.plan.return_value = StockOrderExecutionPlan(
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        extended_hours_trading=False,
        limit_buffer_bps=50.0,
        reason="regular_session_market_order",
    )
    executor = StockOrderExecutor(broker, planner)
    base_order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    executor.execute(base_order, weighting=5.0, notional_dollar_amount=1000.0)

    assert len(broker.orders) == 1
    _submitted_order, weighting, notional_dollar_amount = broker.orders[0]
    assert weighting == 5.0
    assert notional_dollar_amount == 1000.0


def test_executor_submits_market_order_once():
    broker = BrokerProbe(quote=100.0)
    planner = MagicMock()
    planner.plan.return_value = StockOrderExecutionPlan(
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        extended_hours_trading=False,
        limit_buffer_bps=50.0,
        reason="regular_session_market_order",
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
    planner = MagicMock()
    planner.plan.return_value = StockOrderExecutionPlan(
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        extended_hours_trading=False,
        limit_buffer_bps=50.0,
        reason="off_hours_queued_limit_order",
    )
    executor = StockOrderExecutor(broker, planner)
    base_order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    executor.execute(base_order, weighting=None)

    assert len(broker.orders) == 1
    submitted = broker.orders[0][0]
    assert submitted.order_type == "LIMIT"
    assert submitted.time_in_force == "GTC"
    assert submitted.limit_price == 100.5
