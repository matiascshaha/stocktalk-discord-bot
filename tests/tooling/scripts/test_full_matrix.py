from scripts.quality.run_full_matrix import _select_scenarios, build_scenarios


def test_build_scenarios_defaults():
    scenarios = build_scenarios(ai_scope="full", skip_discord_live=False, skip_webull_prod_write=False)
    names = [scenario.name for scenario in scenarios]
    assert names == [
        "deterministic",
        "ai_live_smoke",
        "ai_pipeline_live",
        "webull_read_paper",
        "webull_write_paper",
        "webull_read_production",
        "webull_write_production",
        "discord_live_smoke",
    ]


def test_build_scenarios_with_skips():
    scenarios = build_scenarios(ai_scope="sample", skip_discord_live=True, skip_webull_prod_write=True)
    names = [scenario.name for scenario in scenarios]
    assert "webull_write_production" not in names
    assert "discord_live_smoke" not in names

    pipeline = next(s for s in scenarios if s.name == "ai_pipeline_live")
    assert pipeline.env_overrides["TEST_AI_SCOPE"] == "sample"


def test_select_scenarios_subset_order():
    scenarios = build_scenarios(ai_scope="full", skip_discord_live=False, skip_webull_prod_write=False)
    selected = _select_scenarios(scenarios, "webull_read_paper,deterministic")
    names = [scenario.name for scenario in selected]
    assert names == ["webull_read_paper", "deterministic"]
