import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from config.settings import CHANNEL_ID, DISCORD_TOKEN


@pytest.mark.smoke
@pytest.mark.live
@pytest.mark.discord_live
def test_discord_live_smoke():
    if os.getenv("TEST_DISCORD_LIVE", "0") != "1":
        pytest.skip("TEST_DISCORD_LIVE != 1")

    if not DISCORD_TOKEN or not CHANNEL_ID:
        pytest.skip("Discord token/channel are not configured")

    import discord

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "discord_live_smoke.json"

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "channel_id": str(CHANNEL_ID),
        "message_count": 0,
        "error": None,
    }

    async def _run():
        if hasattr(discord, "Intents"):
            intents = discord.Intents.default()
            intents.message_content = True
            client = discord.Client(intents=intents)
        else:
            client = discord.Client()

        done = asyncio.Event()

        @client.event
        async def on_ready():
            try:
                channel = client.get_channel(CHANNEL_ID)
                if not channel:
                    result["error"] = f"Channel {CHANNEL_ID} not found"
                    return

                count = 0
                async for _msg in channel.history(limit=5):
                    count += 1
                result["message_count"] = count
                result["status"] = "passed"
            except Exception as exc:  # pragma: no cover - live smoke diagnostic
                result["error"] = str(exc)
            finally:
                done.set()
                await client.close()

        await client.start(DISCORD_TOKEN)
        await done.wait()

    try:
        asyncio.run(asyncio.wait_for(_run(), timeout=20))
    except Exception as exc:  # pragma: no cover - live smoke diagnostic
        result["error"] = str(exc)

    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert result["status"] == "passed", result["error"] or "Discord live smoke failed"
