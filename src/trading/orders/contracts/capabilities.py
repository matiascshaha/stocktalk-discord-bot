"""Broker capability declarations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BrokerageCapabilities:
    supports_stock_orders: bool = True
    supports_option_orders: bool = False
    supports_order_preview: bool = True
    supports_positions: bool = True
    supports_balance: bool = True
