"""Option payload normalization helpers for Webull v2 option endpoints."""

from typing import Any, Dict, Optional

from src.models.webull_models import OptionOrderRequest, OrderPreviewResponse, OrderType


class WebullOptionPayloadBuilder:
    """Build and normalize Webull option payload shapes."""

    def build_v2_payload(self, order: OptionOrderRequest, quantity: Optional[int] = None) -> Dict[str, Any]:
        payload = order.model_dump(exclude_none=True)
        resolved_quantity = self.resolve_quantity(quantity, payload.get("quantity"))
        payload["quantity"] = resolved_quantity
        payload["legs"] = self._normalize_legs(payload.get("legs", []), resolved_quantity)
        return payload

    def _normalize_legs(self, legs: Any, resolved_quantity: str) -> list[Dict[str, Any]]:
        normalized_legs: list[Dict[str, Any]] = []
        for leg in legs or []:
            normalized_leg = dict(leg)
            normalized_leg["instrument_type"] = "OPTION"
            option_variant = str(normalized_leg.get("option_type", "")).upper().strip()
            if option_variant in {"CALL", "PUT"}:
                normalized_leg["option_type"] = option_variant
            if "option_expire_date" in normalized_leg:
                option_expiry = str(normalized_leg["option_expire_date"])
                normalized_leg["option_expire_date"] = option_expiry
                normalized_leg["init_exp_date"] = option_expiry
            normalized_leg["quantity"] = resolved_quantity
            normalized_legs.append(normalized_leg)
        return normalized_legs

    @staticmethod
    def resolve_quantity(quantity_override: Optional[int], fallback_quantity: Any) -> str:
        raw_quantity = quantity_override if quantity_override is not None else fallback_quantity
        try:
            quantity = int(float(raw_quantity))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid option quantity: {raw_quantity}") from exc
        if quantity < 1:
            raise ValueError(f"Option quantity must be >= 1 contract, got {quantity}")
        return str(quantity)

    @staticmethod
    def preview_total_cost(preview: OrderPreviewResponse) -> Optional[float]:
        try:
            estimated_cost = float(preview.estimated_cost or 0)
        except (TypeError, ValueError):
            estimated_cost = 0.0

        try:
            estimated_fee = float(preview.estimated_transaction_fee or 0)
        except (TypeError, ValueError):
            estimated_fee = 0.0

        total = estimated_cost + max(estimated_fee, 0.0)
        return total if total > 0 else None

    def build_legacy_payload(self, order: OptionOrderRequest, client_order_id: str) -> Dict[str, Any]:
        option_symbol = self.format_option_symbol(order)
        payload: Dict[str, Any] = {
            "client_order_id": client_order_id,
            "symbol": option_symbol,
            "instrument_type": "OPTION",
            "market": "US",
            "order_type": order.order_type,
            "quantity": str(order.quantity),
            "side": order.side,
            "time_in_force": order.time_in_force,
            "entrust_type": "QTY",
            "combo_type": "NORMAL",
            "support_trading_session": "CORE",
        }
        if order.order_type == OrderType.LIMIT:
            payload["limit_price"] = str(order.limit_price)
        return payload

    @staticmethod
    def format_option_symbol(order: OptionOrderRequest) -> str:
        expiry = order.expiry_date.replace("-", "")[2:]
        option_code = order.option_type[0]
        strike = f"{int(order.strike_price * 1000):08d}"
        return f"{order.symbol}{expiry}{option_code}{strike}"
