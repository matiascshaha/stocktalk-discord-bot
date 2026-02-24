import pytest

from src.models.webull_models import AccountBalanceResponse, AccountCurrencyAsset
from src.trading.buying_power import (
    assert_margin_equity_buffer,
    compute_margin_equity_percentage,
    resolve_effective_buying_power,
    resolve_usable_buying_power,
)


pytestmark = [pytest.mark.unit]


def test_resolve_usable_buying_power_regular_session_adds_cash_and_day_component():
    asset = AccountCurrencyAsset(
        cash_power=1000.0,
        day_buying_power=4000.0,
        margin_power=2500.0,
    )

    assert resolve_usable_buying_power(asset, regular_session=True) == 5000.0


def test_resolve_usable_buying_power_off_hours_uses_overnight_component():
    asset = AccountCurrencyAsset(
        cash_power=250.0,
        overnight_buying_power=1800.0,
        margin_power=900.0,
    )

    assert resolve_usable_buying_power(asset, regular_session=False) == 2050.0


def test_resolve_usable_buying_power_clamps_negative_cash_to_zero():
    asset = AccountCurrencyAsset(
        cash_power=-300.0,
        margin_power=1200.0,
    )

    assert resolve_usable_buying_power(asset, regular_session=True) == 1200.0


def test_resolve_effective_buying_power_returns_none_for_non_positive_total(monkeypatch):
    monkeypatch.setattr("src.trading.buying_power.is_regular_market_session", lambda _: True)
    balance = AccountBalanceResponse(
        account_currency_assets=[AccountCurrencyAsset(cash_power=-100.0, margin_power=0.0)]
    )

    assert resolve_effective_buying_power(balance) is None


def test_compute_margin_equity_percentage_projects_new_exposure():
    balance = AccountBalanceResponse(
        total_market_value=10000.0,
        account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=5000.0)],
    )

    projected = compute_margin_equity_percentage(balance, estimated_trade_notional=5000.0)

    assert projected == pytest.approx(33.3333333333)


def test_assert_margin_equity_buffer_raises_when_projected_drops_below_threshold():
    balance = AccountBalanceResponse(
        total_market_value=10000.0,
        account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=5000.0)],
    )

    with pytest.raises(ValueError, match="Margin buffer violated"):
        assert_margin_equity_buffer(balance, min_margin_equity_pct=35.0, estimated_trade_notional=5000.0)
