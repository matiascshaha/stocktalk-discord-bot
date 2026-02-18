import os

import pytest

from src.models.webull_models import OptionLeg, OptionOrderRequest, OptionType, OrderSide, OrderType, StockOrderRequest, TimeInForce
from tests.testkit.helpers.artifacts import append_smoke_check
from tests.testkit.helpers.webull_smoke_helpers import (
    KNOWN_WEBULL_WRITE_XFAIL_MARKERS,
    REPORT_PATH,
    build_webull_smoke_trader,
    next_weekly_expiry,
    require_webull_enabled,
)


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.webull_write
def test_webull_write_smoke_stock_order_opt_in(broker_matrix):
    require_webull_enabled(broker_matrix)
    if os.getenv("TEST_WEBULL_WRITE", "0") != "1":
        pytest.skip("TEST_WEBULL_WRITE != 1")

    trader = build_webull_smoke_trader()
    order = StockOrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        order_type=OrderType.LIMIT,
        limit_price=1.0,
        time_in_force=TimeInForce.DAY,
    )

    try:
        result = trader.place_stock_order(order)
    except Exception as exc:
        error = str(exc)
        details = {
            "paper_trade": trader.paper_trade,
            "endpoint": trader._get_endpoint(),
            "request_class": "order.place_order",
            "error": error,
        }
        matched_marker = next((marker for marker in KNOWN_WEBULL_WRITE_XFAIL_MARKERS if marker in error), None)
        if matched_marker:
            details["non_blocking_reason"] = matched_marker
            append_smoke_check(REPORT_PATH, "webull_write_stock_order", "xfailed", details)
            pytest.xfail(f"Stock write non-deterministic in this environment: {error}")

        append_smoke_check(REPORT_PATH, "webull_write_stock_order", "failed", details)
        raise

    details = {
        "paper_trade": trader.paper_trade,
        "endpoint": trader._get_endpoint(),
        "request_class": "order.place_order",
        "result_keys": sorted(list(result.keys()))[:8] if isinstance(result, dict) else [],
    }
    append_smoke_check(REPORT_PATH, "webull_write_stock_order", "passed", details)
    assert isinstance(result, dict)


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.webull_write
def test_webull_write_smoke_option_order_opt_in_non_blocking(broker_matrix):
    require_webull_enabled(broker_matrix)
    if os.getenv("TEST_WEBULL_WRITE", "0") != "1":
        pytest.skip("TEST_WEBULL_WRITE != 1")

    trader = build_webull_smoke_trader()
    order = OptionOrderRequest(
        order_type=OrderType.LIMIT,
        quantity="1",
        limit_price="1.00",
        side=OrderSide.BUY,
        time_in_force=TimeInForce.GTC,
        legs=[
            OptionLeg(
                side=OrderSide.BUY,
                quantity="1",
                symbol="TSLA",
                strike_price="400",
                option_expire_date=next_weekly_expiry(days_ahead=21),
                option_type=OptionType.CALL,
                market="US",
            )
        ],
    )

    try:
        result = trader.place_option_order(order)
    except Exception as exc:
        details = {
            "paper_trade": trader.paper_trade,
            "endpoint": trader._get_endpoint(),
            "request_class": "order.place_option",
            "error": str(exc),
        }
        append_smoke_check(REPORT_PATH, "webull_write_option_order", "xfailed", details)
        pytest.xfail(f"Option endpoint unavailable/non-deterministic in this environment: {exc}")

    details = {
        "paper_trade": trader.paper_trade,
        "endpoint": trader._get_endpoint(),
        "request_class": "order.place_option",
        "result_keys": sorted(list(result.keys()))[:8] if isinstance(result, dict) else [],
    }
    append_smoke_check(REPORT_PATH, "webull_write_option_order", "passed", details)
    assert isinstance(result, dict)
