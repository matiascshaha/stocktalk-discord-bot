"""Canonical option order contracts used across broker adapters."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.trading.contracts.orders import OrderSide, OrderType, TimeInForce


class OptionType(str, Enum):
    CALL = "CALL"
    PUT = "PUT"


class OptionOrder(BaseModel):
    """Broker-agnostic single-leg option order."""

    model_config = ConfigDict(use_enum_values=True)

    symbol: str = Field(..., min_length=1)
    side: OrderSide
    quantity: int = Field(..., ge=1)
    option_type: OptionType
    strike_price: float = Field(..., gt=0)
    option_expire_date: str = Field(..., description="Expiry date (YYYY-MM-DD)")
    order_type: OrderType = Field(OrderType.MARKET)
    limit_price: Optional[float] = Field(None, gt=0)
    time_in_force: TimeInForce = Field(TimeInForce.GTC)

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        symbol = str(value or "").upper().replace("$", "").strip()
        if not symbol:
            raise ValueError("symbol is required")
        return symbol

    @field_validator("option_expire_date")
    @classmethod
    def validate_option_expire_date(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("option_expire_date must use YYYY-MM-DD format") from exc
        return value

    @field_validator("limit_price")
    @classmethod
    def validate_limit_price(cls, value: Optional[float], info):
        order_type = info.data.get("order_type")
        normalized_type = getattr(order_type, "value", order_type)
        if str(normalized_type).upper() == OrderType.LIMIT.value and value is None:
            raise ValueError("limit_price is required for LIMIT orders")
        return value
