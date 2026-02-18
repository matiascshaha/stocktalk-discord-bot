"""Webull market-data resolution for executable limit prices."""

from typing import Any, Dict, Iterable, List, Optional, Protocol

from src.utils.logger import setup_logger


logger = setup_logger("webull_quote_service")

_QUOTE_PERMISSION_MARKERS = (
    "insufficient permission",
    "subscribe to stock quotes",
    "unauthorized_category",
    "unauthorized_sub_type",
)


class WebullQuoteClient(Protocol):
    """Minimal market-data contract required for limit-price reference resolution."""

    def get_stock_quotes(self, symbol: str, category: str = "US_STOCK") -> Any:
        ...

    def get_current_stock_quote(self, symbol: str) -> Optional[float]:
        ...

    def get_instrument(self, symbols: str, category: str = "US_STOCK") -> List[Dict[str, Any]]:
        ...


def resolve_limit_reference_price(trader: WebullQuoteClient, symbol: str, side: str) -> Optional[float]:
    """Resolve a market-data reference price for limit-order construction."""
    normalized_side = str(side or "").upper()
    if normalized_side not in {"BUY", "SELL"}:
        raise ValueError(f"Unsupported order side for quote resolution: {side}")

    quote_ref = _resolve_from_quotes(trader, symbol, normalized_side)
    if quote_ref is not None:
        return quote_ref

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
        return _instrument_reference_price(trader, symbol, normalized_side)

    if snapshot_quote is not None:
        return float(snapshot_quote)

    logger.warning(
        "Snapshot quote returned no price for %s; falling back to instrument last_price.",
        symbol,
    )
    return _instrument_reference_price(trader, symbol, normalized_side)


def _resolve_from_quotes(trader: WebullQuoteClient, symbol: str, side: str) -> Optional[float]:
    try:
        quote_payload = trader.get_stock_quotes(symbol, category="US_STOCK")
    except Exception as exc:  # pragma: no cover - library exception shape varies
        if not _is_quote_permission_error(exc):
            raise
        logger.warning(
            "L1 quotes unavailable for %s due to permission limits; "
            "falling back to snapshot/instrument pricing.",
            symbol,
        )
        return None

    quote_entry = _first_quote_entry(quote_payload)
    if not quote_entry:
        return None

    if side == "BUY":
        return _first_numeric(
            _extract_book_price(quote_entry.get("asks")),
            quote_entry.get("ask"),
            quote_entry.get("ask_price"),
            quote_entry.get("price"),
            quote_entry.get("last_price"),
            _extract_book_price(quote_entry.get("bids")),
        )

    return _first_numeric(
        _extract_book_price(quote_entry.get("bids")),
        quote_entry.get("bid"),
        quote_entry.get("bid_price"),
        quote_entry.get("price"),
        quote_entry.get("last_price"),
        _extract_book_price(quote_entry.get("asks")),
    )


def _instrument_reference_price(trader: WebullQuoteClient, symbol: str, side: str) -> Optional[float]:
    instruments = trader.get_instrument(symbol, category="US_STOCK")
    if not instruments:
        return None

    instrument = instruments[0]
    if side == "BUY":
        return _first_numeric(
            instrument.get("ask_price"),
            instrument.get("ask"),
            instrument.get("last_price"),
            instrument.get("price"),
            instrument.get("close"),
            instrument.get("pre_close"),
        )

    return _first_numeric(
        instrument.get("bid_price"),
        instrument.get("bid"),
        instrument.get("last_price"),
        instrument.get("price"),
        instrument.get("close"),
        instrument.get("pre_close"),
    )


def _first_quote_entry(payload: Any) -> Optional[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload[0] if payload and isinstance(payload[0], dict) else None
    if isinstance(payload, dict):
        if payload.get("data") and isinstance(payload.get("data"), list):
            first = payload["data"][0] if payload["data"] else None
            return first if isinstance(first, dict) else None
        return payload
    return None


def _extract_book_price(levels: Any) -> Optional[float]:
    if not isinstance(levels, list) or not levels:
        return None
    top = levels[0]
    if isinstance(top, dict):
        return _to_float(top.get("price"))
    return _to_float(top)


def _first_numeric(*values: Any) -> Optional[float]:
    for value in values:
        parsed = _to_float(value)
        if parsed is not None and parsed > 0:
            return parsed
    return None


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", "null"):
        return None
    if isinstance(value, dict):
        for key in ("price", "value", "last_price"):
            nested = value.get(key)
            if nested not in (None, "", "null"):
                return _to_float(nested)
        return None
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_quote_permission_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _QUOTE_PERMISSION_MARKERS)
