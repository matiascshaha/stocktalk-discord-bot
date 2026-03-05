import pytest

import tests.support.webull_smoke_helpers as webull_smoke_helpers


pytestmark = pytest.mark.unit


def test_known_webull_write_xfail_markers_include_account_trade_deny() -> None:
    assert "ACCOUNT_NOT_ALLOW_TRADE_CS_DENY" in webull_smoke_helpers.KNOWN_WEBULL_WRITE_XFAIL_MARKERS


def test_build_webull_smoke_trader_paper_mode_rejects_prod_credential_fallback(monkeypatch) -> None:
    monkeypatch.setenv("TEST_WEBULL_ENV", "paper")
    monkeypatch.setenv("WEBULL_APP_KEY", "prod_key")
    monkeypatch.setenv("WEBULL_APP_SECRET", "prod_secret")
    monkeypatch.delenv("WEBULL_TEST_APP_KEY", raising=False)
    monkeypatch.delenv("WEBULL_TEST_APP_SECRET", raising=False)
    monkeypatch.setitem(webull_smoke_helpers.WEBULL_CONFIG, "test_app_key", None)
    monkeypatch.setitem(webull_smoke_helpers.WEBULL_CONFIG, "test_app_secret", None)

    with pytest.raises(pytest.fail.Exception, match="Webull paper smoke requires valid credentials"):
        webull_smoke_helpers.build_webull_smoke_trader()


def test_build_webull_smoke_trader_paper_mode_prefers_test_credentials(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeTrader:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(webull_smoke_helpers, "WebullTrader", FakeTrader)
    monkeypatch.setenv("TEST_WEBULL_ENV", "paper")
    monkeypatch.setenv("WEBULL_TEST_APP_KEY", "paper_key")
    monkeypatch.setenv("WEBULL_TEST_APP_SECRET", "paper_secret")
    monkeypatch.setenv("WEBULL_TEST_ACCOUNT_ID", "paper_account")
    monkeypatch.setenv("WEBULL_APP_KEY", "prod_key")
    monkeypatch.setenv("WEBULL_APP_SECRET", "prod_secret")

    webull_smoke_helpers.build_webull_smoke_trader()

    assert captured["app_key"] == "paper_key"
    assert captured["app_secret"] == "paper_secret"
    assert captured["account_id"] == "paper_account"
    assert captured["paper_trade"] is True
