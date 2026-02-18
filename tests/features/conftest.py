import pytest

import src.discord_client as discord_client_module
from tests.testkit.builders.discord_messages import TEST_CHANNEL_ID


@pytest.fixture(autouse=True)
def stable_channel_id(monkeypatch):
    monkeypatch.setattr(discord_client_module, "CHANNEL_ID", TEST_CHANNEL_ID)
