import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.discord_client as discord_client_module
from src.ai_parser import AIParser
from src.discord_client import StockMonitorClient
from tests.data.stocktalk_real_messages import REAL_MESSAGES

TEST_CHANNEL_ID = 123456789
WRONG_CHANNEL_ID = TEST_CHANNEL_ID + 1


def _message(content: str, author_id: int, channel_id: int):
    author = SimpleNamespace(id=author_id, name=f"user-{author_id}")
    channel = SimpleNamespace(id=channel_id)
    return SimpleNamespace(
        content=content,
        author=author,
        channel=channel,
        jump_url="https://discord.com/mock/message",
    )


class _FakeOpenAIClient:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        _ = kwargs
        message = SimpleNamespace(content=self._response_text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _TraderProbe:
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


def _parser_with_fake_response(response_text: str) -> AIParser:
    parser = AIParser()
    parser.provider = "openai"
    parser.client = _FakeOpenAIClient(response_text)
    return parser


PIPELINE_CASES = REAL_MESSAGES[:]


def _select_live_pipeline_cases():
    if os.getenv("RUN_LIVE_AI_PIPELINE_FULL") == "1":
        return REAL_MESSAGES[:]
    return [case for case in REAL_MESSAGES if case[3]][:1]


LIVE_PIPELINE_CASES = _select_live_pipeline_cases()


@pytest.fixture(autouse=True)
def _stable_channel_id(monkeypatch):
    # Keep deterministic tests independent from local/CI CHANNEL_ID env setup.
    monkeypatch.setattr(discord_client_module, "CHANNEL_ID", TEST_CHANNEL_ID)


@pytest.mark.unit
@pytest.mark.contract
def test_client_initializes():
    client = StockMonitorClient(trader=None)
    assert client.client is not None


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_ignores_wrong_channel():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=999)
    client.parser.parse = MagicMock(return_value={"picks": [], "meta": {"status": "ok"}})

    await client.on_message(_message("Buy AAPL", author_id=123, channel_id=WRONG_CHANNEL_ID))
    client.parser.parse.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_ignores_own_message():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=123)
    client.parser.parse = MagicMock(return_value={"picks": [], "meta": {"status": "ok"}})

    await client.on_message(_message("Buy AAPL", author_id=123, channel_id=TEST_CHANNEL_ID))
    client.parser.parse.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_malformed_parser_response_does_not_notify_or_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.parser.parse = MagicMock(return_value=["bad-shape"])
    client.notifier.notify = MagicMock()

    await client.on_message(_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_not_called()
    trader.place_stock_order.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_valid_pick_triggers_notify_and_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "picks": [
                {
                    "ticker": "AAPL",
                    "action": "BUY",
                    "confidence": 0.9,
                    "weight_percent": 5.0,
                    "urgency": "MEDIUM",
                    "sentiment": "BULLISH",
                    "reasoning": "test",
                }
            ],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.side == "BUY"


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_sell_pick_triggers_sell_order():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "picks": [
                {
                    "ticker": "AAPL",
                    "action": "SELL",
                    "confidence": 0.9,
                    "weight_percent": 5.0,
                    "urgency": "MEDIUM",
                    "sentiment": "BEARISH",
                    "reasoning": "test",
                }
            ],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(_message("Sell AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.side == "SELL"


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_hold_pick_does_not_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "picks": [
                {
                    "ticker": "AAPL",
                    "action": "HOLD",
                    "confidence": 0.9,
                    "weight_percent": 5.0,
                    "urgency": "LOW",
                    "sentiment": "NEUTRAL",
                    "reasoning": "test",
                }
            ],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(_message("Hold AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", PIPELINE_CASES)
async def test_real_message_pipeline_fake_ai_to_trader(msg_id, author, text, should_pick, tickers):
    _ = msg_id
    trader = _TraderProbe()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client._log_picks = MagicMock()

    if should_pick:
        fake_payload = {"picks": [{"ticker": t, "action": "BUY", "confidence": 0.95} for t in sorted(tickers)]}
    else:
        fake_payload = {"picks": []}
    client.parser = _parser_with_fake_response(json.dumps(fake_payload))

    await client.on_message(_message(text, author_id=321, channel_id=TEST_CHANNEL_ID))

    if should_pick:
        assert len(trader.orders) == len(tickers)
        assert trader.account_requests >= 1
        parsed_payload = client.notifier.notify.call_args[0][0]
        found = {pick["ticker"] for pick in parsed_payload["picks"]}
        for ticker in tickers:
            assert ticker in found
    else:
        assert trader.orders == []
        client.notifier.notify.assert_not_called()


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.asyncio
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", LIVE_PIPELINE_CASES)
async def test_live_ai_pipeline_message_to_trader(msg_id, author, text, should_pick, tickers):
    _ = msg_id
    if os.getenv("RUN_LIVE_AI_TESTS") != "1":
        pytest.skip("RUN_LIVE_AI_TESTS != 1")

    trader = _TraderProbe()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client._log_picks = MagicMock()

    await client.on_message(_message(text, author_id=321, channel_id=TEST_CHANNEL_ID))

    if should_pick:
        assert len(trader.orders) > 0
        assert trader.account_requests >= 1
        notify_payload = client.notifier.notify.call_args[0][0]
        assert isinstance(notify_payload, dict)
        assert isinstance(notify_payload.get("picks"), list)
        found = {pick["ticker"] for pick in notify_payload["picks"] if isinstance(pick, dict) and pick.get("ticker")}
        assert found & tickers
    else:
        assert trader.orders == []
