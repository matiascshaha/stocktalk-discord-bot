from unittest.mock import MagicMock

import pytest

from src.brokerages.factory import build_brokerage
from src.brokerages.webull import WebullBroker


def test_factory_returns_webull_broker_for_webull_key():
    trader = MagicMock()

    broker = build_brokerage("webull", trader)

    assert isinstance(broker, WebullBroker)


def test_factory_requires_trader_for_webull():
    with pytest.raises(ValueError):
        build_brokerage("webull", None)


def test_factory_rejects_unknown_broker_key():
    with pytest.raises(ValueError):
        build_brokerage("unsupported", MagicMock())
