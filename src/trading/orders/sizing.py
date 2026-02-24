"""Stock sizing policy helpers."""

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class StockSizingDecision:
    """Resolved sizing inputs for stock-order payload construction."""

    notional_dollar_amount: Optional[float]
    weighting: Optional[float]
    fallback_notional_on_weighting_error: Optional[float]


def resolve_stock_sizing_decision(
    side: Any,
    explicit_notional: Optional[float],
    weighting: Optional[float],
    trading_config: Mapping[str, Any],
) -> StockSizingDecision:
    """Resolve whether to size via explicit notional, forced default, or weighting."""
    side_value = str(getattr(side, "value", side or "")).upper().strip()
    default_amount = _positive_float(trading_config.get("default_amount"))
    force_default_for_buy = bool(trading_config.get("force_default_amount_for_buys", True))
    fallback_enabled = bool(trading_config.get("fallback_to_default_amount_on_weighting_failure", True))

    if explicit_notional is not None:
        return StockSizingDecision(
            notional_dollar_amount=float(explicit_notional),
            weighting=None,
            fallback_notional_on_weighting_error=None,
        )

    if side_value == "BUY" and force_default_for_buy:
        if default_amount is None:
            raise ValueError("Invalid trading.default_amount for forced default-amount sizing")
        return StockSizingDecision(
            notional_dollar_amount=default_amount,
            weighting=None,
            fallback_notional_on_weighting_error=None,
        )

    fallback_notional = None
    if side_value == "BUY" and weighting is not None and fallback_enabled:
        fallback_notional = default_amount

    return StockSizingDecision(
        notional_dollar_amount=None,
        weighting=weighting,
        fallback_notional_on_weighting_error=fallback_notional,
    )


def _positive_float(value: Any) -> Optional[float]:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None
