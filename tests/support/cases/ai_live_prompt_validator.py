"""Scenario matrix for live AI prompt-to-contract validation."""

from tests.data.stocktalk_real_messages import MESSAGE_FIXTURES


COMMON_SHARES_MESSAGE = MESSAGE_FIXTURES["frozen_common_shares"]
OPTIONS_ONLY_MESSAGE = MESSAGE_FIXTURES["frozen_options_only"]
REAL_MIXED_MESSAGE = MESSAGE_FIXTURES["real_gldd_shipbuilding_dredge"]
REAL_NO_ACTION_MESSAGE = MESSAGE_FIXTURES["real_portfolio_update_no_action"]
WEIGHTED_MESSAGE = MESSAGE_FIXTURES["frozen_weighted"]
DOLLAR_STYLE_MESSAGE = MESSAGE_FIXTURES["frozen_dollar_amount"]
IRDM_OPTIONS_MESSAGE = MESSAGE_FIXTURES["real_irdm_options"]
MITK_POSITION_MESSAGE = MESSAGE_FIXTURES["real_mitk_common_position"]
ITRI_COMMON_MESSAGE = MESSAGE_FIXTURES["real_itri_weighted_common"]


LIVE_PROMPT_VALIDATOR_CASES = [
    (
        "common_shares_synthetic",
        COMMON_SHARES_MESSAGE.author,
        COMMON_SHARES_MESSAGE.text,
        set(COMMON_SHARES_MESSAGE.expected_tickers),
        {"STOCK"},
        "all",
        False,
        False,
        False,
    ),
    (
        "options_only_synthetic_options_enabled",
        OPTIONS_ONLY_MESSAGE.author,
        OPTIONS_ONLY_MESSAGE.text,
        set(OPTIONS_ONLY_MESSAGE.expected_tickers),
        {"OPTION"},
        "all",
        False,
        False,
        True,
    ),
    (
        "mixed_commons_options_real",
        REAL_MIXED_MESSAGE.author,
        REAL_MIXED_MESSAGE.text,
        set(REAL_MIXED_MESSAGE.expected_tickers),
        {"STOCK", "OPTION"},
        "all",
        False,
        False,
        True,
    ),
    (
        "no_action_real",
        REAL_NO_ACTION_MESSAGE.author,
        REAL_NO_ACTION_MESSAGE.text,
        set(),
        set(),
        "all",
        True,
        False,
        False,
    ),
    (
        "weighted_recommendation_synthetic",
        WEIGHTED_MESSAGE.author,
        WEIGHTED_MESSAGE.text,
        set(WEIGHTED_MESSAGE.expected_tickers),
        {"STOCK"},
        "all",
        False,
        True,
        False,
    ),
    (
        "dollar_style_recommendation_synthetic",
        DOLLAR_STYLE_MESSAGE.author,
        DOLLAR_STYLE_MESSAGE.text,
        set(DOLLAR_STYLE_MESSAGE.expected_tickers),
        {"STOCK"},
        "all",
        False,
        False,
        False,
    ),
    (
        "irdm_options_real_options_enabled",
        IRDM_OPTIONS_MESSAGE.author,
        IRDM_OPTIONS_MESSAGE.text,
        set(IRDM_OPTIONS_MESSAGE.expected_tickers),
        {"OPTION"},
        "all",
        False,
        True,
        True,
    ),
    (
        "mitk_position_real",
        MITK_POSITION_MESSAGE.author,
        MITK_POSITION_MESSAGE.text,
        set(MITK_POSITION_MESSAGE.expected_tickers),
        {"STOCK"},
        "all",
        False,
        False,
        False,
    ),
    (
        "itri_common_weighted_real",
        ITRI_COMMON_MESSAGE.author,
        ITRI_COMMON_MESSAGE.text,
        set(ITRI_COMMON_MESSAGE.expected_tickers),
        {"STOCK"},
        "all",
        False,
        True,
        False,
    ),
]
