import pytest

from src.trading.orders.pricing import compute_buffered_limit_price


pytestmark = [pytest.mark.unit]


def test_compute_buffered_limit_price_buy_adds_buffer():
    assert compute_buffered_limit_price("BUY", 100.0, 50.0) == 100.5


def test_compute_buffered_limit_price_sell_subtracts_buffer():
    assert compute_buffered_limit_price("SELL", 100.0, 50.0) == 99.5


def test_compute_buffered_limit_price_enforces_cent_tick_for_prices_above_one():
    assert compute_buffered_limit_price("BUY", 85.78, 50.0) == 86.21
    assert compute_buffered_limit_price("SELL", 85.78, 50.0) == 85.35


def test_compute_buffered_limit_price_keeps_sub_dollar_precision():
    assert compute_buffered_limit_price("BUY", 0.95, 50.0) == 0.9547


def test_compute_buffered_limit_price_clamps_negative_buffer_to_zero():
    assert compute_buffered_limit_price("BUY", 100.0, -10.0) == 100.0


def test_compute_buffered_limit_price_rejects_non_positive_quote():
    with pytest.raises(ValueError, match="Quote must be positive"):
        compute_buffered_limit_price("BUY", 0.0, 50.0)


def test_compute_buffered_limit_price_rejects_non_positive_result():
    with pytest.raises(ValueError, match="Computed limit price must be positive"):
        compute_buffered_limit_price("SELL", 1.0, 10001.0)
