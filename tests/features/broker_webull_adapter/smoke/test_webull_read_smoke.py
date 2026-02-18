import os

import pytest

from tests.testkit.helpers.artifacts import append_smoke_check
from tests.testkit.helpers.webull_smoke_helpers import REPORT_PATH, build_webull_smoke_trader, require_webull_enabled


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
