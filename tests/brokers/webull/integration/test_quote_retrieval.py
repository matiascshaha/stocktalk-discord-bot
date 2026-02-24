import pytest

from src.brokerages.webull.broker import WebullBroker
from tests.support.fakes.quote_aware_trader_probe import QuoteAwareTraderProbe


pytestmark = [pytest.mark.integration, pytest.mark.broker, pytest.mark.broker_webull]


def test_quote_retrieval_prefers_l1_book_for_buy():
    trader = QuoteAwareTraderProbe(
        quote_payload=[{"asks": [{"price": "101.25"}], "bids": [{"price": "101.20"}]}],
    )
    broker = WebullBroker(trader)

    quote = broker.get_limit_reference_price("AAPL", "BUY")

    assert quote == 101.25
    assert [entry[0] for entry in trader.calls] == ["get_stock_quotes"]


def test_quote_retrieval_falls_back_to_snapshot_then_instrument():
    trader = QuoteAwareTraderProbe(
        quote_error=RuntimeError("HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."),
        snapshot_error=RuntimeError("HTTP Status: 401, Msg: Insufficient permission, please subscribe to stock quotes."),
        instrument_payload=[{"last_price": "99.40"}],
    )
    broker = WebullBroker(trader)

    quote = broker.get_limit_reference_price("AAPL", "BUY")

    assert quote == 99.4
    assert [entry[0] for entry in trader.calls] == [
        "get_stock_quotes",
        "get_current_stock_quote",
        "get_instrument",
    ]
