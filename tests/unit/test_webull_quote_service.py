from unittest.mock import MagicMock

import pytest

from src.brokerages.webull.quote_service import (
    _extract_book_price,
    _first_numeric,
    _first_quote_entry,
    _instrument_reference_price,
    _is_quote_permission_error,
    _resolve_from_quotes,
    _to_float,
    WebullQuoteClient,
    resolve_limit_reference_price,
)

pytestmark = [pytest.mark.unit]


pytestmark = pytest.mark.unit


def test_resolve_limit_reference_price_prefers_l1_ask_for_buy():
    trader = MagicMock()
    trader.get_stock_quotes.return_value = [{"asks": [{"price": "101.25"}], "bids": [{"price": "101.20"}]}]

    quote = resolve_limit_reference_price(trader, "AAPL", "BUY")

    assert quote == 101.25
    trader.get_current_stock_quote.assert_not_called()
    trader.get_instrument.assert_not_called()


def test_resolve_limit_reference_price_prefers_l1_bid_for_sell():
    trader = MagicMock()
    trader.get_stock_quotes.return_value = [{"asks": [{"price": "101.25"}], "bids": [{"price": "101.20"}]}]

    quote = resolve_limit_reference_price(trader, "AAPL", "SELL")

    assert quote == 101.2


def test_resolve_limit_reference_price_falls_back_to_instrument_for_permission_errors():
    trader = MagicMock()
    trader.get_stock_quotes.side_effect = RuntimeError(
        "HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."
    )
    trader.get_current_stock_quote.side_effect = RuntimeError(
        "HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."
    )
    trader.get_instrument.return_value = [{"last_price": "99.40"}]

    quote = resolve_limit_reference_price(trader, "AAPL", "BUY")

    assert quote == 99.4
    trader.get_instrument.assert_called_once_with("AAPL", category="US_STOCK")


def test_resolve_limit_reference_price_falls_back_when_snapshot_returns_none():
    trader = MagicMock()
    trader.get_stock_quotes.return_value = []
    trader.get_current_stock_quote.return_value = None
    trader.get_instrument.return_value = [{"last_price": 88.0}]

    quote = resolve_limit_reference_price(trader, "AAPL", "BUY")

    assert quote == 88.0


def test_resolve_limit_reference_price_raises_non_permission_errors():
    trader = MagicMock()
    trader.get_stock_quotes.return_value = []
    trader.get_current_stock_quote.side_effect = RuntimeError("temporary quote outage")

    with pytest.raises(RuntimeError, match="temporary quote outage"):
        resolve_limit_reference_price(trader, "AAPL", "BUY")


def test_resolve_limit_reference_price_returns_none_when_no_fallback_price():
    trader = MagicMock()
    trader.get_stock_quotes.side_effect = RuntimeError(
        "HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."
    )
    trader.get_current_stock_quote.side_effect = RuntimeError(
        "HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."
    )
    trader.get_instrument.return_value = [{"instrument_id": "AAPL_ID"}]

    quote = resolve_limit_reference_price(trader, "AAPL", "BUY")

    assert quote is None


def test_resolve_limit_reference_price_rejects_invalid_side():
    trader = MagicMock()
    with pytest.raises(ValueError, match="Unsupported order side"):
        resolve_limit_reference_price(trader, "AAPL", "HOLD")


def test_resolve_from_quotes_returns_none_when_quote_payload_unusable():
    trader = MagicMock()
    trader.get_stock_quotes.return_value = {"data": []}

    assert _resolve_from_quotes(trader, "AAPL", "BUY") is None


def test_resolve_from_quotes_raises_non_permission_errors():
    trader = MagicMock()
    trader.get_stock_quotes.side_effect = RuntimeError("service unavailable")

    with pytest.raises(RuntimeError, match="service unavailable"):
        _resolve_from_quotes(trader, "AAPL", "BUY")


def test_instrument_reference_price_sell_prefers_bid_then_last():
    trader = MagicMock()
    trader.get_instrument.return_value = [{"bid_price": None, "last_price": "97.3"}]

    assert _instrument_reference_price(trader, "AAPL", "SELL") == 97.3


def test_first_quote_entry_handles_list_dict_and_invalid_payload():
    assert _first_quote_entry([{"price": 1.0}]) == {"price": 1.0}
    assert _first_quote_entry({"data": [{"price": 2.0}]}) == {"price": 2.0}
    assert _first_quote_entry("bad") is None


def test_extract_book_price_handles_dict_scalar_and_invalid_levels():
    assert _extract_book_price([{"price": "10.5"}]) == 10.5
    assert _extract_book_price([11.2]) == 11.2
    assert _extract_book_price([]) is None


def test_first_numeric_returns_first_positive_numeric_value():
    assert _first_numeric(None, "0", "-2", "4.5", 5) == 4.5
    assert _first_numeric(None, "0", "-2") is None


def test_to_float_handles_scalar_dict_and_iterables():
    assert _to_float("12.3") == 12.3
    assert _to_float({"price": "13.4"}) == 13.4
    assert _to_float(["1"]) is None
    assert _to_float("null") is None


def test_is_quote_permission_error_detects_known_markers():
    assert _is_quote_permission_error(RuntimeError("Insufficient permission for quotes")) is True
    assert _is_quote_permission_error(RuntimeError("network timeout")) is False


def test_quote_client_protocol_defines_required_methods():
    assert hasattr(WebullQuoteClient, "get_stock_quotes")
    assert hasattr(WebullQuoteClient, "get_current_stock_quote")
    assert hasattr(WebullQuoteClient, "get_instrument")
