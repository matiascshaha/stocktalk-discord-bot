"""Urgency-aware limit-price math helpers."""

from typing import Optional

from src.trading.orders.price_models import BestBidAskQuote, ExecutionUrgency


def normalize_execution_urgency(value: object) -> ExecutionUrgency:
    raw = str(value or "").upper().strip()
    if raw == ExecutionUrgency.LOW.value:
        return ExecutionUrgency.LOW
    if raw == ExecutionUrgency.HIGH.value:
        return ExecutionUrgency.HIGH
    return ExecutionUrgency.MEDIUM


def compute_mid_price(quote: BestBidAskQuote) -> float:
    _validate_quote(quote)
    return (float(quote.bid) + float(quote.ask)) / 2.0


def compute_spread(quote: BestBidAskQuote) -> float:
    _validate_quote(quote)
    return float(quote.ask) - float(quote.bid)


def compute_urgency_limit_price(
    side: str,
    quote: BestBidAskQuote,
    urgency: ExecutionUrgency,
) -> float:
    normalized_side = _normalize_side(side)
    spread = compute_spread(quote)
    midpoint = compute_mid_price(quote)

    if urgency == ExecutionUrgency.LOW:
        return midpoint

    if urgency == ExecutionUrgency.MEDIUM:
        # Move 50% of half-spread from midpoint toward the fill side.
        step = spread / 4.0
        return midpoint + step if normalized_side == "BUY" else midpoint - step

    return quote.ask if normalized_side == "BUY" else quote.bid


def apply_slippage_cap_bps(
    side: str,
    target_price: float,
    reference_price: float,
    cap_bps: Optional[float],
) -> float:
    if target_price <= 0:
        raise ValueError(f"target_price must be positive, got {target_price}")
    if reference_price <= 0:
        raise ValueError(f"reference_price must be positive, got {reference_price}")

    if cap_bps is None:
        return float(target_price)

    safe_bps = max(0.0, float(cap_bps))
    side_value = _normalize_side(side)

    if side_value == "BUY":
        max_allowed = reference_price * (1.0 + safe_bps / 10000.0)
        return min(float(target_price), max_allowed)

    min_allowed = reference_price * (1.0 - safe_bps / 10000.0)
    return max(float(target_price), min_allowed)


def _validate_quote(quote: BestBidAskQuote) -> None:
    bid = float(quote.bid)
    ask = float(quote.ask)
    if bid <= 0:
        raise ValueError(f"bid must be positive, got {bid}")
    if ask <= 0:
        raise ValueError(f"ask must be positive, got {ask}")
    if ask < bid:
        raise ValueError(f"ask must be >= bid, got bid={bid}, ask={ask}")


def _normalize_side(side: str) -> str:
    normalized = str(side or "").upper().strip()
    if normalized in {"BUY", "SELL"}:
        return normalized
    raise ValueError(f"Unsupported side {side!r}; expected BUY or SELL")

