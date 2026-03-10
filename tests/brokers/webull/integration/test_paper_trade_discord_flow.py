import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.discord_client as discord_client_module
import src.trading.orders.planner as order_planner_module
import src.webull_trader as webull_trader_module
from src.brokerages.webull.broker import WebullBroker
from src.discord_client import StockMonitorClient
from src.models.webull_models import AccountBalanceResponse, AccountCurrencyAsset
from src.webull_trader import WebullTrader
from tests.data.stocktalk_real_messages import MESSAGE_FIXTURES
from tests.support.factories.discord_messages import TEST_CHANNEL_ID, build_message
from tests.support.payloads.signals import build_signal_payload


pytestmark = [
    pytest.mark.integration,
    pytest.mark.broker,
    pytest.mark.broker_webull,
    pytest.mark.channel,
    pytest.mark.source_discord,
]

FROZEN_COMMON_SHARES_MESSAGE = MESSAGE_FIXTURES["frozen_common_shares"].text
FROZEN_OPTIONS_MESSAGE = MESSAGE_FIXTURES["frozen_options_only"].text
FROZEN_MIXED_MESSAGE = MESSAGE_FIXTURES["frozen_mixed_commons_options"].text
FROZEN_NO_ACTION_MESSAGE = MESSAGE_FIXTURES["frozen_no_action"].text
FROZEN_WEIGHTED_MESSAGE = MESSAGE_FIXTURES["frozen_weighted"].text
FROZEN_DOLLAR_AMOUNT_MESSAGE = MESSAGE_FIXTURES["frozen_dollar_amount"].text


