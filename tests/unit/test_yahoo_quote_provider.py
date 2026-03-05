import pytest

from src.market_data.yahoo.quote_provider import YahooQuoteProvider
from tests.support.fakes.yahoo_quote_provider import build_fake_yahoo_ticker


pytestmark = [pytest.mark.unit]

def test_yahoo_quote_provider_prefers_ask_for_buy_side():
    provider = YahooQuoteProvider(
        ticker_factory=lambda _: build_fake_yahoo_ticker(fast_info={"ask": 101.25, "bid": 101.10})
    )

    price = provider.get_limit_reference_price("AAPL", "BUY")

    assert price == 101.25


def test_yahoo_quote_provider_prefers_bid_for_sell_side():
    provider = YahooQuoteProvider(
        ticker_factory=lambda _: build_fake_yahoo_ticker(fast_info={"ask": 101.25, "bid": 101.10})
    )

    price = provider.get_limit_reference_price("AAPL", "SELL")

    assert price == 101.10


def test_yahoo_quote_provider_falls_back_to_info_when_fast_info_missing():
    provider = YahooQuoteProvider(
        ticker_factory=lambda _: build_fake_yahoo_ticker(fast_info={}, info={"regularMarketPrice": 99.5})
    )

    price = provider.get_limit_reference_price("AAPL", "BUY")

    assert price == 99.5


def test_yahoo_quote_provider_returns_none_when_no_price_candidates_available():
    provider = YahooQuoteProvider(
        ticker_factory=lambda _: build_fake_yahoo_ticker(fast_info={}, info={})
    )

    price = provider.get_limit_reference_price("AAPL", "BUY")

    assert price is None


def test_yahoo_quote_provider_rejects_unknown_side():
    provider = YahooQuoteProvider(
        ticker_factory=lambda _: build_fake_yahoo_ticker(fast_info={"ask": 101.25})
    )

    with pytest.raises(ValueError, match="Unsupported side for quote lookup"):
        provider.get_limit_reference_price("AAPL", "HOLD")
