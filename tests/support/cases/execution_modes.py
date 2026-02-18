from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Tuple


@dataclass(frozen=True)
class ExecutionModeCase:
    name: str
    market_open: bool
    now: datetime
    config: Dict[str, object]
    expected_order_type: str
    expected_time_in_force: str
    expected_reason: str
    expected_limit_buffer_bps: float


EXECUTION_MODE_CASES: Tuple[ExecutionModeCase, ...] = (
    ExecutionModeCase(
        name="regular_session_market_order",
        market_open=True,
        now=datetime(2026, 2, 17, 11, 0, 0),
        config={
            "use_market_orders": True,
            "queue_when_closed": True,
            "time_in_force": "DAY",
            "queue_time_in_force": "GTC",
            "extended_hours_trading": False,
            "out_of_hours_limit_buffer_bps": 50.0,
        },
        expected_order_type="MARKET",
        expected_time_in_force="DAY",
        expected_reason="regular_session_market_order",
        expected_limit_buffer_bps=50.0,
    ),
    ExecutionModeCase(
        name="off_hours_queued_limit_order",
        market_open=False,
        now=datetime(2026, 2, 17, 20, 0, 0),
        config={
            "use_market_orders": True,
            "queue_when_closed": True,
            "time_in_force": "DAY",
            "queue_time_in_force": "GTC",
            "extended_hours_trading": False,
            "out_of_hours_limit_buffer_bps": 75.0,
        },
        expected_order_type="LIMIT",
        expected_time_in_force="GTC",
        expected_reason="off_hours_queued_limit_order",
        expected_limit_buffer_bps=75.0,
    ),
    ExecutionModeCase(
        name="off_hours_queue_disabled_market_order",
        market_open=False,
        now=datetime(2026, 2, 17, 20, 0, 0),
        config={
            "use_market_orders": True,
            "queue_when_closed": False,
            "time_in_force": "DAY",
            "queue_time_in_force": "GTC",
            "extended_hours_trading": False,
            "out_of_hours_limit_buffer_bps": 50.0,
        },
        expected_order_type="MARKET",
        expected_time_in_force="DAY",
        expected_reason="off_hours_queue_disabled_market_order",
        expected_limit_buffer_bps=50.0,
    ),
    ExecutionModeCase(
        name="config_forced_limit_order",
        market_open=True,
        now=datetime(2026, 2, 17, 11, 0, 0),
        config={
            "use_market_orders": False,
            "queue_when_closed": True,
            "time_in_force": "DAY",
            "queue_time_in_force": "GTC",
            "extended_hours_trading": False,
            "out_of_hours_limit_buffer_bps": 50.0,
        },
        expected_order_type="LIMIT",
        expected_time_in_force="DAY",
        expected_reason="config_forced_limit_order",
        expected_limit_buffer_bps=50.0,
    ),
)

