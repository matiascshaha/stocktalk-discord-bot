"""Mapping helpers between broker-agnostic contracts and Webull models."""

from typing import Any, Optional

from src.models.webull_models import (
    OptionLeg,
    OptionOrderRequest as WebullOptionOrderRequest,
    OptionType as WebullOptionType,
    OrderSide as WebullOrderSide,
    OrderType as WebullOrderType,
    StockOrderRequest as WebullStockOrderRequest,
    TimeInForce as WebullTimeInForce,
)
from src.trading.orders.contracts import (
    AccountBalanceSnapshot,
    OptionLegRequest,
    OptionOrderRequest,
    OptionType,
    OrderPreviewResult,
    OrderSubmissionResult,
    PositionSnapshot,
    StockOrderRequest,
    VehicleAssetType,
)


def to_webull_stock_order(order: StockOrderRequest) -> WebullStockOrderRequest:
    return WebullStockOrderRequest(
        symbol=order.symbol,
        side=WebullOrderSide(order.side.value),
        quantity=order.quantity,
        order_type=WebullOrderType(order.order_type.value),
        limit_price=order.limit_price,
        time_in_force=WebullTimeInForce(order.time_in_force.value),
        extended_hours_trading=order.extended_hours_trading,
    )


def to_webull_option_order(order: OptionOrderRequest) -> WebullOptionOrderRequest:
    legs = [to_webull_option_leg(leg) for leg in order.legs]
    limit_price = str(order.limit_price) if order.limit_price is not None else None

    return WebullOptionOrderRequest(
        order_type=WebullOrderType(order.order_type.value),
        quantity=str(order.quantity),
        limit_price=limit_price,
        side=WebullOrderSide(order.side.value),
        time_in_force=WebullTimeInForce(order.time_in_force.value),
        legs=legs,
    )


def to_webull_option_leg(leg: OptionLegRequest) -> OptionLeg:
    option_type = WebullOptionType.CALL if leg.option_type == OptionType.CALL else WebullOptionType.PUT
    return OptionLeg(
        side=WebullOrderSide(leg.side.value),
        quantity=str(leg.quantity),
        symbol=leg.symbol,
        strike_price=str(leg.strike_price),
        option_expire_date=leg.expiry_date,
        option_type=option_type,
        market="US",
    )


def map_submission_result(payload: Any, broker: str, asset_type: VehicleAssetType) -> OrderSubmissionResult:
    raw = payload if isinstance(payload, dict) else {"data": payload}
    order_id = _extract_order_id(payload)
    status = str(raw.get("status") or raw.get("state") or raw.get("result") or "submitted")

    return OrderSubmissionResult(
        status=status,
        broker=broker,
        asset_type=asset_type,
        order_id=order_id,
        message=None,
        raw=raw,
    )


def map_preview_result(payload: Any, broker: str, asset_type: VehicleAssetType) -> OrderPreviewResult:
    raw = payload if isinstance(payload, dict) else {"data": payload}
    return OrderPreviewResult(
        broker=broker,
        asset_type=asset_type,
        estimated_cost=_to_float(raw.get("estimated_cost")),
        estimated_transaction_fee=_to_float(raw.get("estimated_transaction_fee")),
        currency=raw.get("currency"),
        raw=raw,
    )


def map_balance_snapshot(payload: Any, broker: str) -> AccountBalanceSnapshot:
    raw = payload if isinstance(payload, dict) else {"data": payload}
    currency_asset = _first_currency_asset(raw)

    return AccountBalanceSnapshot(
        broker=broker,
        buying_power=_to_float(currency_asset.get("margin_power") if currency_asset else None),
        net_liquidation_value=_to_float(
            (currency_asset or {}).get("net_liquidation_value") or raw.get("total_market_value")
        ),
        currency=(currency_asset or {}).get("currency") or raw.get("currency"),
        raw=raw,
    )


def map_positions(payload: Any, broker: str) -> list[PositionSnapshot]:
    rows = _extract_positions(payload)
    snapshots: list[PositionSnapshot] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        snapshots.append(
            PositionSnapshot(
                broker=broker,
                symbol=row.get("symbol") or row.get("ticker"),
                quantity=_to_float(row.get("qty") or row.get("quantity")),
                average_cost=_to_float(row.get("average_cost") or row.get("avg_price")),
                market_value=_to_float(row.get("market_value") or row.get("value")),
                raw=row,
            )
        )
    return snapshots


def _extract_order_id(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("order_id", "orderId", "id", "client_order_id"):
            value = payload.get(key)
            if value not in (None, ""):
                return str(value)
        nested = payload.get("data")
        if isinstance(nested, dict):
            return _extract_order_id(nested)
        if isinstance(nested, list) and nested and isinstance(nested[0], dict):
            return _extract_order_id(nested[0])
    return None


def _first_currency_asset(payload: dict[str, Any]) -> Optional[dict[str, Any]]:
    assets = payload.get("account_currency_assets")
    if isinstance(assets, list) and assets and isinstance(assets[0], dict):
        return assets[0]
    return None


def _extract_positions(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("positions", "data", "list", "position_list"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
