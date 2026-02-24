import pytest

from tests.support.matrix import has_real_credential

pytestmark = [pytest.mark.unit]


pytestmark = pytest.mark.unit


def test_has_real_credential_rejects_empty():
    assert has_real_credential("") is False
    assert has_real_credential("   ") is False


def test_has_real_credential_rejects_placeholders():
    assert has_real_credential("your_webull_app_key") is False
    assert has_real_credential("sk-proj-your_openai_api_key_here") is False
    assert has_real_credential("<replace-me>") is False


def test_has_real_credential_accepts_non_placeholder():
    assert has_real_credential("sk-proj-abc1234567890-real") is True
