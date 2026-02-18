from unittest.mock import MagicMock

from src.models.parser_models import ParsedSignal
from src.trading.orders import OptionOrderExecutor, SignalOrderRouter, StockOrderExecutor
from src.trading.orders.contracts import OrderType, TimeInForce
from src.trading.orders.planner import StockOrderExecutionPlan
from tests.support.fakes.broker_probe import BrokerProbe

def test_router_executes_stock_and_option_vehicles():
    broker = BrokerProbe()
    planner = MagicMock()
    planner.plan.return_value = StockOrderExecutionPlan(
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        extended_hours_trading=False,
        limit_buffer_bps=50.0,
        reason="regular_session_market_order",
    )
    stock_executor = StockOrderExecutor(broker, planner)
    option_executor = OptionOrderExecutor(broker)
    router = SignalOrderRouter(broker, stock_executor, option_executor)

    signal = ParsedSignal.model_validate(
        {
            "ticker": "AAPL",
            "action": "BUY",
            "confidence": 0.9,
            "vehicles": [
                {"type": "STOCK", "enabled": True, "intent": "EXECUTE", "side": "BUY"},
                {
                    "type": "OPTION",
                    "enabled": True,
                    "intent": "EXECUTE",
                    "side": "BUY",
                    "option_type": "CALL",
                    "strike": 210,
                    "expiry": "2026-03-20",
                    "quantity_hint": 2,
                },
            ],
        }
    )

    router.execute_signal(signal)

    assert len(broker.orders) == 1
    assert len(broker.option_orders) == 1
    assert broker.option_orders[0].quantity == 2


def test_router_skips_invalid_option_vehicle_but_executes_stock():
    broker = BrokerProbe()
    planner = MagicMock()
    planner.plan.return_value = StockOrderExecutionPlan(
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        extended_hours_trading=False,
        limit_buffer_bps=50.0,
        reason="regular_session_market_order",
    )
    stock_executor = StockOrderExecutor(broker, planner)
    option_executor = OptionOrderExecutor(broker)
    router = SignalOrderRouter(broker, stock_executor, option_executor)

    signal = ParsedSignal.model_validate(
        {
            "ticker": "TSLA",
            "action": "BUY",
            "confidence": 0.9,
            "vehicles": [
                {"type": "STOCK", "enabled": True, "intent": "EXECUTE", "side": "BUY"},
                {
                    "type": "OPTION",
                    "enabled": True,
                    "intent": "EXECUTE",
                    "side": "BUY",
                    "option_type": "CALL",
                    "expiry": "2026-03-20",
                },
            ],
        }
    )

    router.execute_signal(signal)

    assert len(broker.orders) == 1
    assert broker.option_orders == []


def test_router_skips_option_when_capability_is_disabled():
    broker = BrokerProbe(supports_options=False)
    planner = MagicMock()
    planner.plan.return_value = StockOrderExecutionPlan(
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        extended_hours_trading=False,
        limit_buffer_bps=50.0,
        reason="regular_session_market_order",
    )
    stock_executor = StockOrderExecutor(broker, planner)
    option_executor = OptionOrderExecutor(broker)
    router = SignalOrderRouter(broker, stock_executor, option_executor)

    signal = ParsedSignal.model_validate(
        {
            "ticker": "NVDA",
            "action": "BUY",
            "confidence": 0.9,
            "vehicles": [
                {"type": "STOCK", "enabled": True, "intent": "EXECUTE", "side": "BUY"},
                {
                    "type": "OPTION",
                    "enabled": True,
                    "intent": "EXECUTE",
                    "side": "BUY",
                    "option_type": "CALL",
                    "strike": 150,
                    "expiry": "2026-03-20",
                },
            ],
        }
    )

    router.execute_signal(signal)

    assert len(broker.orders) == 1
    assert broker.option_orders == []
