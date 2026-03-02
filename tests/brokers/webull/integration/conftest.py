import pytest

import src.discord_client as discord_client_module
from tests.support.factories.discord_messages import TEST_CHANNEL_ID


@pytest.fixture(autouse=True)
def stable_discord_channel(monkeypatch):
    monkeypatch.setattr(discord_client_module, "CHANNEL_ID", TEST_CHANNEL_ID)


@pytest.fixture(autouse=True)
def isolated_picks_log_path(monkeypatch, tmp_path):
    log_path = tmp_path / "picks_log.jsonl"
    monkeypatch.setattr(discord_client_module, "PICKS_LOG_PATH", log_path)
    return log_path
