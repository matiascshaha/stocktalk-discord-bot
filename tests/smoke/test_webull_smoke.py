import os
from datetime import date, timedelta
from pathlib import Path
from typing import List

import pytest

from config.settings import WEBULL_CONFIG
from src.models.webull_models import OptionLeg, OptionOrderRequest, OptionType, OrderSide, OrderType, StockOrderRequest, TimeInForce
from src.webull_trader import WebullTrader
from tests.support.artifacts import append_smoke_check


REPORT_PATH = Path("artifacts/webull_smoke_report.json")
KNOWN_WEBULL_WRITE_XFAIL_MARKERS = (
    "DAY_BUYING_POWER_INSUFFICIENT",
    "OAUTH_OPENAPI_DAY_BUYING_POWER_INSUFFICIENT",
    "CAN_NOT_TRADING_FOR_NON_TRADING_HOURS",
    "OAUTH_OPENAPI_CAN_NOT_TRADING_FOR_FIXGW_NOT_READY_NIGHT",
    "OAUTH_OPENAPI_TRADE_ORDER_NO_PERMISSION",
)


def _paper_trade_enabled() -> bool:
    raw = os.getenv("WEBULL_SMOKE_PAPER_TRADE", os.getenv("PAPER_TRADE", "true")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _require_webull_enabled(broker_matrix: List[str]) -> None:
    if "webull" not in broker_matrix:
        pytest.skip(f"Webull broker not enabled in TEST_BROKERS={','.join(broker_matrix)}")


def _next_weekly_expiry(days_ahead: int = 21) -> str:
    target = date.today() + timedelta(days=days_ahead)
    days_until_friday = (4 - target.weekday()) % 7
    expiry = target + timedelta(days=days_until_friday)
    return expiry.isoformat()


def _build_trader() -> WebullTrader:
    paper_trade = _paper_trade_enabled()

    if paper_trade:
        app_key = os.getenv("WEBULL_TEST_APP_KEY") or WEBULL_CONFIG.get("test_app_key") or os.getenv("WEBULL_APP_KEY")
        app_secret = os.getenv("WEBULL_TEST_APP_SECRET") or WEBULL_CONFIG.get("test_app_secret") or os.getenv("WEBULL_APP_SECRET")
        account_id = (
            os.getenv("WEBULL_TEST_ACCOUNT_ID")
            or WEBULL_CONFIG.get("test_account_id")
            or WEBULL_CONFIG.get("webull_test_account_id")
            or os.getenv("WEBULL_ACCOUNT_ID")
        )
    else:
        app_key = os.getenv("WEBULL_APP_KEY")
        app_secret = os.getenv("WEBULL_APP_SECRET")
        account_id = os.getenv("WEBULL_ACCOUNT_ID")

    if not app_key or not app_secret:
        pytest.skip("Webull credentials are not configured for smoke tests")

    return WebullTrader(
        app_key=app_key,
        app_secret=app_secret,
        paper_trade=paper_trade,
        region=WEBULL_CONFIG.get("region", "US"),
        account_id=account_id,
    )


@pytest.mark.smoke
@pytest.mark.live
def test_webull_read_smoke_login(broker_matrix):
    _require_webull_enabled(broker_matrix)
    if os.getenv("RUN_WEBULL_READ_SMOKE") != "1":
        pytest.skip("RUN_WEBULL_READ_SMOKE != 1")

    trader = _build_trader()
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
    _require_webull_enabled(broker_matrix)
    if os.getenv("RUN_WEBULL_READ_SMOKE") != "1":
        pytest.skip("RUN_WEBULL_READ_SMOKE != 1")

    trader = _build_trader()
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
    _require_webull_enabled(broker_matrix)
    if os.getenv("RUN_WEBULL_WRITE_TESTS") != "1":
        pytest.skip("RUN_WEBULL_WRITE_TESTS != 1")

    if os.getenv("WEBULL_PAPER_REQUIRED", "1") == "1" and not _paper_trade_enabled():
        pytest.skip("WEBULL_PAPER_REQUIRED=1 requires PAPER_TRADE=true for write tests")

    trader = _build_trader()
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
    _require_webull_enabled(broker_matrix)
    if os.getenv("RUN_WEBULL_WRITE_TESTS") != "1":
        pytest.skip("RUN_WEBULL_WRITE_TESTS != 1")

    if os.getenv("WEBULL_PAPER_REQUIRED", "1") == "1" and not _paper_trade_enabled():
        pytest.skip("WEBULL_PAPER_REQUIRED=1 requires PAPER_TRADE=true for write tests")

    trader = _build_trader()
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
                option_expire_date=_next_weekly_expiry(days_ahead=21),
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
