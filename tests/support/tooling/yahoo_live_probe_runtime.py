"""Runtime helpers for Yahoo live smoke probes."""

import os

import pytest

from tests.support.tooling.yahoo_probe import resolve_probe_symbols


def require_yahoo_live_enabled() -> None:
    if os.getenv("TEST_YAHOO_LIVE", "0") != "1":
        pytest.skip("TEST_YAHOO_LIVE != 1")


def load_yfinance():
    try:
        import yfinance as yf
    except Exception as exc:  # pragma: no cover - dependency/runtime check
        pytest.skip(f"yfinance unavailable: {exc}")
    return yf


def probe_symbols():
    return resolve_probe_symbols(os.getenv("TEST_YAHOO_SYMBOLS"))
