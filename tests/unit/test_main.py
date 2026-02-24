from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.main as main_module


pytestmark = [pytest.mark.unit]


def test_print_banner_outputs_title(capsys):
    main_module.print_banner()

    out = capsys.readouterr().out
    assert "Discord Stock Monitor" in out


def test_main_exits_when_config_invalid(monkeypatch):
    monkeypatch.setattr(main_module, "validate_config", MagicMock(return_value=["bad config"]))
    monkeypatch.setattr(main_module, "sys", SimpleNamespace(exit=MagicMock(side_effect=SystemExit(1))))

    with pytest.raises(SystemExit):
        main_module.main()


def test_main_runs_monitor_only_when_auto_trade_disabled(monkeypatch):
    fake_client = MagicMock()
    fake_client.run = MagicMock()
    monkeypatch.setattr(main_module, "validate_config", MagicMock(return_value=[]))
    monkeypatch.setattr(main_module, "TRADING_CONFIG", {"auto_trade": False})
    monkeypatch.setattr(main_module, "StockMonitorClient", MagicMock(return_value=fake_client))

    main_module.main()

    main_module.StockMonitorClient.assert_called_once_with(broker=None, trading_account=None)
    fake_client.run.assert_called_once()


def test_main_initializes_broker_runtime_when_auto_trade_enabled(monkeypatch):
    fake_client = MagicMock()
    fake_client.run = MagicMock()
    runtime = SimpleNamespace(broker="broker", trading_account="acct")
    monkeypatch.setattr(main_module, "validate_config", MagicMock(return_value=[]))
    monkeypatch.setattr(main_module, "TRADING_CONFIG", {"auto_trade": True})
    monkeypatch.setattr(main_module, "create_broker_runtime", MagicMock(return_value=runtime))
    monkeypatch.setattr(main_module, "StockMonitorClient", MagicMock(return_value=fake_client))

    main_module.main()

    main_module.create_broker_runtime.assert_called_once()
    main_module.StockMonitorClient.assert_called_once_with(broker="broker", trading_account="acct")


def test_main_exits_when_broker_runtime_initialization_fails(monkeypatch):
    monkeypatch.setattr(main_module, "validate_config", MagicMock(return_value=[]))
    monkeypatch.setattr(main_module, "TRADING_CONFIG", {"auto_trade": True})
    monkeypatch.setattr(main_module, "create_broker_runtime", MagicMock(side_effect=RuntimeError("boom")))
    monkeypatch.setattr(main_module, "sys", SimpleNamespace(exit=MagicMock(side_effect=SystemExit(1))))

    with pytest.raises(SystemExit):
        main_module.main()


def test_main_handles_keyboard_interrupt_without_exit(monkeypatch):
    fake_client = MagicMock()
    fake_client.run = MagicMock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(main_module, "validate_config", MagicMock(return_value=[]))
    monkeypatch.setattr(main_module, "TRADING_CONFIG", {"auto_trade": False})
    monkeypatch.setattr(main_module, "StockMonitorClient", MagicMock(return_value=fake_client))

    main_module.main()

    fake_client.run.assert_called_once()
