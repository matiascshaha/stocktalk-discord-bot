import pytest

from src.brokerages.provider_registry import (
    resolve_execution_provider_name,
    resolve_quote_provider_name,
    validate_provider_split,
)


pytestmark = [pytest.mark.unit]


def test_resolve_execution_provider_prefers_explicit_execution_provider():
    name = resolve_execution_provider_name(
        {"execution_provider": "WEBULL", "broker": "public"}
    )
    assert name == "webull"


def test_resolve_execution_provider_falls_back_to_legacy_broker():
    name = resolve_execution_provider_name({"broker": "webull"})
    assert name == "webull"


def test_resolve_quote_provider_auto_maps_to_execution_provider():
    quote = resolve_quote_provider_name({"quote_provider": "auto"}, execution_provider="webull")
    assert quote == "webull"


def test_validate_provider_split_accepts_webull_execution_with_yahoo_quotes():
    assert validate_provider_split("webull", "yahoo") == []


def test_validate_provider_split_rejects_unknown_provider_names():
    errors = validate_provider_split("unknown", "webull")
    assert any("Unsupported trading execution provider 'unknown'" in error for error in errors)


def test_validate_provider_split_rejects_unimplemented_execution_provider():
    errors = validate_provider_split("public", "webull")
    assert any("Execution provider 'public' is configured but not implemented" in error for error in errors)


def test_validate_provider_split_rejects_unimplemented_quote_provider():
    errors = validate_provider_split("webull", "public")
    assert any("Quote provider 'public' is configured but not implemented" in error for error in errors)
