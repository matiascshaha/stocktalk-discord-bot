from src.discord_client import StockMonitorClient

import pytest


pytestmark = [pytest.mark.feature, pytest.mark.happy_path]


def test_client_initializes():
    client = StockMonitorClient(trader=None)
    assert client.client is not None
