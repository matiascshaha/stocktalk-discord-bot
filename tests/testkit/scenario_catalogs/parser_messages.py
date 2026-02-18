from dataclasses import dataclass
from typing import FrozenSet, Tuple

from tests.testkit.datasets.stocktalk_real_messages import REAL_MESSAGES
from tests.testkit.scenario_catalogs.live_scope import select_live_cases


@dataclass(frozen=True)
class ParserMessageCase:
    case_id: int
    author: str
    text: str
    should_pick: bool
    tickers: FrozenSet[str]


def _build_case(raw_case: tuple) -> ParserMessageCase:
    case_id, author, text, should_pick, tickers = raw_case
    return ParserMessageCase(
        case_id=int(case_id),
        author=str(author),
        text=str(text),
        should_pick=bool(should_pick),
        tickers=frozenset(tickers),
    )


PARSER_MESSAGE_CASES: Tuple[ParserMessageCase, ...] = tuple(_build_case(raw_case) for raw_case in REAL_MESSAGES)

PARSER_MESSAGE_PARAMS: Tuple[tuple, ...] = tuple(
    (case.case_id, case.author, case.text, case.should_pick, set(case.tickers))
    for case in PARSER_MESSAGE_CASES
)

LIVE_PARSER_MESSAGE_PARAMS: Tuple[tuple, ...] = tuple(select_live_cases(PARSER_MESSAGE_PARAMS))
