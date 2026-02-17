class BrokerProbe:
    def __init__(self, quote=100.0):
        self.quote = quote
        self.orders = []

    def place_stock_order(self, order, weighting=None):
        self.orders.append((order, weighting))
        return {"ok": True}

    def get_current_stock_quote(self, symbol):
        _ = symbol
        return self.quote

