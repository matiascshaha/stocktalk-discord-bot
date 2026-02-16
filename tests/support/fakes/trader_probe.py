class TraderProbe:
    def __init__(self):
        self.orders = []
        self.account_requests = 0

    def get_account_balance(self):
        self.account_requests += 1
        return {
            "total_market_value": 10000.0,
            "account_currency_assets": [
                {
                    "net_liquidation_value": 10000.0,
                    "margin_power": 5000.0,
                    "cash_power": 5000.0,
                }
            ],
        }

    def place_stock_order(self, order, weighting=None):
        self.orders.append((order, weighting))
        return {"ok": True}
