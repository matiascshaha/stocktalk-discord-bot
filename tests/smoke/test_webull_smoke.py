import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from config.settings import CHANNEL_ID
from src.discord_client import StockMonitorClient
from src.models.webull_models import OptionLeg, OptionOrderRequest, OptionType, OrderSide, OrderType, StockOrderRequest, TimeInForce
from tests.support.artifacts import append_smoke_check
from tests.support.factories.discord_messages import build_message
from tests.support.payloads.signals import build_signal_payload
from tests.support.webull_smoke_helpers import (
    KNOWN_WEBULL_WRITE_XFAIL_MARKERS,
    REPORT_PATH,
    build_webull_smoke_trader,
    next_weekly_expiry,
    require_webull_enabled,
)


@pytest.mark.smoke
@pytest.mark.live
def test_webull_read_smoke_login(broker_matrix):
    require_webull_enabled(broker_matrix)
    if os.getenv("TEST_WEBULL_READ", "0") != "1":
        pytest.skip("TEST_WEBULL_READ != 1")

    trader = build_webull_smoke_trader()
    error = None
    ok = False
    account_id = None
    try:
        account_id = trader.resolve_account_id()
        ok = True
    except Exception as exc:  # pragma: no cover - live smoke diagnostic
        error = str(exc)
    details = {
        "paper_trade": trader.paper_trade,
        "region": trader.region,
        "endpoint": trader._get_endpoint(),
        "request_class": "account_v2.get_account_list",
        "account_id_masked": trader._mask_id(account_id) if account_id else None,
        "error": error,
    }
    append_smoke_check(REPORT_PATH, "webull_read_login", "passed" if ok else "failed", details)
    assert ok is True


@pytest.mark.smoke
@pytest.mark.live
def test_webull_read_smoke_balance_and_instrument(broker_matrix):
    require_webull_enabled(broker_matrix)
    if os.getenv("TEST_WEBULL_READ", "0") != "1":
        pytest.skip("TEST_WEBULL_READ != 1")

    trader = build_webull_smoke_trader()
    try:
        account_id = trader.resolve_account_id()
        balance = trader.get_account_balance()
        instruments = trader.get_instrument("AAPL")
    except Exception as exc:
        details = {
            "paper_trade": trader.paper_trade,
            "region": trader.region,
            "endpoint": trader._get_endpoint(),
            "request_class": "account.get_account_balance + instrument.get_instrument",
            "error": str(exc),
        }
        append_smoke_check(REPORT_PATH, "webull_read_balance_instrument", "failed", details)
        raise

    details = {
        "paper_trade": trader.paper_trade,
        "region": trader.region,
        "endpoint": trader._get_endpoint(),
        "account_id_masked": trader._mask_id(account_id),
        "balance_keys": sorted(list(balance.keys()))[:8],
        "instrument_count": len(instruments),
        "request_class": "account.get_account_balance + instrument.get_instrument",
    }
    append_smoke_check(REPORT_PATH, "webull_read_balance_instrument", "passed", details)
    assert len(instruments) > 0


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


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.webull_write
def test_webull_write_smoke_discord_runtime_option_path_opt_in_non_blocking(broker_matrix):
    require_webull_enabled(broker_matrix)
    if os.getenv("TEST_WEBULL_WRITE", "0") != "1":
        pytest.skip("TEST_WEBULL_WRITE != 1")
    if not CHANNEL_ID:
        pytest.skip("CHANNEL_ID is not configured")

    trader = build_webull_smoke_trader()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999999)
    client.notifier.notify = MagicMock()

    option_vehicle = {
        "type": "OPTION",
        "enabled": True,
        "intent": "EXECUTE",
        "side": "BUY",
        "option_type": "CALL",
        "strike": 400.0,
        "expiry": next_weekly_expiry(days_ahead=21),
        "quantity_hint": 1,
    }
    client.parser.parse = MagicMock(
        return_value={
            "signals": [build_signal_payload("TSLA", "BUY", weight_percent=None, vehicles=[option_vehicle])],
            "meta": {"status": "ok"},
        }
    )

    call_state = {"called": False, "result": None, "error": None}
    original_place_option_order = trader.place_option_order

    def wrapped_place_option_order(order, skip_preview=False):
        call_state["called"] = True
        try:
            result = original_place_option_order(order, skip_preview=skip_preview)
            call_state["result"] = result
            return result
        except Exception as exc:  # pragma: no cover - live smoke diagnostic
            call_state["error"] = str(exc)
            raise

    trader.place_option_order = wrapped_place_option_order

    import asyncio

    message = build_message("runtime option smoke", author_id=321, channel_id=CHANNEL_ID)
    asyncio.run(client.on_message(message))

    if not call_state["called"]:
        details = {
            "paper_trade": trader.paper_trade,
            "endpoint": trader._get_endpoint(),
            "request_class": "discord_client.on_message -> order.place_option",
            "error": "Runtime option path did not invoke place_option_order",
        }
        append_smoke_check(REPORT_PATH, "webull_write_discord_runtime_option_path", "failed", details)
        pytest.fail(details["error"])

    if call_state["error"]:
        error = call_state["error"]
        details = {
            "paper_trade": trader.paper_trade,
            "endpoint": trader._get_endpoint(),
            "request_class": "discord_client.on_message -> order.place_option",
            "error": error,
        }
        matched_marker = next((marker for marker in KNOWN_WEBULL_WRITE_XFAIL_MARKERS if marker in error), None)
        if matched_marker:
            details["non_blocking_reason"] = matched_marker
            append_smoke_check(REPORT_PATH, "webull_write_discord_runtime_option_path", "xfailed", details)
            pytest.xfail(f"Discord runtime option write non-deterministic in this environment: {error}")

        append_smoke_check(REPORT_PATH, "webull_write_discord_runtime_option_path", "failed", details)
        pytest.fail(error)

    result = call_state["result"]
    details = {
        "paper_trade": trader.paper_trade,
        "endpoint": trader._get_endpoint(),
        "request_class": "discord_client.on_message -> order.place_option",
        "result_keys": sorted(list(result.keys()))[:8] if isinstance(result, dict) else [],
    }
    append_smoke_check(REPORT_PATH, "webull_write_discord_runtime_option_path", "passed", details)
    assert isinstance(result, dict)
