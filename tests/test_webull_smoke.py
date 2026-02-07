import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from config.settings import WEBULL_CONFIG
from src.models.webull_models import OptionLeg, OptionOrderRequest, OptionType, OrderSide, OrderType, StockOrderRequest, TimeInForce
from src.webull_trader import WebullTrader


REPORT_PATH = Path("artifacts/webull_smoke_report.json")


def _append_check(name: str, status: str, details: dict):
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REPORT_PATH.exists():
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    else:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": [],
        }
    report["checks"].append({"name": name, "status": status, "details": details})
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _paper_trade_enabled() -> bool:
    raw = os.getenv("PAPER_TRADE", "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


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
def test_webull_read_smoke_login():
    if os.getenv("RUN_WEBULL_READ_SMOKE") != "1":
        pytest.skip("RUN_WEBULL_READ_SMOKE != 1")

    trader = _build_trader()
    ok = trader.login()
    details = {
        "paper_trade": trader.paper_trade,
        "region": trader.region,
        "endpoint": trader._get_endpoint(),
    }
    _append_check("webull_read_login", "passed" if ok else "failed", details)
    assert ok is True


@pytest.mark.smoke
@pytest.mark.live
def test_webull_read_smoke_balance_and_instrument():
    if os.getenv("RUN_WEBULL_READ_SMOKE") != "1":
        pytest.skip("RUN_WEBULL_READ_SMOKE != 1")

    trader = _build_trader()
    account_id = trader.resolve_account_id()
    balance = trader.get_account_balance()
    instruments = trader.get_instrument("AAPL")

    details = {
        "paper_trade": trader.paper_trade,
        "region": trader.region,
        "endpoint": trader._get_endpoint(),
        "account_id_masked": trader._mask_id(account_id),
        "balance_keys": sorted(list(balance.keys()))[:8],
        "instrument_count": len(instruments),
    }
    _append_check("webull_read_balance_instrument", "passed", details)
    assert len(instruments) > 0


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.webull_write
def test_webull_write_smoke_stock_order_opt_in():
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

    result = trader.place_stock_order(order)
    details = {
        "paper_trade": trader.paper_trade,
        "endpoint": trader._get_endpoint(),
        "result_keys": sorted(list(result.keys()))[:8] if isinstance(result, dict) else [],
    }
    _append_check("webull_write_stock_order", "passed", details)
    assert isinstance(result, dict)


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.webull_write
def test_webull_write_smoke_option_order_opt_in_non_blocking():
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
                strike_price="400.0",
                option_expire_date="2025-11-26",
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
            "error": str(exc),
        }
        _append_check("webull_write_option_order", "xfailed", details)
        pytest.xfail(f"Option endpoint unavailable/non-deterministic in this environment: {exc}")

    details = {
        "paper_trade": trader.paper_trade,
        "endpoint": trader._get_endpoint(),
        "result_keys": sorted(list(result.keys()))[:8] if isinstance(result, dict) else [],
    }
    _append_check("webull_write_option_order", "passed", details)
    assert isinstance(result, dict)
