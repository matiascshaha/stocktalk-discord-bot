"""Broker-agnostic response contracts."""

from dataclasses import dataclass, field
from typing import Any, Optional

from src.trading.orders.contracts.requests import VehicleAssetType


@dataclass(frozen=True)
class OrderSubmissionResult:
    status: str
    broker: str
    asset_type: VehicleAssetType
    order_id: Optional[str] = None
    message: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OrderPreviewResult:
    broker: str
    asset_type: VehicleAssetType
    estimated_cost: Optional[float] = None
    estimated_transaction_fee: Optional[float] = None
    currency: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AccountBalanceSnapshot:
    broker: str
    buying_power: Optional[float]
    net_liquidation_value: Optional[float]
    currency: Optional[str]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PositionSnapshot:
    broker: str
    symbol: Optional[str]
    quantity: Optional[float]
    average_cost: Optional[float]
    market_value: Optional[float]
    raw: dict[str, Any] = field(default_factory=dict)
