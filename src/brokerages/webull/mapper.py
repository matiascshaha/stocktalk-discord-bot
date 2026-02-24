"""Mapping between canonical trading contracts and Webull request/response shapes."""

from typing import Any, Dict, Optional

from src.models.webull_models import (
    OrderSide as WebullOrderSide,
    OrderType as WebullOrderType,
    StockOrderRequest,
    TimeInForce as WebullTimeInForce,
    TradingSession as WebullTradingSession,
)
from src.trading.contracts import OrderType, OrderResult, StockOrder


def to_webull_stock_order(order: StockOrder) -> StockOrderRequest:
    side = _enum_value(order.side)
    order_type = _enum_value(order.order_type)
    time_in_force = _enum_value(order.time_in_force)
    trading_session = _enum_value(order.trading_session)
    return StockOrderRequest(
        symbol=order.symbol,
        side=WebullOrderSide(side),
        quantity=order.quantity,
        order_type=WebullOrderType(order_type),
        limit_price=order.limit_price if order_type == OrderType.LIMIT.value else None,
        time_in_force=WebullTimeInForce(time_in_force),
        trading_session=WebullTradingSession(trading_session),
        extended_hours_trading=order.extended_hours_trading,
    )


def to_order_result(payload: Any) -> OrderResult:
    raw = payload if isinstance(payload, dict) else {"response": payload}
    return OrderResult(
        broker="webull",
        success=True,
        raw=raw,
        order_id=_extract_order_id(raw),
    )


def _extract_order_id(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("order_id", "orderId", "id"):
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    data = payload.get("data")
    if isinstance(data, dict):
        return _extract_order_id(data)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return _extract_order_id(data[0])
    return None


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value or "")).upper().strip()
