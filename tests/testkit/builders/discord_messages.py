from types import SimpleNamespace


TEST_CHANNEL_ID = 123456789
WRONG_CHANNEL_ID = TEST_CHANNEL_ID + 1


def build_message(content: str, author_id: int, channel_id: int):
    author = SimpleNamespace(id=author_id, name=f"user-{author_id}")
    channel = SimpleNamespace(id=channel_id)
    return SimpleNamespace(
        content=content,
        author=author,
        channel=channel,
        jump_url="https://discord.com/mock/message",
    )
