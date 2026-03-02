import os
from typing import Any, Sequence


def _case_should_pick(case: Any) -> bool:
    if hasattr(case, "should_pick"):
        return bool(case.should_pick)
    return bool(case[3])


def select_live_cases(cases: Sequence[Any]) -> list[Any]:
    if os.getenv("TEST_AI_SCOPE", "sample").strip().lower() == "full":
        return list(cases)
    return [case for case in cases if _case_should_pick(case)][:1]
