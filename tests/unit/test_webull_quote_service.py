from unittest.mock import MagicMock

import pytest

from src.brokerages.webull.quote_service import resolve_limit_reference_price


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
