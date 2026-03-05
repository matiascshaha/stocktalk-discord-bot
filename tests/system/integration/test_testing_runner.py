import pytest

from scripts.testing.runner import build_profile_suites, resolve_profile_name


pytestmark = [pytest.mark.integration, pytest.mark.system]


def test_resolve_profile_name_supports_aliases():
    assert resolve_profile_name("quick") == "deterministic"
    assert resolve_profile_name("live") == "live-read"
    assert resolve_profile_name("night") == "night-probe"


def test_build_critical_profile_suites():
    suites = build_profile_suites("critical", ai_scope="sample", ack=None, python_bin="python")
    names = [suite.name for suite in suites]
    assert names == [
        "test_file_purity",
        "pathing_contracts",
        "parser_contracts",
        "discord_mocked_flow",
        "webull_paper_trade_flow",
        "webull_account_context",
        "webull_contract",
        "system_quality",
    ]


def test_build_all_profile_combines_deterministic_and_live_read():
    suites = build_profile_suites("all", ai_scope="sample", ack=None, python_bin="python")
    names = [suite.name for suite in suites]
    assert names == [
        "test_file_purity",
        "deterministic_all",
        "discord_live_smoke",
        "webull_read_smoke_paper",
    ]


def test_night_probe_requires_ack_value():
    with pytest.raises(ValueError, match="night-probe requires --ack YES_IM_LIVE"):
        build_profile_suites("night-probe", ai_scope="sample", ack=None, python_bin="python")

