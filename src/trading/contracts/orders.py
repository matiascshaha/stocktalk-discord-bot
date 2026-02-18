"""Canonical trading order contracts used across broker adapters."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class TradingSession(str, Enum):
    ALL = "ALL"
    CORE = "CORE"
    NIGHT = "NIGHT"


class StockOrder(BaseModel):
    """Broker-agnostic stock order."""

    model_config = ConfigDict(use_enum_values=True)

    symbol: str = Field(..., min_length=1)
    side: OrderSide
    quantity: float = Field(..., gt=0)
    order_type: OrderType = Field(OrderType.MARKET)
    limit_price: Optional[float] = Field(None, gt=0)
    time_in_force: TimeInForce = Field(TimeInForce.DAY)
    trading_session: TradingSession = Field(TradingSession.CORE)
    extended_hours_trading: bool = Field(False)

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        symbol = str(value or "").upper().replace("$", "").strip()
        if not symbol:
            raise ValueError("symbol is required")
        return symbol

    @field_validator("limit_price")
    @classmethod
    def validate_limit_price(cls, value: Optional[float], info):
        order_type = info.data.get("order_type")
        normalized_type = getattr(order_type, "value", order_type)
        if str(normalized_type).upper() == OrderType.LIMIT.value and value is None:
            raise ValueError("limit_price is required for LIMIT orders")
        return value
