"""Deterministic policy helpers for stock order execution."""

from typing import Any

from src.models.webull_models import OrderSide, OrderType, StockOrderRequest, TimeInForce


NON_TRADING_HOURS_ERROR_MARKERS = (
    "CAN_NOT_TRADING_FOR_NON_TRADING_HOURS",
    "OAUTH_OPENAPI_CAN_NOT_TRADING_FOR_FIXGW_NOT_READY_NIGHT",
)


def resolve_time_in_force(raw_value: Any, default: TimeInForce) -> TimeInForce:
    value = str(raw_value or "").strip().upper()
    if value in {TimeInForce.DAY.value, TimeInForce.GTC.value, TimeInForce.IOC.value, TimeInForce.FOK.value}:
        return TimeInForce(value)
    return default


def resolve_buffer_bps(raw_value: Any, default: float = 50.0) -> float:
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return default
    return max(0.0, value)


def is_non_trading_hours_error(exc: Exception) -> bool:
    text = str(exc or "").upper()
    return any(marker in text for marker in NON_TRADING_HOURS_ERROR_MARKERS)


def compute_buffered_limit_price(side: str, quote: float, buffer_bps: float) -> float:
    if quote <= 0:
        raise ValueError(f"Quote must be positive, got {quote}")

    multiplier = 1.0 + (buffer_bps / 10000.0)
    if str(side).upper() == OrderSide.SELL.value:
        multiplier = 1.0 - (buffer_bps / 10000.0)

    price = quote * multiplier
    if price <= 0:
        raise ValueError(f"Computed limit price must be positive, got {price}")
    return round(price, 4)


def build_market_order(
    order: StockOrderRequest,
    time_in_force: TimeInForce,
    extended_hours_trading: bool,
) -> StockOrderRequest:
    return StockOrderRequest(
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        order_type=OrderType.MARKET,
        time_in_force=time_in_force,
        trading_session=order.trading_session,
        extended_hours_trading=extended_hours_trading,
    )


def build_buffered_limit_order(
    order: StockOrderRequest,
    quote: float,
    buffer_bps: float,
    time_in_force: TimeInForce,
    extended_hours_trading: bool,
) -> StockOrderRequest:
    limit_price = compute_buffered_limit_price(str(order.side), quote, buffer_bps)
    return StockOrderRequest(
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        order_type=OrderType.LIMIT,
        limit_price=limit_price,
        time_in_force=time_in_force,
        trading_session=order.trading_session,
        extended_hours_trading=extended_hours_trading,
    )
