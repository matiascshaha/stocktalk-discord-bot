"""Buying-power and margin-buffer policy helpers."""

from datetime import datetime
from typing import Iterable, Optional

from src.models.webull_models import AccountBalanceResponse, AccountCurrencyAsset
from src.trading.market_hours import is_regular_market_session


def _positive(value: Optional[float]) -> float:
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    return 0.0


def _first_positive(values: Iterable[Optional[float]]) -> float:
    for value in values:
        candidate = _positive(value)
        if candidate > 0:
            return candidate
    return 0.0


def resolve_margin_component(asset: AccountCurrencyAsset, regular_session: bool) -> float:
    """Resolve the margin-side buying-power component for the current session."""
    if regular_session:
        return _first_positive(
            (
                asset.day_buying_power,
                asset.buying_power,
                asset.stock_power,
                asset.margin_power,
            )
        )
    return _first_positive(
        (
            asset.overnight_buying_power,
            asset.overnight_power,
            asset.buying_power,
            asset.stock_power,
            asset.margin_power,
        )
    )


def resolve_usable_buying_power(asset: AccountCurrencyAsset, regular_session: bool) -> float:
    """
    Compute usable buying power.

    Policy:
    - cash contributes when positive
    - margin-side component contributes when positive
    - negative cash never subtracts from buying power
    """
    cash_component = _positive(asset.cash_power)
    margin_component = resolve_margin_component(asset, regular_session=regular_session)
    return cash_component + margin_component


def resolve_effective_buying_power(
    balance: AccountBalanceResponse,
    now: Optional[datetime] = None,
) -> Optional[float]:
    """Resolve effective buying power from account payload and market session."""
    if not balance.account_currency_assets:
        return None

    regular_session = is_regular_market_session(now)
    usable = resolve_usable_buying_power(balance.account_currency_assets[0], regular_session=regular_session)
    return usable if usable > 0 else None


def compute_margin_equity_percentage(
    balance: AccountBalanceResponse,
    estimated_trade_notional: float = 0.0,
) -> Optional[float]:
    """
    Estimate margin equity percentage after adding market exposure.

    Uses:
    - numerator: net_liquidation_value
    - denominator: total_market_value + estimated_trade_notional
    """
    if not balance.account_currency_assets:
        return None

    asset = balance.account_currency_assets[0]
    if asset.net_liquidation_value is None or balance.total_market_value is None:
        return None

    current_market_value = max(float(balance.total_market_value), 0.0)
    additional_market_value = max(float(estimated_trade_notional or 0.0), 0.0)
    projected_market_value = current_market_value + additional_market_value

    if projected_market_value <= 0:
        return 100.0

    return (float(asset.net_liquidation_value) / projected_market_value) * 100.0


def assert_margin_equity_buffer(
    balance: AccountBalanceResponse,
    min_margin_equity_pct: float,
    estimated_trade_notional: float,
) -> None:
    """Raise ValueError when projected margin equity drops below threshold."""
    threshold = float(min_margin_equity_pct)
    if threshold <= 0:
        return

    current_pct = compute_margin_equity_percentage(balance, estimated_trade_notional=0.0)
    projected_pct = compute_margin_equity_percentage(
        balance,
        estimated_trade_notional=estimated_trade_notional,
    )
    if current_pct is None or projected_pct is None:
        raise ValueError(
            "Unable to enforce margin buffer: missing total_market_value or net_liquidation_value in account balance"
        )
    if projected_pct < threshold:
        raise ValueError(
            f"Margin buffer violated: current={current_pct:.2f}%, projected={projected_pct:.2f}%, "
            f"required>={threshold:.2f}%"
        )
