import os
from typing import Sequence


def select_live_cases(cases: Sequence[tuple]) -> list[tuple]:
    if os.getenv("TEST_AI_SCOPE", "sample").strip().lower() == "full":
        return list(cases)
    return [case for case in cases if case[3]][:1]