@pytest.mark.asyncio
async def test_happy_path_common_shares_recommendation_submits_order_and_logs_pick(
    monkeypatch, isolated_picks_log_path, caplog
):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    caplog.set_level("INFO", logger="webull_trader")

    response_payload = {"order_id": "order-1", "status": "accepted", "client_order_id": "cid-1"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-1")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock()
    broker = WebullBroker(trader)
    execution_results = []
    original_place_stock_order = broker.place_stock_order
    broker.place_stock_order = MagicMock(
        side_effect=lambda order, weighting=None: execution_results.append(
            original_place_stock_order(order, weighting=weighting)
        )
        or execution_results[-1]
    )
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "signals": [build_signal_payload("AAPL", "BUY", confidence=0.95, weight_percent=None)],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(
        build_message(FROZEN_COMMON_SHARES_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID)
    )

    trader.order_api.place_order.assert_called_once()
    place_call_kwargs = trader.order_api.place_order.call_args.kwargs
    assert place_call_kwargs["account_id"] == "paper-account-1"
    assert place_call_kwargs["side"] == "BUY"
    assert place_call_kwargs["instrument_id"] == "AAPL_ID"

    assert len(execution_results) == 1
    assert execution_results[0].success is True
    assert execution_results[0].order_id == "order-1"
    assert execution_results[0].raw["order_id"] == "order-1"
    assert execution_results[0].raw["status"] == "accepted"
    assert any("Placing BUY" in message and "UAT/PAPER" in message for message in caplog.messages)
    assert any("Order placed:" in message for message in caplog.messages)

    lines = isolated_picks_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    log_entry = json.loads(lines[0])
    assert log_entry["message"] == FROZEN_COMMON_SHARES_MESSAGE
    assert log_entry["ai_parsed_signals"]["signals"][0]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_options_only_recommendation_does_not_submit_stock_order(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "options_enabled", False)

    signal = build_signal_payload("AAPL", "BUY", confidence=0.9, weight_percent=None)
    signal["vehicles"] = [
        {
            "type": "OPTION",
            "enabled": True,
            "intent": "EXECUTE",
            "side": "BUY",
            "option_type": "CALL",
            "strike": 200.0,
            "expiry": "2026-03-20",
        }
    ]

    response_payload = {"order_id": "unused-order", "status": "accepted"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-1")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock()
    broker = WebullBroker(trader)
    execution_results = []
    original_place_stock_order = broker.place_stock_order
    broker.place_stock_order = MagicMock(
        side_effect=lambda order, weighting=None: execution_results.append(
            original_place_stock_order(order, weighting=weighting)
        )
        or execution_results[-1]
    )
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(return_value={"signals": [signal], "meta": {"status": "ok"}})

    await client.on_message(build_message(FROZEN_OPTIONS_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.order_api.place_order.assert_not_called()
    assert execution_results == []
    lines = isolated_picks_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    log_entry = json.loads(lines[0])
    assert log_entry["ai_parsed_signals"]["signals"][0]["vehicles"][0]["type"] == "OPTION"


@pytest.mark.asyncio
async def test_common_plus_options_recommendation_submits_stock_order(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "options_enabled", False)

    signal = build_signal_payload("TSLA", "BUY", confidence=0.93, weight_percent=None)
    signal["vehicles"] = [
        {
            "type": "OPTION",
            "enabled": True,
            "intent": "EXECUTE",
            "side": "BUY",
            "option_type": "CALL",
            "strike": 250.0,
            "expiry": "2026-06-19",
        },
        {"type": "STOCK", "enabled": True, "intent": "EXECUTE", "side": "BUY"},
    ]

    response_payload = {"order_id": "mixed-order", "status": "accepted", "client_order_id": "cid-mixed"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-2")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "TSLA_ID", "last_price": 200.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader.get_current_stock_quote = MagicMock(return_value=200.0)
    trader._enforce_margin_buffer = MagicMock()
    broker = WebullBroker(trader)
    execution_results = []
    original_place_stock_order = broker.place_stock_order
    broker.place_stock_order = MagicMock(
        side_effect=lambda order, weighting=None: execution_results.append(
            original_place_stock_order(order, weighting=weighting)
        )
        or execution_results[-1]
    )
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(return_value={"signals": [signal], "meta": {"status": "ok"}})

    await client.on_message(build_message(FROZEN_MIXED_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.order_api.place_order.assert_called_once()
    place_call_kwargs = trader.order_api.place_order.call_args.kwargs
    assert place_call_kwargs["account_id"] == "paper-account-2"
    assert place_call_kwargs["instrument_id"] == "TSLA_ID"
    assert place_call_kwargs["side"] == "BUY"
    assert len(execution_results) == 1
    assert execution_results[0].success is True
    assert execution_results[0].order_id == "mixed-order"
    assert execution_results[0].raw["status"] == "accepted"
    lines = isolated_picks_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


@pytest.mark.asyncio
async def test_options_only_recommendation_submits_option_order_when_enabled(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "options_enabled", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_options", False)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "fallback_to_default_amount_on_weighting_failure", False)

    signal = build_signal_payload("AAPL", "BUY", confidence=0.9, weight_percent=None)
    signal["vehicles"] = [
        {
            "type": "OPTION",
            "enabled": True,
            "intent": "EXECUTE",
            "side": "BUY",
            "option_type": "CALL",
            "strike": 200.0,
            "expiry": "2026-03-20",
        }
    ]

    stock_response_payload = {"order_id": "unused-stock-order", "status": "accepted"}
    option_preview_payload = {"estimated_cost": "1.00", "estimated_transaction_fee": "0.00", "currency": "USD"}
    option_place_payload = {"order_id": "option-order-1", "status": "accepted"}
    fake_stock_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: stock_response_payload)
    fake_option_preview_response = SimpleNamespace(
        status_code=200, text='{"ok": true}', json=lambda: option_preview_payload
    )
    fake_option_place_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: option_place_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_stock_response))
    trader.order_v2_api = SimpleNamespace(
        preview_option=MagicMock(return_value=fake_option_preview_response),
        place_option=MagicMock(return_value=fake_option_place_response),
    )
    trader.resolve_account_id = MagicMock(return_value="paper-account-1")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock()
    broker = WebullBroker(trader)
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(return_value={"signals": [signal], "meta": {"status": "ok"}})

    await client.on_message(build_message(FROZEN_OPTIONS_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.order_api.place_order.assert_not_called()
    trader.order_v2_api.preview_option.assert_called_once()
    trader.order_v2_api.place_option.assert_called_once()
    preview_call_args = trader.order_v2_api.preview_option.call_args.args
    place_call_args = trader.order_v2_api.place_option.call_args.args
    assert preview_call_args[0] == "paper-account-1"
    assert place_call_args[0] == "paper-account-1"
    assert len(preview_call_args[1]) == 1
    assert len(place_call_args[1]) == 1
    assert place_call_args[1][0]["legs"][0]["instrument_type"] == "OPTION"
    assert place_call_args[1][0]["legs"][0]["option_type"] == "CALL"
    assert place_call_args[1][0]["legs"][0]["option_expire_date"] == "2026-03-20"
    assert place_call_args[1][0]["legs"][0]["init_exp_date"] == "2026-03-20"
    lines = isolated_picks_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


@pytest.mark.asyncio
async def test_mixed_recommendation_submits_stock_and_option_when_enabled(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "options_enabled", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_options", False)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "fallback_to_default_amount_on_weighting_failure", False)

    signal = build_signal_payload("TSLA", "BUY", confidence=0.93, weight_percent=None)
    signal["vehicles"] = [
        {
            "type": "OPTION",
            "enabled": True,
            "intent": "EXECUTE",
            "side": "BUY",
            "option_type": "CALL",
            "strike": 250.0,
            "expiry": "2026-06-19",
        },
        {"type": "STOCK", "enabled": True, "intent": "EXECUTE", "side": "BUY"},
    ]

    stock_response_payload = {"order_id": "mixed-stock-order", "status": "accepted", "client_order_id": "cid-mixed"}
    option_preview_payload = {"estimated_cost": "1.00", "estimated_transaction_fee": "0.00", "currency": "USD"}
    option_place_payload = {"order_id": "mixed-option-order", "status": "accepted"}
    fake_stock_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: stock_response_payload)
    fake_option_preview_response = SimpleNamespace(
        status_code=200, text='{"ok": true}', json=lambda: option_preview_payload
    )
    fake_option_place_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: option_place_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_stock_response))
    trader.order_v2_api = SimpleNamespace(
        preview_option=MagicMock(return_value=fake_option_preview_response),
        place_option=MagicMock(return_value=fake_option_place_response),
    )
    trader.resolve_account_id = MagicMock(return_value="paper-account-2")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "TSLA_ID", "last_price": 200.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader.get_current_stock_quote = MagicMock(return_value=200.0)
    trader._enforce_margin_buffer = MagicMock()
    broker = WebullBroker(trader)
    execution_results = []
    original_place_stock_order = broker.place_stock_order
    broker.place_stock_order = MagicMock(
        side_effect=lambda order, weighting=None: execution_results.append(
            original_place_stock_order(order, weighting=weighting)
        )
        or execution_results[-1]
    )
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(return_value={"signals": [signal], "meta": {"status": "ok"}})

    await client.on_message(build_message(FROZEN_MIXED_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.order_api.place_order.assert_called_once()
    trader.order_v2_api.preview_option.assert_called_once()
    trader.order_v2_api.place_option.assert_called_once()
    assert len(execution_results) == 1
    assert execution_results[0].success is True
    lines = isolated_picks_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


@pytest.mark.asyncio
async def test_weighted_option_recommendation_passes_weighting_for_option_sizing(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "options_enabled", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_options", False)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "fallback_to_default_amount_on_weighting_failure", False)

    signal = build_signal_payload("NVDA", "BUY", confidence=0.94, weight_percent=10.0)
    signal["vehicles"] = [
        {
            "type": "OPTION",
            "enabled": True,
            "intent": "EXECUTE",
            "side": "BUY",
            "option_type": "CALL",
            "strike": 150.0,
            "expiry": "2026-06-19",
        }
    ]

    option_preview_one_contract_payload = {"estimated_cost": "125.00", "estimated_transaction_fee": "0.00", "currency": "USD"}
    option_preview_sized_payload = {"estimated_cost": "500.00", "estimated_transaction_fee": "0.00", "currency": "USD"}
    option_place_payload = {"order_id": "weighted-option-order", "status": "accepted"}
    fake_option_preview_one_contract_response = SimpleNamespace(
        status_code=200, text='{"ok": true}', json=lambda: option_preview_one_contract_payload
    )
    fake_option_preview_sized_response = SimpleNamespace(
        status_code=200, text='{"ok": true}', json=lambda: option_preview_sized_payload
    )
    fake_option_place_response = SimpleNamespace(
        status_code=200, text='{"ok": true}', json=lambda: option_place_payload
    )

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock())
    trader.order_v2_api = SimpleNamespace(
        preview_option=MagicMock(
            side_effect=[fake_option_preview_one_contract_response, fake_option_preview_sized_response]
        ),
        place_option=MagicMock(return_value=fake_option_place_response),
    )
    trader.resolve_account_id = MagicMock(return_value="paper-account-5")
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader._enforce_margin_buffer = MagicMock()
    broker = WebullBroker(trader)
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(return_value={"signals": [signal], "meta": {"status": "ok"}})

    await client.on_message(build_message(FROZEN_WEIGHTED_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.order_api.place_order.assert_not_called()
    trader._get_buying_power.assert_called_once()
    trader.order_v2_api.preview_option.assert_called()
    trader.order_v2_api.place_option.assert_called_once()
    place_call_args = trader.order_v2_api.place_option.call_args.args
    assert place_call_args[0] == "paper-account-5"
    assert place_call_args[1][0]["quantity"] == "4"
    lines = isolated_picks_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


@pytest.mark.asyncio
async def test_no_recommendation_payload_produces_no_order_and_no_pick_log(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)

    response_payload = {"order_id": "unused-order", "status": "accepted"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-1")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "AAPL_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock()
    broker = WebullBroker(trader)
    execution_results = []
    original_place_stock_order = broker.place_stock_order
    broker.place_stock_order = MagicMock(
        side_effect=lambda order, weighting=None: execution_results.append(
            original_place_stock_order(order, weighting=weighting)
        )
        or execution_results[-1]
    )
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(return_value={"signals": [], "meta": {"status": "ok"}})

    await client.on_message(build_message(FROZEN_NO_ACTION_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID))

    trader.order_api.place_order.assert_not_called()
    client.notifier.notify.assert_not_called()
    assert execution_results == []
    assert not isolated_picks_log_path.exists()


@pytest.mark.asyncio
async def test_weighted_recommendation_passes_weighting_to_webull_trader(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_buys", False)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "fallback_to_default_amount_on_weighting_failure", False)

    response_payload = {"order_id": "weighted-order", "status": "accepted", "client_order_id": "cid-weighted"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-3")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "NVDA_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=8000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=8000.0)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock()

    broker = WebullBroker(trader)
    execution_results = []
    original_place_stock_order = broker.place_stock_order
    broker.place_stock_order = MagicMock(
        side_effect=lambda order, weighting=None: execution_results.append(
            original_place_stock_order(order, weighting=weighting)
        )
        or execution_results[-1]
    )
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "signals": [build_signal_payload("NVDA", "BUY", confidence=0.94, weight_percent=12.5)],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(build_message(FROZEN_WEIGHTED_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID))

    trader._get_buying_power.assert_called_once()
    trader.order_api.place_order.assert_called_once()
    place_call_kwargs = trader.order_api.place_order.call_args.kwargs
    assert place_call_kwargs["account_id"] == "paper-account-3"
    assert place_call_kwargs["instrument_id"] == "NVDA_ID"
    assert place_call_kwargs["qty"] == 10
    assert len(execution_results) == 1
    assert execution_results[0].success is True
    assert execution_results[0].order_id == "weighted-order"
    assert execution_results[0].raw["status"] == "accepted"
    assert isolated_picks_log_path.exists()


@pytest.mark.asyncio
async def test_dollar_amount_recommendation_uses_default_notional_path(monkeypatch, isolated_picks_log_path):
    monkeypatch.setattr(order_planner_module, "is_regular_market_session", lambda _: True)
    monkeypatch.setitem(discord_client_module.TRADING_CONFIG, "use_market_orders", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "force_default_amount_for_buys", True)
    monkeypatch.setitem(webull_trader_module.TRADING_CONFIG, "default_amount", 750.0)

    response_payload = {"order_id": "notional-order", "status": "accepted", "client_order_id": "cid-notional"}
    fake_response = SimpleNamespace(status_code=200, text='{"ok": true}', json=lambda: response_payload)

    trader = WebullTrader.__new__(WebullTrader)
    trader.paper_trade = True
    assert trader.paper_trade is True
    trader.order_api = SimpleNamespace(place_order=MagicMock(return_value=fake_response))
    trader.resolve_account_id = MagicMock(return_value="paper-account-4")
    trader.get_instrument = MagicMock(return_value=[{"instrument_id": "MSFT_ID", "last_price": 100.0}])
    trader._get_account_balance_contract = MagicMock(
        return_value=AccountBalanceResponse(
            total_market_value=10000.0,
            account_currency_assets=[AccountCurrencyAsset(net_liquidation_value=9000.0, cash_power=5000.0)],
        )
    )
    trader._get_buying_power = MagicMock(return_value=5000.0)
    trader.get_current_stock_quote = MagicMock(return_value=100.0)
    trader._enforce_margin_buffer = MagicMock()

    broker = WebullBroker(trader)
    execution_results = []
    original_place_stock_order = broker.place_stock_order
    broker.place_stock_order = MagicMock(
        side_effect=lambda order, weighting=None: execution_results.append(
            original_place_stock_order(order, weighting=weighting)
        )
        or execution_results[-1]
    )
    client = StockMonitorClient(broker=broker, trading_account=trader)
    type(client.client).user = SimpleNamespace(id=999)
    client.notifier.notify = MagicMock()
    client.parser.parse = MagicMock(
        return_value={
            "signals": [build_signal_payload("MSFT", "BUY", confidence=0.91, weight_percent=None)],
            "meta": {"status": "ok"},
        }
    )

    await client.on_message(
        build_message(FROZEN_DOLLAR_AMOUNT_MESSAGE, author_id=321, channel_id=TEST_CHANNEL_ID)
    )

    trader.order_api.place_order.assert_called_once()
    place_call_kwargs = trader.order_api.place_order.call_args.kwargs
    assert place_call_kwargs["account_id"] == "paper-account-4"
    assert place_call_kwargs["instrument_id"] == "MSFT_ID"
    assert place_call_kwargs["qty"] == 7
    assert len(execution_results) == 1
    assert execution_results[0].success is True
    assert execution_results[0].order_id == "notional-order"
    assert execution_results[0].raw["status"] == "accepted"
    assert isolated_picks_log_path.exists()
