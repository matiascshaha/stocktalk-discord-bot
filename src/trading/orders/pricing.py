"""Stock limit-price helpers."""

from src.trading.contracts import OrderSide
from src.trading.orders.price_ticks import normalize_stock_limit_price_tick


def compute_buffered_limit_price(side: str, quote: float, buffer_bps: float) -> float:
    if quote <= 0:
        raise ValueError(f"Quote must be positive, got {quote}")

    safe_bps = max(0.0, float(buffer_bps))
    multiplier = 1.0 + (safe_bps / 10000.0)
    if str(side).upper() == OrderSide.SELL.value:
        multiplier = 1.0 - (safe_bps / 10000.0)

    price = normalize_stock_limit_price_tick(quote * multiplier)
    if price <= 0:
        raise ValueError(f"Computed limit price must be positive, got {price}")
    return price
