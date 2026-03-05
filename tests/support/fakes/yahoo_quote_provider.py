from types import SimpleNamespace
from typing import Any, Optional


def build_fake_yahoo_ticker(
    fast_info: Optional[dict[str, Any]] = None,
    info: Optional[dict[str, Any]] = None,
):
    return SimpleNamespace(
        fast_info=fast_info if fast_info is not None else {},
        info=info if info is not None else {},
    )
