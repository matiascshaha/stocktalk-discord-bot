import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.ai_parser import AIParser
from src.discord_client import StockMonitorClient
from tests.support.cases.parser_messages import LIVE_PARSER_MESSAGE_PARAMS
from tests.support.factories.discord_messages import TEST_CHANNEL_ID, build_message
from tests.support.fakes.trader_probe import TraderProbe
from tests.support.matrix import ai_provider_has_credentials


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", LIVE_PARSER_MESSAGE_PARAMS)
async def test_live_ai_pipeline_message_to_trader(msg_id, author, text, should_pick, tickers):
    _ = msg_id
    if os.getenv("TEST_AI_LIVE", "0") != "1":
        pytest.skip("TEST_AI_LIVE != 1")

    parser_probe = AIParser()
    resolved_provider = (parser_probe.provider or "").lower()
    if not resolved_provider:
        pytest.fail("Live AI pipeline test requires a resolved AI provider")
    if not ai_provider_has_credentials(resolved_provider):
        pytest.fail(f"Live AI pipeline test requires valid credentials for provider '{resolved_provider}'")

    trader = TraderProbe()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client._log_signals = MagicMock()

    await client.on_message(build_message(text, author_id=321, channel_id=TEST_CHANNEL_ID))

    if should_pick:
        assert len(trader.orders) > 0
        assert trader.account_requests >= 1
        notify_payload = client.notifier.notify.call_args[0][0]
        assert isinstance(notify_payload, dict)
        assert isinstance(notify_payload.get("signals"), list)
        found = {signal["ticker"] for signal in notify_payload["signals"] if isinstance(signal, dict) and signal.get("ticker")}
        assert found & tickers
    else:
        assert trader.orders == []
