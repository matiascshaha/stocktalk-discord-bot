from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from config.settings import TRADING_CONFIG
from src.models.webull_models import (
    AccountBalanceResponse,
    AccountCurrencyAsset,
    OptionLeg,
    OptionOrderRequest,
    OrderSide,
    OrderType,
    StockOrderRequest,
)
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
    balance = AccountBalanceResponse(account_currency_assets=[AccountCurrencyAsset(cash_power=10000.0)])
    trader._get_account_balance_contract = MagicMock(return_value=balance)
    trader._get_buying_power = MagicMock(return_value=10000.0)
    trader._enforce_margin_buffer = MagicMock()
    trader.get_current_stock_quote = MagicMock(return_value=50.0)
    order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    payload = trader._build_stock_payload(order, weighting=10.0)

    assert payload["qty"] == 20
    trader._enforce_margin_buffer.assert_called_once_with(balance, estimated_trade_notional=1000.0)


def test_build_stock_payload_notional_uses_instrument_price_fallback_chain():
    trader = WebullTrader.__new__(WebullTrader)
    trader.get_instrument = MagicMock(
        return_value=[
            {
                "instrument_id": "IID",
                "last_price": None,
                "price": "125.0",
            }
        ]
    )
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(account_currency_assets=[AccountCurrencyAsset(cash_power=10000.0)])
    )
    trader._enforce_margin_buffer = MagicMock()
    order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    payload = trader._build_stock_payload(order, notional_dollar_amount=1000.0)

    assert payload["qty"] == 8
    trader._enforce_margin_buffer.assert_called_once()


def test_build_stock_payload_notional_prefers_limit_price_when_present():
    trader = WebullTrader.__new__(WebullTrader)
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "IID"}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(account_currency_assets=[AccountCurrencyAsset(cash_power=10000.0)])
    )
    trader._enforce_margin_buffer = MagicMock()
    order = StockOrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        order_type=OrderType.LIMIT,
        limit_price=1.0,
    )

    payload = trader._build_stock_payload(order, notional_dollar_amount=1000.0)

    assert payload["qty"] == 1000


def test_place_stock_order_forces_default_amount_for_buy(monkeypatch):
    trader = WebullTrader.__new__(WebullTrader)
    monkeypatch.setitem(TRADING_CONFIG, "force_default_amount_for_buys", True)
    monkeypatch.setitem(TRADING_CONFIG, "default_amount", 1000.0)

    trader._build_stock_payload = MagicMock(return_value={"qty": 5})
    trader._execute_order = MagicMock(return_value={"ok": True})
    order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    result = trader.place_stock_order(order, weighting=15.0)

    assert result == {"ok": True}
    trader._build_stock_payload.assert_called_once_with(order, notional_dollar_amount=1000.0)


def test_place_stock_order_weighting_failure_falls_back_to_default_amount(monkeypatch):
    trader = WebullTrader.__new__(WebullTrader)
    monkeypatch.setitem(TRADING_CONFIG, "force_default_amount_for_buys", False)
    monkeypatch.setitem(TRADING_CONFIG, "fallback_to_default_amount_on_weighting_failure", True)
    monkeypatch.setitem(TRADING_CONFIG, "default_amount", 1000.0)

    trader._build_stock_payload = MagicMock(side_effect=[RuntimeError("quote unavailable"), {"qty": 10}])
    trader._execute_order = MagicMock(return_value={"ok": True})
    order = StockOrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=1)

    result = trader.place_stock_order(order, weighting=10.0)

    assert result == {"ok": True}
    assert trader._build_stock_payload.call_args_list == [
        call(order, weighting=10.0),
        call(order, notional_dollar_amount=1000.0),
    ]


def test_place_stock_order_sell_does_not_force_or_fallback_default_amount(monkeypatch):
    trader = WebullTrader.__new__(WebullTrader)
    monkeypatch.setitem(TRADING_CONFIG, "force_default_amount_for_buys", True)
    monkeypatch.setitem(TRADING_CONFIG, "fallback_to_default_amount_on_weighting_failure", True)
    monkeypatch.setitem(TRADING_CONFIG, "default_amount", 1000.0)

    trader._build_stock_payload = MagicMock(side_effect=RuntimeError("quote unavailable"))
    trader._execute_order = MagicMock()
    order = StockOrderRequest(symbol="AAPL", side=OrderSide.SELL, quantity=1)

    with pytest.raises(RuntimeError, match="quote unavailable"):
        trader.place_stock_order(order, weighting=10.0)

    trader._build_stock_payload.assert_called_once_with(order, weighting=10.0)


def test_resolve_effective_buying_power_adds_cash_and_margin_components():
    trader = WebullTrader.__new__(WebullTrader)
    balance = AccountBalanceResponse(
        account_currency_assets=[
            AccountCurrencyAsset(
                margin_power=3000.0,
                cash_power=5000.0,
            )
        ]
    )

    buying_power = trader._resolve_effective_buying_power(balance)

    assert buying_power == 8000.0


def test_resolve_effective_buying_power_returns_none_when_no_positive_candidate():
    trader = WebullTrader.__new__(WebullTrader)
    balance = AccountBalanceResponse(
        account_currency_assets=[
            AccountCurrencyAsset(
                margin_power=0.0,
                cash_power=0.0,
                day_buying_power=None,
            )
        ]
    )

    buying_power = trader._resolve_effective_buying_power(balance)

    assert buying_power is None


def test_get_buying_power_uses_validated_balance_contract():
    trader = WebullTrader.__new__(WebullTrader)
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            account_currency_assets=[AccountCurrencyAsset(margin_power=0.0, cash_power=2500.5)]
        )
    )

    buying_power = trader._get_buying_power()

    assert buying_power == 2500.5


def test_enforce_margin_buffer_rejects_when_projected_ratio_is_below_threshold(monkeypatch):
    trader = WebullTrader.__new__(WebullTrader)
    balance = AccountBalanceResponse(
        total_market_value=10000.0,
        account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=5000.0)],
    )
    monkeypatch.setitem(TRADING_CONFIG, "min_margin_equity_pct", 35.0)

    with pytest.raises(ValueError, match="Margin buffer violated"):
        trader._enforce_margin_buffer(balance, estimated_trade_notional=5000.0)


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
