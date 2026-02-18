from unittest.mock import MagicMock

import pytest

from src.brokerages.webull.quote_service import resolve_stock_quote


def test_resolve_stock_quote_prefers_snapshot_price():
    trader = MagicMock()
    trader.get_current_stock_quote.return_value = 101.25

    quote = resolve_stock_quote(trader, "AAPL")

    assert quote == 101.25
    trader.get_instrument.assert_not_called()


def test_resolve_stock_quote_falls_back_to_instrument_last_price_for_permission_errors():
    trader = MagicMock()
    trader.get_current_stock_quote.side_effect = RuntimeError(
        "HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."
    )
    trader.get_instrument.return_value = [{"last_price": "99.40"}]

    quote = resolve_stock_quote(trader, "AAPL")

    assert quote == 99.4
    trader.get_instrument.assert_called_once_with("AAPL", category="US_STOCK")


def test_resolve_stock_quote_falls_back_when_snapshot_returns_none():
    trader = MagicMock()
    trader.get_current_stock_quote.return_value = None
    trader.get_instrument.return_value = [{"last_price": 88.0}]

    quote = resolve_stock_quote(trader, "AAPL")

    assert quote == 88.0


def test_resolve_stock_quote_raises_non_permission_errors():
    trader = MagicMock()
    trader.get_current_stock_quote.side_effect = RuntimeError("temporary quote outage")

    with pytest.raises(RuntimeError, match="temporary quote outage"):
        resolve_stock_quote(trader, "AAPL")


def test_resolve_stock_quote_returns_none_when_no_fallback_price():
    trader = MagicMock()
    trader.get_current_stock_quote.side_effect = RuntimeError(
        "HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."
    )
    trader.get_instrument.return_value = [{"instrument_id": "AAPL_ID"}]

    quote = resolve_stock_quote(trader, "AAPL")

    assert quote is None
