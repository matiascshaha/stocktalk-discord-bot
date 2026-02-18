"""Broker-agnostic order request contracts."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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


class VehicleAssetType(str, Enum):
    STOCK = "STOCK"
    OPTION = "OPTION"


class OptionType(str, Enum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass(frozen=True)
class StockOrderRequest:
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    extended_hours_trading: bool = False

    def __post_init__(self) -> None:
        normalized_symbol = str(self.symbol or "").upper().replace("$", "").strip()
        if not normalized_symbol:
            raise ValueError("symbol is required")
        if float(self.quantity) <= 0:
            raise ValueError("quantity must be > 0")
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for LIMIT orders")

        object.__setattr__(self, "symbol", normalized_symbol)


@dataclass(frozen=True)
class OptionLegRequest:
    side: OrderSide
    quantity: int
    symbol: str
    strike_price: float
    expiry_date: str
    option_type: OptionType

    def __post_init__(self) -> None:
        normalized_symbol = str(self.symbol or "").upper().replace("$", "").strip()
        if not normalized_symbol:
            raise ValueError("option leg symbol is required")
        if int(self.quantity) < 1:
            raise ValueError("option leg quantity must be >= 1")
        if float(self.strike_price) <= 0:
            raise ValueError("strike_price must be > 0")
        expiry = str(self.expiry_date or "").strip()
        if not expiry:
            raise ValueError("expiry_date is required")

        object.__setattr__(self, "symbol", normalized_symbol)
        object.__setattr__(self, "expiry_date", expiry)


@dataclass(frozen=True)
class OptionOrderRequest:
    side: OrderSide
    quantity: int
    legs: list[OptionLegRequest] = field(default_factory=list)
    order_type: OrderType = OrderType.MARKET
    time_in_force: TimeInForce = TimeInForce.DAY
    limit_price: Optional[float] = None

    def __post_init__(self) -> None:
        if int(self.quantity) < 1:
            raise ValueError("option quantity must be >= 1")
        if not self.legs:
            raise ValueError("option order must include at least one leg")
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price is required for LIMIT orders")
