import pytest

import src.trading.orders.planner as planner_module
from src.trading.orders.planner import StockOrderExecutionPlanner
from tests.testkit.scenario_catalogs.execution_modes import EXECUTION_MODE_CASES


@pytest.mark.unit
@pytest.mark.feature_regression
@pytest.mark.parametrize("case", EXECUTION_MODE_CASES, ids=lambda case: case.name)
def test_plan_execution_modes(case, monkeypatch):
    monkeypatch.setattr(planner_module, "is_regular_market_session", lambda _: case.market_open)
    planner = StockOrderExecutionPlanner(case.config, now_provider=lambda: case.now)

    plan = planner.plan()

    assert plan.order_type == case.expected_order_type
    assert plan.time_in_force == case.expected_time_in_force
    assert plan.reason == case.expected_reason
    assert plan.limit_buffer_bps == case.expected_limit_buffer_bps
