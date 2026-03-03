"""Price tick helpers."""


def normalize_stock_limit_price_tick(price: float) -> float:
    """
    Normalize stock price to expected tick increments.

    Webull rejects stock limit prices above $1 unless they are in $0.01 increments.
    """
    if price > 1.0:
        return round(price, 2)
    return round(price, 4)

