import pytest

from tests.support.fakes.yahoo_probe_table import FakeTable
from tests.support.tooling.yahoo_probe import (
    capture_option_chain_shape,
    capture_quote_shape,
    extract_price_presence,
    resolve_probe_symbols,
)


pytestmark = [pytest.mark.unit]


def test_resolve_probe_symbols_uses_default_when_empty():
    assert resolve_probe_symbols(None) == ["AAPL", "TSLA"]
    assert resolve_probe_symbols("") == ["AAPL", "TSLA"]


def test_resolve_probe_symbols_normalizes_env_values():
    assert resolve_probe_symbols(" $aapl, tsla ,, msft ") == ["AAPL", "TSLA", "MSFT"]


def test_capture_quote_shape_includes_expected_fields():
    shape = capture_quote_shape(
        {"bid": 100.1, "lastPrice": 100.3, "currency": "USD"},
        {"ask": 100.2, "currentPrice": 100.25},
    )

    assert shape["sample_values"]["bid"] == 100.1
    assert shape["sample_values"]["ask"] == 100.2
    assert shape["sample_values"]["lastPrice"] == 100.3
    assert shape["price_fields_present"]["currentPrice"] is True


def test_extract_price_presence_returns_true_when_price_is_usable():
    shape = {
        "sample_values": {"lastPrice": 100.3, "bid": None, "ask": None},
    }
    assert extract_price_presence(shape) is True


def test_extract_price_presence_returns_false_when_price_is_missing():
    shape = {
        "sample_values": {"lastPrice": None, "bid": None, "ask": None},
    }
    assert extract_price_presence(shape) is False


def test_capture_option_chain_shape_extracts_table_structure_and_sample():
    calls = FakeTable(
        columns=["contractSymbol", "strike", "bid", "ask", "lastPrice"],
        rows=[{"contractSymbol": "AAPL260320C00190000", "strike": 190.0, "bid": 4.1, "ask": 4.3, "lastPrice": 4.2}],
    )
    puts = FakeTable(
        columns=["contractSymbol", "strike", "bid", "ask", "lastPrice"],
        rows=[{"contractSymbol": "AAPL260320P00190000", "strike": 190.0, "bid": 3.8, "ask": 4.0, "lastPrice": 3.9}],
    )

    shape = capture_option_chain_shape(calls, puts)

    assert shape["calls"]["row_count"] == 1
    assert shape["puts"]["row_count"] == 1
    assert shape["calls"]["sample"]["contractSymbol"] == "AAPL260320C00190000"
    assert shape["puts"]["sample"]["contractSymbol"] == "AAPL260320P00190000"
