"""Canonical trading order contracts used across broker adapters."""

from dataclasses import dataclass
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


class TradingSession(str, Enum):
    ALL = "ALL"
    CORE = "CORE"
    NIGHT = "NIGHT"


@dataclass
class StockOrder:
    """Broker-agnostic stock order."""

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    trading_session: TradingSession = TradingSession.CORE
    extended_hours_trading: bool = False

    def __post_init__(self):
        self.symbol = str(self.symbol or "").upper().replace("$", "").strip()
        if not self.symbol:
            raise ValueError("symbol is required")

        self.side = self._coerce_enum(self.side, OrderSide, "side")
        self.order_type = self._coerce_enum(self.order_type, OrderType, "order_type")
        self.time_in_force = self._coerce_enum(self.time_in_force, TimeInForce, "time_in_force")
        self.trading_session = self._coerce_enum(self.trading_session, TradingSession, "trading_session")

        self.quantity = float(self.quantity)
        if self.quantity <= 0:
            raise ValueError("quantity must be > 0")

        if self.order_type == OrderType.LIMIT:
            if self.limit_price is None:
                raise ValueError("limit_price is required for LIMIT orders")
            self.limit_price = float(self.limit_price)
            if self.limit_price <= 0:
                raise ValueError("limit_price must be > 0")
        elif self.limit_price is not None:
            self.limit_price = float(self.limit_price)

    def _coerce_enum(self, value, enum_cls, field_name: str):
        if isinstance(value, enum_cls):
            return value
        raw = str(value or "").upper().strip()
        try:
            return enum_cls(raw)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be one of {[e.value for e in enum_cls]}") from exc

