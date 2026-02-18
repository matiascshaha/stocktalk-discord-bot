from src.trading.orders.contracts import BrokerageCapabilities


class BrokerProbe:
    def __init__(self, quote=100.0, supports_options=True):
        self.quote = quote
        self.orders = []
        self.option_orders = []
        self.supports_options = supports_options

    def place_stock_order(self, order, weighting=None):
        self.orders.append((order, weighting))
        return {
            "status": "ok",
            "broker": "probe",
            "asset_type": "STOCK",
            "raw": {"ok": True},
        }

    def preview_stock_order(self, order):
        _ = order
        return {
            "broker": "probe",
            "asset_type": "STOCK",
            "estimated_cost": 100.0,
            "estimated_transaction_fee": 0.0,
            "currency": "USD",
            "raw": {"ok": True},
        }

    def place_option_order(self, order):
        self.option_orders.append(order)
        if not self.supports_options:
            raise RuntimeError("option orders unsupported")
        return {
            "status": "ok",
            "broker": "probe",
            "asset_type": "OPTION",
            "raw": {"ok": True},
        }

    def preview_option_order(self, order):
        _ = order
        return {
            "broker": "probe",
            "asset_type": "OPTION",
            "estimated_cost": 10.0,
            "estimated_transaction_fee": 0.0,
            "currency": "USD",
            "raw": {"ok": True},
        }

    def get_limit_reference_price(self, symbol, side):
        _ = symbol
        _ = side
        return self.quote

    def get_capabilities(self):
        return BrokerageCapabilities(supports_option_orders=self.supports_options)

    def get_account_balance(self):
        return {
            "broker": "probe",
            "buying_power": 10000.0,
            "net_liquidation_value": 10000.0,
            "currency": "USD",
            "raw": {},
        }

    def get_positions(self):
        return []
