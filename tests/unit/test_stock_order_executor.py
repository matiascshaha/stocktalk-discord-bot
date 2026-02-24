from unittest.mock import MagicMock

import pytest
from types import SimpleNamespace

from src.models.webull_models import OrderSide, OrderType, StockOrderRequest, TimeInForce
from src.trading.contracts import StockOrder
from src.trading.orders.executor import StockOrderExecutor, _enum_value
from src.trading.orders.planner import StockOrderExecutionPlan
from tests.support.fakes.broker_probe import BrokerProbe

pytestmark = [pytest.mark.unit]


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


def test_executor_rejects_both_weighting_and_sizing_percent():
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

    with pytest.raises(ValueError, match="Pass only one of weighting or sizing_percent"):
        executor.execute(base_order, weighting=1.0, sizing_percent=1.0)


def test_executor_raises_when_limit_reference_price_unavailable():
    broker = BrokerProbe(quote=None)
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

    with pytest.raises(ValueError, match="Unable to fetch executable reference price"):
        executor.execute(base_order)


def test_executor_uses_configured_buy_limit_price_when_quote_unavailable():
    broker = BrokerProbe(quote=None)
    planner = MagicMock()
    planner.plan.return_value = StockOrderExecutionPlan(
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        extended_hours_trading=False,
        limit_buffer_bps=50.0,
        reason="off_hours_queued_limit_order",
        buy_limit_price_without_quote=1.0,
    )
    executor = StockOrderExecutor(broker, planner)
    base_order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    executor.execute(base_order)

    assert len(broker.orders) == 1
    submitted = broker.orders[0][0]
    assert submitted.order_type == "LIMIT"
    assert submitted.limit_price == 1.0


def test_executor_normalizes_dict_order():
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

    executor.execute({"symbol": "aapl", "side": "BUY", "quantity": 2})

    submitted = broker.orders[0][0]
    assert submitted.symbol == "AAPL"
    assert submitted.side == "BUY"
    assert submitted.quantity == 2


def test_executor_normalizes_object_with_model_dump():
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
    wrapped_order = MagicMock()
    wrapped_order.model_dump.return_value = {"symbol": "$msft", "side": "SELL", "quantity": 1}

    executor.execute(wrapped_order)

    submitted = broker.orders[0][0]
    assert submitted.symbol == "MSFT"
    assert submitted.side == "SELL"


def test_executor_normalizes_attribute_based_object():
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
    attribute_order = SimpleNamespace(
        symbol="TSLA",
        side="BUY",
        quantity=3,
        order_type="MARKET",
        limit_price=None,
        time_in_force="DAY",
        trading_session="CORE",
        extended_hours_trading=False,
    )

    executor.execute(attribute_order)

    submitted = broker.orders[0][0]
    assert submitted.symbol == "TSLA"
    assert submitted.quantity == 3


def test_executor_accepts_already_normalized_stock_order():
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
    order = StockOrder(symbol="NVDA", side="BUY", quantity=1)

    executor.execute(order)

    submitted = broker.orders[0][0]
    assert submitted.symbol == "NVDA"


def test_enum_value_normalizes_input():
    assert _enum_value(" buy ") == "BUY"
