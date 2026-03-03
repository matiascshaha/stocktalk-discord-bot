"""Quote shape-capture helpers for Yahoo live probes."""

from typing import Any, Dict, Mapping, Sequence

from tests.support.tooling.yahoo_probe.scalar_normalization import (
    coerce_number_or_text,
    first_non_empty,
    to_float,
)


QUOTE_SAMPLE_KEYS: Sequence[str] = (
    "bid",
    "ask",
    "lastPrice",
    "regularMarketPrice",
    "currentPrice",
    "previousClose",
)


def capture_quote_shape(fast_info: Mapping[str, Any], info: Mapping[str, Any]) -> Dict[str, Any]:
    fast_info_keys = sorted(str(key) for key in fast_info.keys())
    info_keys = sorted(str(key) for key in info.keys())

    sample_values = {
        key: coerce_number_or_text(first_non_empty(fast_info.get(key), info.get(key)))
        for key in QUOTE_SAMPLE_KEYS
    }

    return {
        "fast_info_keys": fast_info_keys,
        "info_keys_count": len(info_keys),
        "info_keys_sample": info_keys[:25],
        "sample_values": sample_values,
        "price_fields_present": {
            key: key in fast_info or key in info
            for key in QUOTE_SAMPLE_KEYS
        },
    }


def extract_price_presence(shape: Mapping[str, Any]) -> bool:
    sample_values = shape.get("sample_values", {})
    if not isinstance(sample_values, Mapping):
        return False

    for key in ("lastPrice", "regularMarketPrice", "currentPrice", "bid", "ask", "previousClose"):
        value = sample_values.get(key)
        numeric = to_float(value)
        if numeric is not None and numeric > 0:
            return True
    return False
