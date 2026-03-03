"""Yahoo quote provider adapter for executable stock limit references."""

from collections.abc import Mapping
from typing import Any, Callable, Optional

from src.utils.logger import setup_logger


logger = setup_logger("yahoo_quote_provider")


class YahooQuoteProvider:
    """Resolve side-aware executable quote references from Yahoo payloads."""

    def __init__(self, ticker_factory: Optional[Callable[[str], Any]] = None):
        self._ticker_factory = ticker_factory or _build_default_ticker_factory()

    def get_limit_reference_price(self, symbol: str, side: str) -> Optional[float]:
        normalized_symbol = _normalize_symbol(symbol)
        normalized_side = _normalize_side(side)

        try:
            ticker = self._ticker_factory(normalized_symbol)
        except Exception as exc:
            logger.warning("Failed to create Yahoo ticker client for %s: %s", normalized_symbol, exc)
            return None

        fast_info = _as_mapping(getattr(ticker, "fast_info", None))
        price = _pick_side_reference_price(fast_info, normalized_side)
        if price is not None:
            return price

        info = _as_mapping(getattr(ticker, "info", None))
        return _pick_side_reference_price(info, normalized_side)


def _build_default_ticker_factory() -> Callable[[str], Any]:
    try:
        import yfinance as yf
    except Exception as exc:
        raise RuntimeError(
            "yfinance is required when trading.quote_provider=yahoo"
        ) from exc

    return yf.Ticker


def _normalize_symbol(symbol: str) -> str:
    normalized = str(symbol or "").strip().upper().replace("$", "")
    if not normalized:
        raise ValueError("Quote symbol is required")
    return normalized


def _normalize_side(side: str) -> str:
    normalized = str(side or "").strip().upper()
    if normalized not in {"BUY", "SELL"}:
        raise ValueError(f"Unsupported side for quote lookup: {side}")
    return normalized


def _pick_side_reference_price(payload: Mapping[str, Any], side: str) -> Optional[float]:
    if not payload:
        return None

    if side == "BUY":
        return _first_positive_float(
            payload.get("ask"),
            payload.get("regularMarketPrice"),
            payload.get("lastPrice"),
            payload.get("currentPrice"),
            payload.get("previousClose"),
            payload.get("bid"),
            payload.get("last_price"),
            payload.get("current_price"),
            payload.get("previous_close"),
        )

    return _first_positive_float(
        payload.get("bid"),
        payload.get("regularMarketPrice"),
        payload.get("lastPrice"),
        payload.get("currentPrice"),
        payload.get("previousClose"),
        payload.get("ask"),
        payload.get("last_price"),
        payload.get("current_price"),
        payload.get("previous_close"),
    )


def _as_mapping(payload: Any) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        return payload
    return {}


def _first_positive_float(*candidates: Any) -> Optional[float]:
    for candidate in candidates:
        try:
            parsed = float(candidate)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return parsed
    return None
