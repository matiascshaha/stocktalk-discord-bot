import pytest

from src.market_data.yahoo.contracts import YahooOptionChainShape, YahooQuoteShape
from tests.data.yahoo_probe_samples import (
    YAHOO_OPTION_CHAIN_SHAPE_SAMPLE_AAPL,
    YAHOO_QUOTE_SHAPE_SAMPLE_AAPL,
)


pytestmark = [pytest.mark.unit]


def test_yahoo_quote_shape_contract_validates_live_sample_payload():
    contract = YahooQuoteShape.model_validate(YAHOO_QUOTE_SHAPE_SAMPLE_AAPL)

    assert contract.info_keys_count > 0
    assert contract.sample_values.has_usable_price() is True
    assert contract.price_fields_present.last_price is True


def test_yahoo_option_chain_shape_contract_validates_live_sample_payload():
    contract = YahooOptionChainShape.model_validate(YAHOO_OPTION_CHAIN_SHAPE_SAMPLE_AAPL)

    assert contract.calls.row_count > 0
    assert contract.puts.row_count > 0
    assert contract.calls.sample.contract_symbol
    assert contract.puts.sample.contract_symbol


def test_yahoo_quote_shape_contract_rejects_unknown_fields():
    with pytest.raises(Exception):
        YahooQuoteShape.model_validate(
            {
                **YAHOO_QUOTE_SHAPE_SAMPLE_AAPL,
                "unexpected": "value",
            }
        )


def test_yahoo_option_chain_shape_contract_rejects_negative_row_count():
    payload = {
        **YAHOO_OPTION_CHAIN_SHAPE_SAMPLE_AAPL,
        "calls": {
            **YAHOO_OPTION_CHAIN_SHAPE_SAMPLE_AAPL["calls"],
            "row_count": -1,
        },
    }
    with pytest.raises(Exception):
        YahooOptionChainShape.model_validate(payload)

