import pytest

from src.trading.orders.price_ticks import normalize_stock_limit_price_tick


pytestmark = [pytest.mark.unit]


def test_normalize_stock_limit_price_tick_uses_cent_tick_above_one():
    assert normalize_stock_limit_price_tick(85.7899) == 85.79


def test_normalize_stock_limit_price_tick_uses_sub_dollar_precision():
    assert normalize_stock_limit_price_tick(0.95474) == 0.9547

