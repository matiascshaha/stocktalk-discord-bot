import pytest

import src.trading.orders.planner as order_planner_module
from src.brokerages.webull.broker import WebullBroker
from src.models.webull_models import StockOrderRequest
from src.trading.contracts import StockOrder
from src.trading.orders.executor import StockOrderExecutor
from src.trading.orders.planner import StockOrderExecutionPlanner
from tests.support.fakes.quote_aware_trader_probe import QuoteAwareTraderProbe


pytestmark = [pytest.mark.integration, pytest.mark.broker, pytest.mark.broker_webull]


def test_quote_execute_uses_l1_ask_for_buy_and_submits_limit_order(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: False)
    trader = QuoteAwareTraderProbe(
        quote_payload=[{"asks": [{"price": "101.25"}], "bids": [{"price": "101.20"}]}],
    )
    broker = WebullBroker(trader)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": True,
            "queue_time_in_force": "GTC",
            "out_of_hours_limit_buffer_bps": 50.0,
        }
    )
    executor = StockOrderExecutor(broker, planner)

    result = executor.execute(StockOrder(symbol="AAPL", side="BUY", quantity=1))

    assert result.success is True
    assert [entry[0] for entry in trader.calls] == ["get_stock_quotes", "place_stock_order"]
    assert len(trader.placed_orders) == 1
    placed = trader.placed_orders[0][0]
    assert isinstance(placed, StockOrderRequest)
    assert placed.order_type == "LIMIT"
    assert placed.time_in_force == "GTC"
    assert placed.limit_price == pytest.approx(101.76)


def test_quote_execute_uses_l1_bid_for_sell_and_submits_limit_order(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: False)
    trader = QuoteAwareTraderProbe(
        quote_payload=[{"asks": [{"price": "101.25"}], "bids": [{"price": "101.20"}]}],
    )
    broker = WebullBroker(trader)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": True,
            "queue_time_in_force": "GTC",
            "out_of_hours_limit_buffer_bps": 50.0,
        }
    )
    executor = StockOrderExecutor(broker, planner)

    executor.execute(StockOrder(symbol="AAPL", side="SELL", quantity=1))

    assert [entry[0] for entry in trader.calls] == ["get_stock_quotes", "place_stock_order"]
    assert len(trader.placed_orders) == 1
    placed = trader.placed_orders[0][0]
    assert placed.side == "SELL"
    assert placed.limit_price == pytest.approx(100.69)


def test_quote_execute_falls_back_to_snapshot_on_permission_errors(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: False)
    trader = QuoteAwareTraderProbe(
        quote_error=RuntimeError("HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."),
        snapshot_price=100.0,
    )
    broker = WebullBroker(trader)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": True,
            "queue_time_in_force": "GTC",
            "out_of_hours_limit_buffer_bps": 50.0,
        }
    )
    executor = StockOrderExecutor(broker, planner)

    executor.execute(StockOrder(symbol="AAPL", side="BUY", quantity=1))

    assert [entry[0] for entry in trader.calls] == [
        "get_stock_quotes",
        "get_current_stock_quote",
        "place_stock_order",
    ]
    assert len(trader.placed_orders) == 1
    placed = trader.placed_orders[0][0]
    assert placed.limit_price == pytest.approx(100.5)


def test_quote_execute_falls_back_to_instrument_when_snapshot_is_unavailable(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: False)
    trader = QuoteAwareTraderProbe(
        quote_error=RuntimeError("HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."),
        snapshot_error=RuntimeError("HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."),
        instrument_payload=[{"last_price": "99.40"}],
    )
    broker = WebullBroker(trader)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": True,
            "queue_time_in_force": "GTC",
            "out_of_hours_limit_buffer_bps": 50.0,
        }
    )
    executor = StockOrderExecutor(broker, planner)

    executor.execute(StockOrder(symbol="AAPL", side="BUY", quantity=1))

    assert [entry[0] for entry in trader.calls] == [
        "get_stock_quotes",
        "get_current_stock_quote",
        "get_instrument",
        "place_stock_order",
    ]
    assert len(trader.placed_orders) == 1
    placed = trader.placed_orders[0][0]
    assert placed.limit_price == pytest.approx(99.9)


def test_quote_execute_uses_fallback_buy_limit_price_when_quotes_are_unavailable(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: False)
    trader = QuoteAwareTraderProbe(
        quote_payload=[],
        snapshot_price=None,
        instrument_payload=[{"instrument_id": "AAPL_ID"}],
    )
    broker = WebullBroker(trader)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": True,
            "queue_time_in_force": "GTC",
            "out_of_hours_limit_buffer_bps": 50.0,
        }
    )
    executor = StockOrderExecutor(broker, planner)

    executor.execute(StockOrder(symbol="AAPL", side="BUY", quantity=1))

    assert [entry[0] for entry in trader.calls] == [
        "get_stock_quotes",
        "get_current_stock_quote",
        "get_instrument",
        "place_stock_order",
    ]
    assert len(trader.placed_orders) == 1
    placed = trader.placed_orders[0][0]
    assert placed.limit_price == pytest.approx(1.0)


def test_quote_execute_raises_non_permission_quote_errors_without_submit(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: False)
    trader = QuoteAwareTraderProbe(
        quote_error=RuntimeError("service unavailable"),
    )
    broker = WebullBroker(trader)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": True,
            "queue_time_in_force": "GTC",
            "out_of_hours_limit_buffer_bps": 50.0,
        }
    )
    executor = StockOrderExecutor(broker, planner)

    with pytest.raises(RuntimeError, match="service unavailable"):
        executor.execute(StockOrder(symbol="AAPL", side="BUY", quantity=1))

    assert [entry[0] for entry in trader.calls] == ["get_stock_quotes"]
    assert trader.placed_orders == []
