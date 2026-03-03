"""Scalar normalization helpers for Yahoo probe artifacts."""

from typing import Any, Optional


def to_float(value: Any) -> Optional[float]:
    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first_non_empty(*values: Any) -> Any:
    for value in values:
        if value in (None, "", "null"):
            continue
        return value
    return None


def coerce_number_or_text(value: Any) -> Any:
    numeric = to_float(value)
    if numeric is not None:
        return numeric
    if value in (None, "", "null"):
        return None
    text = str(value).strip()
    return text or None
