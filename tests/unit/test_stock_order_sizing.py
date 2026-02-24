import pytest

from src.trading.orders.sizing import resolve_stock_sizing_decision


pytestmark = [pytest.mark.unit]


def test_resolve_stock_sizing_decision_uses_explicit_notional_first():
    decision = resolve_stock_sizing_decision(
        side="BUY",
        explicit_notional=750.0,
        weighting=25.0,
        trading_config={},
    )

    assert decision.notional_dollar_amount == 750.0
    assert decision.weighting is None
    assert decision.fallback_notional_on_weighting_error is None


def test_resolve_stock_sizing_decision_forces_default_amount_for_buy():
    decision = resolve_stock_sizing_decision(
        side="BUY",
        explicit_notional=None,
        weighting=15.0,
        trading_config={"default_amount": 1000.0, "force_default_amount_for_buys": True},
    )

    assert decision.notional_dollar_amount == 1000.0
    assert decision.weighting is None
    assert decision.fallback_notional_on_weighting_error is None


def test_resolve_stock_sizing_decision_rejects_invalid_default_for_forced_mode():
    with pytest.raises(ValueError, match="Invalid trading.default_amount"):
        resolve_stock_sizing_decision(
            side="BUY",
            explicit_notional=None,
            weighting=10.0,
            trading_config={"default_amount": 0.0, "force_default_amount_for_buys": True},
        )


def test_resolve_stock_sizing_decision_returns_weighting_with_buy_fallback():
    decision = resolve_stock_sizing_decision(
        side="BUY",
        explicit_notional=None,
        weighting=12.5,
        trading_config={
            "default_amount": 1000.0,
            "force_default_amount_for_buys": False,
            "fallback_to_default_amount_on_weighting_failure": True,
        },
    )

    assert decision.notional_dollar_amount is None
    assert decision.weighting == 12.5
    assert decision.fallback_notional_on_weighting_error == 1000.0


def test_resolve_stock_sizing_decision_sell_never_forces_or_fallbacks():
    decision = resolve_stock_sizing_decision(
        side="SELL",
        explicit_notional=None,
        weighting=10.0,
        trading_config={
            "default_amount": 1000.0,
            "force_default_amount_for_buys": True,
            "fallback_to_default_amount_on_weighting_failure": True,
        },
    )

    assert decision.notional_dollar_amount is None
    assert decision.weighting == 10.0
    assert decision.fallback_notional_on_weighting_error is None
