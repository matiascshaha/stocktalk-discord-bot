import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.discord_client as discord_client_module
import src.trading.orders.planner as order_planner_module
from src.ai_parser import AIParser
from src.discord_client import StockMonitorClient
from tests.data.stocktalk_real_messages import REAL_MESSAGES
from tests.support.cases.live_scope import select_live_cases
from tests.support.factories.discord_messages import TEST_CHANNEL_ID, WRONG_CHANNEL_ID, build_message
from tests.support.factories.parser import parser_with_fake_openai_response
from tests.support.fakes.trader_probe import TraderProbe
from tests.support.matrix import ai_provider_has_credentials
from tests.support.payloads.signals import build_signal_payload


PIPELINE_CASES = REAL_MESSAGES[:]
LIVE_PIPELINE_CASES = select_live_cases(REAL_MESSAGES)


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
    client.parser.parse = MagicMock(return_value={"signals": [], "meta": {"status": "ok"}})

    await client.on_message(build_message("Buy AAPL", author_id=123, channel_id=WRONG_CHANNEL_ID))
    client.parser.parse.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_ignores_own_message():
    client = StockMonitorClient(trader=None)
    type(client.client).user = SimpleNamespace(id=123)
    client.parser.parse = MagicMock(return_value={"signals": [], "meta": {"status": "ok"}})

    await client.on_message(build_message("Buy AAPL", author_id=123, channel_id=TEST_CHANNEL_ID))
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

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_not_called()
    trader.place_stock_order.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_valid_signal_triggers_notify_and_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.side == "BUY"


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_option_vehicle_triggers_option_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "signals": [
                build_signal_payload(
                    "AAPL",
                    "BUY",
                    vehicles=[
                        {
                            "type": "OPTION",
                            "enabled": True,
                            "intent": "EXECUTE",
                            "side": "BUY",
                            "option_type": "CALL",
                            "strike": 210,
                            "expiry": "2026-03-20",
                        }
                    ],
                )
            ],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(build_message("AAPL 210c", author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.place_option_order.assert_called_once()
    option_order = trader.place_option_order.call_args[0][0]
    assert option_order.order_type == "MARKET"
    assert option_order.time_in_force == "DAY"
    assert option_order.legs[0].strike_price == "210.0"


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_off_hours_uses_queued_limit_without_retry(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: False)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "queue_when_closed", True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "queue_time_in_force", "GTC")
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)

    trader = MagicMock()
    trader.get_stock_quotes = MagicMock(return_value=[{"asks": [{"price": "100.0"}], "bids": [{"price": "99.9"}]}])
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY", weight_percent=None)], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.order_type == "LIMIT"
    assert order.time_in_force == "GTC"


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_regular_hours_uses_market_order_without_retry(monkeypatch):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)

    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "BUY", weight_percent=None)], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Buy AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.order_type == "MARKET"


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_sell_signal_triggers_sell_order():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "SELL")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Sell AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    trader.place_stock_order.assert_called_once()
    order = trader.place_stock_order.call_args[0][0]
    assert order.side == "SELL"


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
async def test_hold_signal_does_not_trade():
    trader = MagicMock()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={"signals": [build_signal_payload("AAPL", "HOLD")], "meta": {"status": "ok"}}
    )

    await client.on_message(build_message("Hold AAPL", author_id=321, channel_id=TEST_CHANNEL_ID))
    client.notifier.notify.assert_called_once()
    trader.place_stock_order.assert_not_called()


@pytest.mark.unit
@pytest.mark.contract
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


@pytest.mark.unit
@pytest.mark.contract
@pytest.mark.asyncio
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", PIPELINE_CASES)
async def test_real_message_pipeline_fake_ai_to_trader(msg_id, author, text, should_pick, tickers):
    _ = msg_id
    trader = TraderProbe()
    client = StockMonitorClient(trader=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client._log_signals = MagicMock()

    if should_pick:
        fake_payload = {
            "signals": [build_signal_payload(ticker, "BUY", confidence=0.95, weight_percent=None) for ticker in sorted(tickers)]
        }
    else:
        fake_payload = {"signals": []}
    client.parser = parser_with_fake_openai_response(json.dumps(fake_payload))

    await client.on_message(build_message(text, author_id=321, channel_id=TEST_CHANNEL_ID))

    if should_pick:
        assert len(trader.orders) == len(tickers)
        assert trader.account_requests >= 1
        parsed_payload = client.notifier.notify.call_args[0][0]
        found = {signal["ticker"] for signal in parsed_payload["signals"]}
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
        found = {
            signal["ticker"] for signal in notify_payload["signals"] if isinstance(signal, dict) and signal.get("ticker")
        }
        assert found & tickers
    else:
        assert trader.orders == []
