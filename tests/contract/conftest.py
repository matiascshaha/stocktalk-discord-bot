import pytest

from src.webull_trader import WebullTrader


@pytest.fixture()
def trader():
    return WebullTrader(
        app_key="dummy",
        app_secret="dummy",
        paper_trade=True,
        region="US",
        account_id="TEST_ACCOUNT",
    )
