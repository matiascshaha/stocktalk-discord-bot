"""Quote retrieval with Webull-specific fallback behavior."""

from typing import Any, Dict, List, Optional, Protocol

from src.utils.logger import setup_logger


logger = setup_logger("webull_quote_service")

_QUOTE_PERMISSION_MARKERS = (
    "insufficient permission",
    "subscribe to stock quotes",
    "unauthorized_category",
    "unauthorized_sub_type",
)


class WebullQuoteClient(Protocol):
    """Minimal quote/instrument contract required for quote resolution."""

    def get_current_stock_quote(self, symbol: str) -> Optional[float]:
        ...

    def get_instrument(self, symbols: str, category: str = "US_STOCK") -> List[Dict[str, Any]]:
        ...


def resolve_stock_quote(trader: WebullQuoteClient, symbol: str) -> Optional[float]:
    """Resolve a usable quote for stock limit pricing.

    Uses market snapshot first. If quote entitlements are missing, falls back
    to instrument `last_price`, which is typically available with trading scope.
    """
    try:
        snapshot_quote = trader.get_current_stock_quote(symbol)
    except Exception as exc:  # pragma: no cover - library exception shape varies
        if not _is_quote_permission_error(exc):
            raise
        logger.warning(
            "Snapshot quote unavailable for %s due to permission limits; "
            "falling back to instrument last_price.",
            symbol,
        )
        return _instrument_last_price(trader, symbol)

    if snapshot_quote is not None:
        return float(snapshot_quote)

    logger.warning(
        "Snapshot quote returned no price for %s; falling back to instrument last_price.",
        symbol,
    )
    return _instrument_last_price(trader, symbol)


def _instrument_last_price(trader: WebullQuoteClient, symbol: str) -> Optional[float]:
    instruments = trader.get_instrument(symbol, category="US_STOCK")
    if not instruments:
        return None

    raw_last_price = instruments[0].get("last_price")
    if raw_last_price is None:
        return None

    try:
        return float(raw_last_price)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid last_price for symbol {symbol}: {raw_last_price}") from exc


def _is_quote_permission_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _QUOTE_PERMISSION_MARKERS)
