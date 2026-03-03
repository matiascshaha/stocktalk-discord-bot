"""Symbol resolution for Yahoo live probes."""

from typing import List, Optional, Sequence


DEFAULT_PROBE_SYMBOLS: Sequence[str] = ("AAPL", "TSLA")


def resolve_probe_symbols(env_value: Optional[str]) -> List[str]:
    if not env_value:
        return list(DEFAULT_PROBE_SYMBOLS)

    resolved: List[str] = []
    for raw_value in str(env_value).split(","):
        symbol = raw_value.strip().upper().replace("$", "")
        if symbol:
            resolved.append(symbol)
    return resolved or list(DEFAULT_PROBE_SYMBOLS)
