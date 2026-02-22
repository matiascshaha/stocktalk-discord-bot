import pytest

from src.brokerages.ports import MarketDataPort, StockOrderBrokerPort, TradingBrokerPort


pytestmark = [pytest.mark.unit]


def test_trading_broker_port_composes_stock_and_market_ports():
    with pytest.raises(TypeError, match="runtime_checkable"):
        issubclass(TradingBrokerPort, StockOrderBrokerPort)
    with pytest.raises(TypeError, match="runtime_checkable"):
        issubclass(TradingBrokerPort, MarketDataPort)


def test_broker_ports_expose_required_methods():
    assert hasattr(StockOrderBrokerPort, "place_stock_order")
    assert hasattr(MarketDataPort, "get_limit_reference_price")
