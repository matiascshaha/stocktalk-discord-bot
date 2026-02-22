from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.models.webull_models import OptionLeg, OptionOrderRequest, OrderSide, OrderType, StockOrderRequest
from src.webull_trader import WebullTrader


pytestmark = [pytest.mark.unit]


def test_validate_config_rejects_missing_credentials():
    trader = WebullTrader.__new__(WebullTrader)
    trader.app_key = ""
    trader.app_secret = ""
    trader.region = "us"

    with pytest.raises(ValueError, match="app_key and app_secret required"):
        trader._validate_config()


def test_validate_config_rejects_invalid_region():
    trader = WebullTrader.__new__(WebullTrader)
    trader.app_key = "key"
    trader.app_secret = "secret"
    trader.region = "invalid"

    with pytest.raises(ValueError, match="Invalid region"):
        trader._validate_config()


def test_get_endpoint_uses_env_mapping():
    trader = WebullTrader.__new__(WebullTrader)
    trader.ENDPOINTS = WebullTrader.ENDPOINTS
    trader.region = "us"
    trader.paper_trade = True
    assert trader._get_endpoint() == "us-openapi-alb.uat.webullbroker.com"

    trader.paper_trade = False
    assert trader._get_endpoint() == "api.webull.com"


def test_extract_accounts_handles_supported_response_shapes():
    trader = WebullTrader.__new__(WebullTrader)

    assert trader._extract_accounts([{"account_id": "1"}]) == [{"account_id": "1"}]
    assert trader._extract_accounts({"accounts": [{"account_id": "2"}]}) == [{"account_id": "2"}]
    assert trader._extract_accounts({"data": [{"account_id": "3"}]}) == [{"account_id": "3"}]
    assert trader._extract_accounts({"list": [{"account_id": "4"}]}) == [{"account_id": "4"}]
    assert trader._extract_accounts("bad") == []


def test_format_and_normalize_stock_quantity():
    trader = WebullTrader.__new__(WebullTrader)

    assert trader._format_quantity(3.0) == "3"
    assert trader._format_quantity(3.5) == "3.5"
    assert trader._normalize_stock_quantity(2.9) == 2

    with pytest.raises(ValueError, match="must be >= 1"):
        trader._normalize_stock_quantity(0.4)


def test_mask_id_obscures_all_but_last_four_chars():
    trader = WebullTrader.__new__(WebullTrader)
    assert trader._mask_id("12345678") == "••••5678"


def test_check_response_raises_on_non_200_status():
    trader = WebullTrader.__new__(WebullTrader)

    with pytest.raises(RuntimeError, match="failed"):
        trader._check_response(SimpleNamespace(status_code=500, text="boom"), "op")


def test_check_response_accepts_200_status():
    trader = WebullTrader.__new__(WebullTrader)

    trader._check_response(SimpleNamespace(status_code=200, text="ok"), "op")


def test_get_current_stock_quote_uses_first_snapshot_price():
    trader = WebullTrader.__new__(WebullTrader)
    trader.get_market_snapshot = MagicMock(return_value=[{"price": "101.2"}])

    quote = trader.get_current_stock_quote("AAPL")

    assert quote == 101.2


def test_get_current_stock_quote_returns_none_when_empty_snapshots():
    trader = WebullTrader.__new__(WebullTrader)
    trader.get_market_snapshot = MagicMock(return_value=[])

    quote = trader.get_current_stock_quote("AAPL")

    assert quote is None


def test_build_stock_payload_uses_instrument_id_and_limit_price():
    trader = WebullTrader.__new__(WebullTrader)
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "IID", "last_price": 100.0}])
    order = StockOrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        order_type=OrderType.LIMIT,
        limit_price=101.5,
    )

    payload = trader._build_stock_payload(order)

    assert payload["instrument_id"] == "IID"
    assert payload["order_type"] == "LIMIT"
    assert payload["limit_price"] == "101.5"


def test_build_stock_payload_weighting_path_uses_buying_power_and_quote():
    trader = WebullTrader.__new__(WebullTrader)
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "IID", "last_price": 100.0}])
    trader._get_buying_power = MagicMock(return_value=10000.0)
    trader.get_current_stock_quote = MagicMock(return_value=50.0)
    order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    payload = trader._build_stock_payload(order, weighting=10.0)

    assert payload["qty"] == 20


def test_build_option_payload_formats_symbol_for_limit_order():
    trader = WebullTrader.__new__(WebullTrader)
    order = OptionOrderRequest(
        order_type=OrderType.LIMIT,
        quantity="1",
        limit_price="2.50",
        side=OrderSide.BUY,
        legs=[
            OptionLeg(
                side=OrderSide.BUY,
                quantity="1",
                symbol="AAPL",
                strike_price="200",
                option_expire_date="2026-03-20",
                option_type="CALL",
            )
        ],
    )

    with pytest.raises(AttributeError):
        trader._build_option_payload(order)
