import pytest

import src.discord_client as discord_client_module
from tests.support.factories.discord_messages import TEST_CHANNEL_ID


@pytest.fixture(autouse=True)
def stable_channel_id(monkeypatch):
    monkeypatch.setattr(discord_client_module, "CHANNEL_ID", TEST_CHANNEL_ID)


@pytest.fixture(autouse=True)
def stable_message_filters(monkeypatch):
    monkeypatch.setattr(discord_client_module, "ALLOW_ALL_CHANNELS_FOR_TESTING", False)
    monkeypatch.setattr(discord_client_module, "ALLOW_SELF_MESSAGES_FOR_TESTING", False)
