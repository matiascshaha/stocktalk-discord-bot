import pytest

from src.brokerages.public.broker import PublicBroker
from src.trading.contracts import StockOrder


pytestmark = [pytest.mark.unit]


def test_public_broker_stores_config():
    broker = PublicBroker({"paper_trade": True})
    assert broker._config["paper_trade"] is True


def test_public_broker_place_stock_order_not_implemented():
    broker = PublicBroker({})
    order = StockOrder(symbol="AAPL", side="BUY", quantity=1)

    with pytest.raises(NotImplementedError, match="not implemented"):
        broker.place_stock_order(order)


def test_public_broker_get_limit_reference_price_not_implemented():
    broker = PublicBroker({})

    with pytest.raises(NotImplementedError, match="not implemented"):
        broker.get_limit_reference_price("AAPL", "BUY")
