"""Webull capability declaration."""

from src.trading.orders.contracts import BrokerageCapabilities


WEBULL_CAPABILITIES = BrokerageCapabilities(
    supports_stock_orders=True,
    supports_option_orders=True,
    supports_order_preview=True,
    supports_positions=True,
    supports_balance=True,
)
