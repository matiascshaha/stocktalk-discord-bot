from unittest.mock import MagicMock

import pytest

import src.brokerages.factory as broker_factory_module
from src.brokerages.composite.broker import CompositeTradingBroker
from src.brokerages.factory import BrokerRuntime, create_broker_runtime


pytestmark = [pytest.mark.unit]


def test_create_broker_runtime_returns_none_when_auto_trade_disabled():
    runtime = create_broker_runtime(
        trading_config={"auto_trade": False},
        webull_config={},
        public_config={},
    )

    assert runtime is None


def test_create_broker_runtime_routes_webull_builder_with_legacy_broker_key(monkeypatch):
    sentinel_runtime = BrokerRuntime(broker=MagicMock(), trading_account=MagicMock())
    monkeypatch.setattr(broker_factory_module, "_build_webull_runtime", MagicMock(return_value=sentinel_runtime))

    runtime = create_broker_runtime(
        trading_config={"auto_trade": True, "broker": "webull"},
        webull_config={"app_key": "key", "app_secret": "secret"},
    )

    assert runtime is sentinel_runtime


def test_create_broker_runtime_composes_yahoo_quotes_with_webull_execution(monkeypatch):
    execution_broker = MagicMock(name="execution-broker")
    execution_runtime = BrokerRuntime(broker=execution_broker, trading_account=MagicMock(name="acct"))
    yahoo_quote_provider = MagicMock(name="yahoo-quote-provider")

    monkeypatch.setattr(broker_factory_module, "_build_webull_runtime", MagicMock(return_value=execution_runtime))
    monkeypatch.setattr(broker_factory_module, "YahooQuoteProvider", MagicMock(return_value=yahoo_quote_provider))

    runtime = create_broker_runtime(
        trading_config={
            "auto_trade": True,
            "execution_provider": "webull",
            "quote_provider": "yahoo",
        },
        webull_config={"app_key": "key", "app_secret": "secret"},
    )

    assert isinstance(runtime, BrokerRuntime)
    assert isinstance(runtime.broker, CompositeTradingBroker)
    assert runtime.trading_account is execution_runtime.trading_account
    assert runtime.broker._execution_broker is execution_broker
    assert runtime.broker._quote_provider is yahoo_quote_provider


def test_create_broker_runtime_rejects_execution_provider_that_is_not_implemented():
    with pytest.raises(ValueError, match="Execution provider 'public' is configured but not implemented"):
        create_broker_runtime(
            trading_config={"auto_trade": True, "execution_provider": "public"},
            webull_config={},
            public_config={},
        )


def test_create_broker_runtime_rejects_unknown_quote_provider():
    with pytest.raises(ValueError, match="Unsupported trading quote provider 'unknown'"):
        create_broker_runtime(
            trading_config={
                "auto_trade": True,
                "execution_provider": "webull",
                "quote_provider": "unknown",
            },
            webull_config={"app_key": "key", "app_secret": "secret"},
            public_config={},
        )


def test_build_webull_runtime_uses_env_fallback_for_credentials(monkeypatch):
    fake_trader = MagicMock()
    fake_trader.login.return_value = True
    fake_webull_broker = MagicMock(name="webull-broker")
    monkeypatch.setenv("WEBULL_APP_KEY", "env-key")
    monkeypatch.setenv("WEBULL_APP_SECRET", "env-secret")
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "env-account")
    monkeypatch.setattr(broker_factory_module, "WebullTrader", MagicMock(return_value=fake_trader))
    monkeypatch.setattr(broker_factory_module, "WebullBroker", MagicMock(return_value=fake_webull_broker))

    runtime = broker_factory_module._build_webull_runtime(
        trading_config={"paper_trade": False},
        webull_config={},
    )

    assert isinstance(runtime, BrokerRuntime)
    assert runtime.broker is fake_webull_broker
    assert runtime.trading_account is fake_trader
    broker_factory_module.WebullTrader.assert_called_once_with(
        app_key="env-key",
        app_secret="env-secret",
        paper_trade=False,
        region="US",
        account_id="env-account",
    )


def test_build_webull_runtime_uses_test_credentials_in_paper_mode(monkeypatch):
    fake_trader = MagicMock()
    fake_trader.login.return_value = True
    monkeypatch.setattr(broker_factory_module, "WebullTrader", MagicMock(return_value=fake_trader))
    monkeypatch.setattr(broker_factory_module, "WebullBroker", MagicMock(return_value="broker"))

    runtime = broker_factory_module._build_webull_runtime(
        trading_config={"paper_trade": True},
        webull_config={
            "test_app_key": "paper-key",
            "test_app_secret": "paper-secret",
            "test_account_id": "paper-account",
            "region": "US",
        },
    )

    assert runtime is not None
    broker_factory_module.WebullTrader.assert_called_once_with(
        app_key="paper-key",
        app_secret="paper-secret",
        paper_trade=True,
        region="US",
        account_id="paper-account",
    )


def test_build_webull_runtime_returns_none_when_login_fails(monkeypatch):
    fake_trader = MagicMock()
    fake_trader.login.return_value = False
    monkeypatch.setattr(broker_factory_module, "WebullTrader", MagicMock(return_value=fake_trader))
    monkeypatch.setattr(broker_factory_module, "WebullBroker", MagicMock())

    runtime = broker_factory_module._build_webull_runtime(
        trading_config={"paper_trade": False},
        webull_config={"app_key": "key", "app_secret": "secret"},
    )

    assert runtime is None
    broker_factory_module.WebullBroker.assert_not_called()


def test_build_webull_runtime_requires_credentials(monkeypatch):
    monkeypatch.delenv("WEBULL_APP_KEY", raising=False)
    monkeypatch.delenv("WEBULL_APP_SECRET", raising=False)
    with pytest.raises(ValueError, match="Webull credentials are required"):
        broker_factory_module._build_webull_runtime(
            trading_config={"paper_trade": False},
            webull_config={"app_key": "", "app_secret": None},
        )
