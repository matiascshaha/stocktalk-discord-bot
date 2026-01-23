import os
import pytest

from src.ai_parser import AIParser
from tests.data.stocktalk_real_messages import REAL_MESSAGES


def force_fallback(p: AIParser):
    p.client = None
    p.provider = None
    return p


@pytest.fixture()
def parser_offline():
    return force_fallback(AIParser())


@pytest.fixture()
def parser_live():
    return AIParser()


@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", REAL_MESSAGES)
def test_offline(parser_offline, msg_id, author, text, should_pick, tickers):
    picks = parser_offline.parse(text, author)

    if not should_pick:
        assert picks == [], f"{msg_id} should not produce picks"
        return

    assert picks, f"{msg_id} should produce picks"
    found = {p["ticker"] for p in picks}
    for t in tickers:
        assert t in found


@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", REAL_MESSAGES)
def test_live_ai(parser_live, msg_id, author, text, should_pick, tickers):
    if os.getenv("RUN_LIVE_AI_TESTS") != "1":
        pytest.skip()

    picks = parser_live.parse(text, author)

    if not should_pick:
        assert picks == []
        return

    assert picks
    found = {p["ticker"] for p in picks}
    for t in tickers:
        assert t in found
