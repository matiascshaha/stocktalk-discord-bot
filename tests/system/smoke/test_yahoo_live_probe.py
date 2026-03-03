from pathlib import Path

import pytest

from src.market_data.yahoo.contracts import YahooOptionChainShape, YahooQuoteShape
from tests.support.artifacts import append_smoke_check
from tests.support.tooling.yahoo_live_probe_runtime import (
    load_yfinance,
    probe_symbols,
    require_yahoo_live_enabled,
)
from tests.support.tooling.yahoo_probe import (
    capture_option_chain_shape,
    capture_quote_shape,
    extract_price_presence,
)


pytestmark = [pytest.mark.e2e, pytest.mark.smoke, pytest.mark.live, pytest.mark.system]

REPORT_PATH = Path("artifacts/yahoo_live_probe_report.json")


def test_yahoo_live_quote_probe():
    require_yahoo_live_enabled()
    yf = load_yfinance()

    symbols = probe_symbols()
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            fast_info = dict(getattr(ticker, "fast_info", {}) or {})
            info = dict(getattr(ticker, "info", {}) or {})
            shape = capture_quote_shape(fast_info, info)
            _ = YahooQuoteShape.model_validate(shape)
            has_price = extract_price_presence(shape)

            details = {
                "symbol": symbol,
                "has_usable_price": has_price,
                "quote_shape": shape,
            }
            append_smoke_check(
                REPORT_PATH,
                f"yahoo_quote_probe_{symbol}",
                "passed" if has_price else "failed",
                details,
            )
            assert has_price is True, f"No usable price fields found for {symbol}"
        except Exception as exc:
            append_smoke_check(
                REPORT_PATH,
                f"yahoo_quote_probe_{symbol}",
                "failed",
                {"symbol": symbol, "error": str(exc)},
            )
            raise


def test_yahoo_live_options_chain_probe():
    require_yahoo_live_enabled()
    yf = load_yfinance()

    symbols = probe_symbols()
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            expirations = tuple(getattr(ticker, "options", ()) or ())
            if not expirations:
                append_smoke_check(
                    REPORT_PATH,
                    f"yahoo_options_probe_{symbol}",
                    "xfailed",
                    {
                        "symbol": symbol,
                        "reason": "No option expirations returned by Yahoo for symbol",
                    },
                )
                continue

            selected_expiration = expirations[0]
            chain = ticker.option_chain(selected_expiration)
            shape = capture_option_chain_shape(chain.calls, chain.puts)
            _ = YahooOptionChainShape.model_validate(shape)

            calls_count = int(shape.get("calls", {}).get("row_count", 0))
            puts_count = int(shape.get("puts", {}).get("row_count", 0))
            has_contract_rows = calls_count > 0 or puts_count > 0

            details = {
                "symbol": symbol,
                "expiration_count": len(expirations),
                "selected_expiration": selected_expiration,
                "has_contract_rows": has_contract_rows,
                "option_chain_shape": shape,
            }
            append_smoke_check(
                REPORT_PATH,
                f"yahoo_options_probe_{symbol}",
                "passed" if has_contract_rows else "xfailed",
                details,
            )
            if not has_contract_rows:
                pytest.xfail(f"Yahoo option chain returned zero rows for {symbol} ({selected_expiration})")
        except Exception as exc:
            append_smoke_check(
                REPORT_PATH,
                f"yahoo_options_probe_{symbol}",
                "failed",
                {"symbol": symbol, "error": str(exc)},
            )
            raise
