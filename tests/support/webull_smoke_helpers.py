import os
from datetime import date, timedelta
from pathlib import Path

import pytest

from config.settings import WEBULL_CONFIG
from src.webull_trader import WebullTrader


KNOWN_WEBULL_WRITE_XFAIL_MARKERS = (
    "DAY_BUYING_POWER_INSUFFICIENT",
    "OAUTH_OPENAPI_DAY_BUYING_POWER_INSUFFICIENT",
    "CAN_NOT_TRADING_FOR_NON_TRADING_HOURS",
    "CAN_NOT_TRADING_FOR_FIXGW_NOT_READY_NIGHT",
    "OAUTH_OPENAPI_CAN_NOT_TRADING_FOR_FIXGW_NOT_READY_NIGHT",
    "OAUTH_OPENAPI_TRADE_ORDER_NO_PERMISSION",
)

REPORT_PATH = Path("artifacts/webull_smoke_report.json")


def looks_like_placeholder(value: str) -> bool:
    candidate = (value or "").strip().lower()
    if not candidate:
        return True
    if candidate.endswith("here"):
        return True
    return any(marker in candidate for marker in ("your_", "replace", "example", "changeme", "<", ">"))


def paper_trade_enabled() -> bool:
    target = os.getenv("TEST_WEBULL_ENV", "paper").strip().lower()
    if target not in {"paper", "production"}:
        pytest.skip("TEST_WEBULL_ENV must be one of: paper, production")
    return target == "paper"


def require_webull_enabled(broker_matrix: list[str]) -> None:
    if "webull" not in broker_matrix:
        pytest.skip(f"Webull broker not enabled in TEST_BROKERS={','.join(broker_matrix)}")


def next_weekly_expiry(days_ahead: int = 21) -> str:
    target = date.today() + timedelta(days=days_ahead)
    days_until_friday = (4 - target.weekday()) % 7
    expiry = target + timedelta(days=days_until_friday)
    return expiry.isoformat()


def build_webull_smoke_trader() -> WebullTrader:
    paper_trade = paper_trade_enabled()

    if paper_trade:
        app_key = os.getenv("WEBULL_TEST_APP_KEY") or WEBULL_CONFIG.get("test_app_key") or os.getenv("WEBULL_APP_KEY")
        app_secret = (
            os.getenv("WEBULL_TEST_APP_SECRET") or WEBULL_CONFIG.get("test_app_secret") or os.getenv("WEBULL_APP_SECRET")
        )
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

    if looks_like_placeholder(app_key) or looks_like_placeholder(app_secret):
        if paper_trade:
            pytest.fail(
                "Webull paper smoke requires valid credentials (set WEBULL_TEST_APP_KEY/WEBULL_TEST_APP_SECRET "
                "or config.webull.test_app_key/test_app_secret)"
            )
        pytest.fail("Webull production smoke requires valid WEBULL_APP_KEY/WEBULL_APP_SECRET credentials")

    return WebullTrader(
        app_key=app_key,
        app_secret=app_secret,
        paper_trade=paper_trade,
        region=WEBULL_CONFIG.get("region", "US"),
        account_id=account_id,
    )
