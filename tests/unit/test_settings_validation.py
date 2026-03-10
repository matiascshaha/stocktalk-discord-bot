import pytest

import config.settings as settings_module


pytestmark = [pytest.mark.unit]


def test_validate_config_rejects_unimplemented_execution_provider(monkeypatch):
    monkeypatch.setattr(settings_module, "DISCORD_TOKEN", "token")
    monkeypatch.setattr(settings_module, "CHANNEL_ID", 123)
    monkeypatch.setattr(settings_module, "AI_PROVIDER", "none")
    monkeypatch.setattr(
        settings_module,
        "TRADING_CONFIG",
        {
            "auto_trade": True,
            "execution_provider": "public",
            "quote_provider": "auto",
        },
    )
    monkeypatch.setattr(settings_module, "WEBULL_CONFIG", {"app_key": "", "app_secret": ""})

    errors = settings_module.validate_config()

    assert any("Execution provider 'public' is configured but not implemented" in error for error in errors)


def test_validate_config_accepts_webull_execution_with_yahoo_quote_provider(monkeypatch):
    monkeypatch.setattr(settings_module, "DISCORD_TOKEN", "token")
    monkeypatch.setattr(settings_module, "CHANNEL_ID", 123)
    monkeypatch.setattr(settings_module, "AI_PROVIDER", "none")
    monkeypatch.setattr(
        settings_module,
        "TRADING_CONFIG",
        {
            "auto_trade": True,
            "execution_provider": "webull",
            "quote_provider": "yahoo",
        },
    )
    monkeypatch.setattr(settings_module, "WEBULL_CONFIG", {"app_key": "k", "app_secret": "s"})

    errors = settings_module.validate_config()

    assert errors == []


def test_trading_config_exposes_independent_weighting_toggles():
    assert "weighting_stocks_enabled" in settings_module.TRADING_CONFIG
    assert "weighting_options_enabled" in settings_module.TRADING_CONFIG
    assert isinstance(settings_module.TRADING_CONFIG["weighting_stocks_enabled"], bool)
    assert isinstance(settings_module.TRADING_CONFIG["weighting_options_enabled"], bool)
