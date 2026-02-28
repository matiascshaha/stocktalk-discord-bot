import os

import pytest

import src.ai_parser as ai_parser_module
from src.ai_parser import AIParser
from src.models.parser_models import ParsedMessage
from tests.data.stocktalk_real_messages import REAL_PIPELINE_CASES, MessageFixture
from tests.support.cases.ai_live_prompt_validator import LIVE_PROMPT_VALIDATOR_CASES
from tests.support.matrix import ai_provider_has_credentials


pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.live, pytest.mark.parser]


@pytest.mark.parametrize("case", REAL_PIPELINE_CASES, ids=lambda case: case.scenario_id)
def test_live_ai_smoke(case: MessageFixture, ai_smoke_providers, configured_ai_provider):
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

    result = parser.parse(case.text, case.author)
    signals = result.get("signals", [])
    found = {s["ticker"] for s in signals if isinstance(s, dict) and s.get("ticker")}

    if case.should_pick:
        for ticker in case.expected_tickers:
            assert ticker in found, f"{case.scenario_id} missing ticker {ticker}"
    else:
        assert found == set(), f"{case.scenario_id} should not produce picks"


@pytest.mark.parametrize(
    "scenario_id, author, text, expected_tickers, expected_vehicle_types, vehicle_type_match, expects_no_action, requires_weight, options_enabled_override",
    LIVE_PROMPT_VALIDATOR_CASES,
)
def test_live_ai_prompt_contract_validator(
    scenario_id,
    author,
    text,
    expected_tickers,
    expected_vehicle_types,
    vehicle_type_match,
    expects_no_action,
    requires_weight,
    options_enabled_override,
    monkeypatch,
    ai_smoke_providers,
    configured_ai_provider,
):
    if os.getenv("TEST_AI_LIVE", "0") != "1":
        pytest.skip("TEST_AI_LIVE != 1")

    if configured_ai_provider == "none":
        pytest.skip("AI_PROVIDER=none")

    monkeypatch.setitem(ai_parser_module.TRADING_CONFIG, "options_enabled", bool(options_enabled_override))

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
    parsed = ParsedMessage.model_validate(result)

    assert parsed.contract_version == "1.0", scenario_id
    assert parsed.source.author == author, scenario_id
    assert parsed.source.message_text == text, scenario_id
    assert parsed.meta.provider == resolved_provider, scenario_id
    assert parser.options_enabled == bool(options_enabled_override), scenario_id

    tickers_found = {signal.ticker for signal in parsed.signals}
    vehicle_types_found = {
        vehicle.type for signal in parsed.signals for vehicle in signal.vehicles if getattr(vehicle, "type", None)
    }

    if expects_no_action:
        assert parsed.signals == [], scenario_id
        assert parsed.meta.status == "no_action", scenario_id
        return

    if not parser.options_enabled:
        assert not any(
            vehicle.type == "OPTION" and vehicle.enabled for signal in parsed.signals for vehicle in signal.vehicles
        ), f"{scenario_id} produced executable OPTION vehicle while options are disabled"
    else:
        if "OPTION" in expected_vehicle_types:
            assert any(
                vehicle.type == "OPTION" and vehicle.enabled for signal in parsed.signals for vehicle in signal.vehicles
            ), f"{scenario_id} expected at least one enabled OPTION vehicle"

    assert parsed.meta.status == "ok", scenario_id
    for ticker in expected_tickers:
        assert ticker in tickers_found, f"{scenario_id} missing ticker {ticker} in {sorted(tickers_found)}"

    if expected_vehicle_types:
        if vehicle_type_match == "all":
            for vehicle_type in expected_vehicle_types:
                assert (
                    vehicle_type in vehicle_types_found
                ), f"{scenario_id} missing vehicle type {vehicle_type} in {sorted(vehicle_types_found)}"
        else:
            assert (
                expected_vehicle_types & vehicle_types_found
            ), f"{scenario_id} expected one of {sorted(expected_vehicle_types)} in {sorted(vehicle_types_found)}"

    if requires_weight:
        assert any(
            signal.weight_percent is not None and signal.weight_percent > 0 for signal in parsed.signals
        ), f"{scenario_id} expected at least one positive weight_percent"
