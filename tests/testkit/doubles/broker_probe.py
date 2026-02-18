class BrokerProbe:
    def __init__(self, quote=100.0):
        self.quote = quote
        self.orders = []

    def place_stock_order(self, order, weighting=None, notional_dollar_amount=None):
        self.orders.append((order, weighting, notional_dollar_amount))
        return {"ok": True}

    def get_limit_reference_price(self, symbol, side):
        _ = symbol
        _ = side
        return self.quote
