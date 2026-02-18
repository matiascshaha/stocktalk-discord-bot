from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.discord_client import StockMonitorClient
from tests.testkit.builders.discord_messages import TEST_CHANNEL_ID, build_message
from tests.testkit.payloads.signals import build_signal_payload


pytestmark = [pytest.mark.feature, pytest.mark.edge_case]


@pytest.mark.asyncio
async def test_trade_failure_does_not_crash_message_handler():
    trader = MagicMock()
    trader.place_stock_order = MagicMock(side_effect=RuntimeError("INVALID_PARAMETER"))

    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_called_once()
