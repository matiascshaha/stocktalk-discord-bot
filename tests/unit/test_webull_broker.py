from unittest.mock import MagicMock

import pytest

import src.brokerages.webull.broker as webull_broker_module
from src.brokerages.webull.broker import WebullBroker


pytestmark = [pytest.mark.unit]


def test_place_stock_order_maps_request_and_result(monkeypatch):
    trader = MagicMock()
    trader.place_stock_order.return_value = {"id": "abc"}
    monkeypatch.setattr(webull_broker_module, "to_webull_stock_order", MagicMock(return_value="mapped-order"))
    monkeypatch.setattr(webull_broker_module, "to_order_result", MagicMock(return_value="mapped-result"))
    broker = WebullBroker(trader)

    result = broker.place_stock_order("canonical-order", weighting=5.0)

    assert result == "mapped-result"
    webull_broker_module.to_webull_stock_order.assert_called_once_with("canonical-order")
    trader.place_stock_order.assert_called_once_with("mapped-order", weighting=5.0)
    webull_broker_module.to_order_result.assert_called_once_with({"id": "abc"})


def test_get_limit_reference_price_delegates_to_quote_service(monkeypatch):
    trader = MagicMock()
    monkeypatch.setattr(webull_broker_module, "resolve_limit_reference_price", MagicMock(return_value=101.0))
    broker = WebullBroker(trader)

    price = broker.get_limit_reference_price("AAPL", "BUY")

    assert price == 101.0
    webull_broker_module.resolve_limit_reference_price.assert_called_once_with(trader, "AAPL", "BUY")
