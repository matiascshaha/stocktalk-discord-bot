import os

import pytest

from src.ai_parser import AIParser
from tests.data.stocktalk_real_messages import REAL_MESSAGES
from tests.support.matrix import ai_provider_has_credentials


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.parametrize("msg_id, author, text, should_pick, tickers", REAL_MESSAGES)
def test_live_ai_smoke(msg_id, author, text, should_pick, tickers, ai_smoke_providers, configured_ai_provider):
    if os.getenv("TEST_AI_LIVE", "0") != "1":
        pytest.skip("TEST_AI_LIVE != 1")

    if configured_ai_provider == "none":
        pytest.skip("AI_PROVIDER=none")

    parser = AIParser()
    resolved_provider = (parser.provider or "").lower()
    if not resolved_provider:
        pytest.skip("No AI provider resolved by runtime configuration")

    if resolved_provider not in ai_smoke_providers:
        pytest.skip(
            f"Resolved provider '{resolved_provider}' is not enabled in TEST_AI_PROVIDERS={','.join(ai_smoke_providers)}"
        )

    if not ai_provider_has_credentials(resolved_provider):
        pytest.fail(f"Live AI smoke requires valid credentials for provider '{resolved_provider}'")

    result = parser.parse(text, author)
    picks = result.get("picks", [])
    found = {p["ticker"] for p in picks if isinstance(p, dict) and p.get("ticker")}

    if should_pick:
        for ticker in tickers:
            assert ticker in found, f"{msg_id} missing ticker {ticker}"
    else:
        assert found == set(), f"{msg_id} should not produce picks"
