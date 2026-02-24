from datetime import datetime

import pytest

import src.trading.orders.planner as planner_module
from src.trading.orders.planner import StockOrderExecutionPlanner
from src.trading.contracts import TimeInForce

pytestmark = [pytest.mark.unit]


def test_plan_uses_market_order_during_regular_session(monkeypatch):
    monkeypatch.setattr(planner_module, "is_regular_market_session", lambda _: True)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": True,
            "time_in_force": "DAY",
            "queue_time_in_force": "GTC",
            "extended_hours_trading": False,
            "out_of_hours_limit_buffer_bps": 50.0,
        },
        now_provider=lambda: datetime(2026, 2, 17, 11, 0, 0),
    )

    plan = planner.plan()
    assert plan.order_type == "MARKET"
    assert plan.time_in_force == "DAY"
    assert plan.reason == "regular_session_market_order"


def test_plan_uses_queued_limit_outside_hours_when_enabled(monkeypatch):
    monkeypatch.setattr(planner_module, "is_regular_market_session", lambda _: False)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": True,
            "time_in_force": "DAY",
            "queue_time_in_force": "GTC",
            "extended_hours_trading": False,
            "out_of_hours_limit_buffer_bps": 75.0,
        },
        now_provider=lambda: datetime(2026, 2, 17, 20, 0, 0),
    )

    plan = planner.plan()
    assert plan.order_type == "LIMIT"
    assert plan.time_in_force == "GTC"
    assert plan.limit_buffer_bps == 75.0
    assert plan.reason == "off_hours_queued_limit_order"


def test_plan_uses_market_outside_hours_when_queue_disabled(monkeypatch):
    monkeypatch.setattr(planner_module, "is_regular_market_session", lambda _: False)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": True,
            "queue_when_closed": False,
            "time_in_force": "DAY",
            "queue_time_in_force": "GTC",
            "extended_hours_trading": False,
            "out_of_hours_limit_buffer_bps": 50.0,
        },
        now_provider=lambda: datetime(2026, 2, 17, 20, 0, 0),
    )

    plan = planner.plan()
    assert plan.order_type == "MARKET"
    assert plan.reason == "off_hours_queue_disabled_market_order"


def test_plan_forced_limit_when_market_orders_disabled(monkeypatch):
    monkeypatch.setattr(planner_module, "is_regular_market_session", lambda _: True)
    planner = StockOrderExecutionPlanner(
        {
            "use_market_orders": False,
            "queue_when_closed": True,
            "time_in_force": "DAY",
            "queue_time_in_force": "GTC",
            "extended_hours_trading": False,
            "out_of_hours_limit_buffer_bps": 50.0,
        },
        now_provider=lambda: datetime(2026, 2, 17, 11, 0, 0),
    )

    plan = planner.plan()
    assert plan.order_type == "LIMIT"
    assert plan.time_in_force == "DAY"
    assert plan.reason == "config_forced_limit_order"


def test_resolve_time_in_force_accepts_valid_upper_and_lower():
    assert StockOrderExecutionPlanner._resolve_time_in_force("day", TimeInForce.GTC) == TimeInForce.DAY
    assert StockOrderExecutionPlanner._resolve_time_in_force(" IOC ", TimeInForce.GTC) == TimeInForce.IOC


def test_resolve_time_in_force_falls_back_to_default_for_invalid():
    assert StockOrderExecutionPlanner._resolve_time_in_force("bad", TimeInForce.FOK) == TimeInForce.FOK
    assert StockOrderExecutionPlanner._resolve_time_in_force(None, TimeInForce.GTC) == TimeInForce.GTC


def test_resolve_buffer_bps_parses_numeric_and_clamps_negative():
    assert StockOrderExecutionPlanner._resolve_buffer_bps("75.5") == 75.5
    assert StockOrderExecutionPlanner._resolve_buffer_bps(-1) == 0.0


def test_resolve_buffer_bps_uses_default_for_invalid():
    assert StockOrderExecutionPlanner._resolve_buffer_bps("bad", default=33.0) == 33.0
