import pytest

from src.trading.orders.price_models import BestBidAskQuote, ExecutionUrgency
from src.trading.orders.urgency_pricing import (
    apply_slippage_cap_bps,
    compute_mid_price,
    compute_spread,
    compute_urgency_limit_price,
    normalize_execution_urgency,
)


pytestmark = [pytest.mark.unit]


def test_compute_mid_price_returns_midpoint():
    assert compute_mid_price(BestBidAskQuote(bid=100.0, ask=101.0)) == 100.5


def test_compute_spread_returns_ask_minus_bid():
    assert compute_spread(BestBidAskQuote(bid=100.0, ask=101.0)) == 1.0


def test_compute_urgency_limit_price_low_uses_midpoint():
    quote = BestBidAskQuote(bid=100.0, ask=101.0)
    assert compute_urgency_limit_price("BUY", quote, ExecutionUrgency.LOW) == 100.5
    assert compute_urgency_limit_price("SELL", quote, ExecutionUrgency.LOW) == 100.5


def test_compute_urgency_limit_price_medium_moves_half_half_spread_toward_fill_side():
    quote = BestBidAskQuote(bid=100.0, ask=101.0)
    # midpoint=100.5, spread=1.0, move=0.25
    assert compute_urgency_limit_price("BUY", quote, ExecutionUrgency.MEDIUM) == 100.75
    assert compute_urgency_limit_price("SELL", quote, ExecutionUrgency.MEDIUM) == 100.25


def test_compute_urgency_limit_price_high_uses_fill_side_top_of_book():
    quote = BestBidAskQuote(bid=100.0, ask=101.0)
    assert compute_urgency_limit_price("BUY", quote, ExecutionUrgency.HIGH) == 101.0
    assert compute_urgency_limit_price("SELL", quote, ExecutionUrgency.HIGH) == 100.0


def test_apply_slippage_cap_bps_caps_buy_above_reference_band():
    # max allowed = 100 * (1 + 0.5%) = 100.5
    assert apply_slippage_cap_bps("BUY", target_price=101.2, reference_price=100.0, cap_bps=50.0) == pytest.approx(100.5)
    assert apply_slippage_cap_bps("BUY", target_price=100.4, reference_price=100.0, cap_bps=50.0) == pytest.approx(100.4)


def test_apply_slippage_cap_bps_caps_sell_below_reference_band():
    # min allowed = 100 * (1 - 0.5%) = 99.5
    assert apply_slippage_cap_bps("SELL", target_price=98.8, reference_price=100.0, cap_bps=50.0) == pytest.approx(99.5)
    assert apply_slippage_cap_bps("SELL", target_price=99.7, reference_price=100.0, cap_bps=50.0) == pytest.approx(99.7)


def test_apply_slippage_cap_bps_accepts_none_cap():
    assert apply_slippage_cap_bps("BUY", target_price=101.2, reference_price=100.0, cap_bps=None) == 101.2


def test_normalize_execution_urgency_defaults_to_medium():
    assert normalize_execution_urgency("LOW") == ExecutionUrgency.LOW
    assert normalize_execution_urgency("HIGH") == ExecutionUrgency.HIGH
    assert normalize_execution_urgency("something_else") == ExecutionUrgency.MEDIUM


def test_urgency_helpers_reject_invalid_quote_or_side():
    with pytest.raises(ValueError, match="ask must be >= bid"):
        compute_mid_price(BestBidAskQuote(bid=101.0, ask=100.0))

    with pytest.raises(ValueError, match="Unsupported side"):
        compute_urgency_limit_price("HOLD", BestBidAskQuote(bid=100.0, ask=101.0), ExecutionUrgency.MEDIUM)

    with pytest.raises(ValueError, match="reference_price must be positive"):
        apply_slippage_cap_bps("BUY", target_price=100.0, reference_price=0.0, cap_bps=25.0)
