import pytest

from scripts.quality.quality_flags import resolve_test_flags


pytestmark = [pytest.mark.integration, pytest.mark.system]


def test_resolve_test_flags_local_defaults():
    flags = resolve_test_flags({}, default_mode="local")
    assert flags.mode == "local"
    assert flags.ai_live is False
    assert flags.discord_live is False
    assert flags.webull_read is False
    assert flags.webull_write is False
    assert flags.webull_env == "paper"
    assert flags.ai_scope == "sample"


def test_resolve_test_flags_smoke_defaults():
    flags = resolve_test_flags({"TEST_MODE": "smoke"}, default_mode="local")
    assert flags.mode == "smoke"
    assert flags.ai_live is True
    assert flags.discord_live is True
    assert flags.webull_read is True
    assert flags.webull_write is False
    assert flags.webull_env == "production"


def test_resolve_test_flags_explicit_override():
    flags = resolve_test_flags(
        {
            "TEST_MODE": "local",
            "TEST_AI_LIVE": "1",
            "TEST_WEBULL_WRITE": "1",
            "TEST_WEBULL_ENV": "paper",
            "TEST_AI_SCOPE": "full",
        },
        default_mode="local",
    )
    assert flags.ai_live is True
    assert flags.webull_write is True
    assert flags.webull_env == "paper"
    assert flags.ai_scope == "full"


def test_resolve_test_flags_invalid_mode():
    with pytest.raises(ValueError):
        resolve_test_flags({"TEST_MODE": "invalid"}, default_mode="local")


def test_resolve_test_flags_invalid_bool():
    with pytest.raises(ValueError):
        resolve_test_flags({"TEST_AI_LIVE": "maybe"}, default_mode="local")
