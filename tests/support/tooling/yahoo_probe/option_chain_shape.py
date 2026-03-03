"""Options-chain shape-capture helpers for Yahoo live probes."""

from typing import Any, Dict, List, Sequence

from tests.support.tooling.yahoo_probe.scalar_normalization import coerce_number_or_text


OPTION_SAMPLE_KEYS: Sequence[str] = (
    "contractSymbol",
    "strike",
    "bid",
    "ask",
    "lastPrice",
    "volume",
    "openInterest",
    "impliedVolatility",
    "inTheMoney",
)


def capture_option_chain_shape(calls_table: Any, puts_table: Any) -> Dict[str, Any]:
    return {
        "calls": _capture_option_table_shape(calls_table),
        "puts": _capture_option_table_shape(puts_table),
    }


def _capture_option_table_shape(table: Any) -> Dict[str, Any]:
    columns = _table_columns(table)
    row_count = _table_row_count(table)
    sample_row = _table_sample_row(table)
    sample = {key: coerce_number_or_text(sample_row.get(key)) for key in OPTION_SAMPLE_KEYS} if sample_row else {}

    return {
        "row_count": row_count,
        "columns": columns,
        "sample": sample,
    }


def _table_columns(table: Any) -> List[str]:
    columns = getattr(table, "columns", None)
    if columns is None:
        return []
    try:
        return [str(value) for value in list(columns)]
    except Exception:
        return []


def _table_row_count(table: Any) -> int:
    length = getattr(table, "__len__", None)
    if callable(length):
        try:
            return int(length())
        except Exception:
            return 0
    return 0


def _table_sample_row(table: Any) -> Dict[str, Any]:
    try:
        if _table_row_count(table) < 1:
            return {}
        sample_row = table.iloc[0]
    except Exception:
        return {}

    to_dict = getattr(sample_row, "to_dict", None)
    if callable(to_dict):
        try:
            payload = to_dict()
        except Exception:
            return {}
        if isinstance(payload, dict):
            return payload
    return {}
