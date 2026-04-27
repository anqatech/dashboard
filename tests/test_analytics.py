import math

import pandas as pd
import pytest

from dashboard_core.analytics import (
    build_sector_summary,
    build_stock_screener_table,
    build_stock_volatility_table,
    build_trend_signals_table,
    build_universe_stock_table,
    filter_prices_by_window,
    weighted_average,
    weighted_simple_return,
)


def test_filter_prices_by_window_returns_tail_for_finite_window() -> None:
    prices = pd.DataFrame({"close": range(100)})

    filtered = filter_prices_by_window(prices, "3M")

    assert len(filtered) == 63
    assert filtered["close"].tolist()[0] == 37
    assert filtered["close"].tolist()[-1] == 99


def test_weighted_average_ignores_missing_and_zero_weights() -> None:
    frame = pd.DataFrame(
        {
            "value": [0.1, 0.2, None, 0.9],
            "market_cap": [10.0, 30.0, 40.0, 0.0],
        }
    )

    result = weighted_average(frame, "value")

    assert result == pytest.approx((0.1 * 10 + 0.2 * 30) / 40)


def test_weighted_simple_return_uses_simple_returns() -> None:
    frame = pd.DataFrame(
        {
            "log_return": [math.log(1.10), math.log(0.90)],
            "market_cap": [2.0, 1.0],
        }
    )

    result = weighted_simple_return(frame, "log_return")

    expected = ((0.10 * 2.0) + (-0.10 * 1.0)) / 3.0
    assert result == pytest.approx(expected)


def test_build_sector_summary_sorts_by_market_cap_weight_desc() -> None:
    universe_with_status = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB", "CCC"],
            "gics_sector": ["Tech", "Tech", "Health"],
            "gics_sub_industry": ["Software", "Hardware", "Biotech"],
            "market_cap": [200.0, 100.0, 50.0],
        }
    )

    summary = build_sector_summary(universe_with_status)

    assert summary["gics_sector"].tolist() == ["Tech", "Health"]
    assert summary.loc[0, "ticker_count"] == 2
    assert summary.loc[0, "market_cap_weight_display"] == "85.7%"


def test_build_stock_screener_table_keeps_desc_market_cap_order_and_formats() -> None:
    filtered_universe = pd.DataFrame(
        {
            "ticker": ["BBB", "AAA"],
            "company_name": ["Beta", "Alpha"],
            "gics_sector": ["Tech", "Tech"],
            "gics_sub_industry": ["Software", "Software"],
        }
    )
    status_frame = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB"],
            "market_cap": [2_000_000_000, 5_000_000_000],
            "start": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "end": pd.to_datetime(["2025-01-01", "2025-01-01"]),
        }
    )
    performance_frame = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB"],
            "latest_close": [10.0, 20.0],
            "log_return_1d": [0.0, math.log(1.05)],
            "log_return_1w": [0.0, 0.0],
            "log_return_1m": [0.0, 0.0],
            "log_return_ytd": [0.0, 0.0],
            "log_return_1y": [0.0, 0.0],
            "log_return_3y": [0.0, 0.0],
        }
    )

    result = build_stock_screener_table(filtered_universe, status_frame, performance_frame)

    assert result["ticker"].tolist() == ["BBB", "AAA"]
    assert result.loc[0, "market_cap_display"] == "$5.00b"
    assert result.loc[0, "1D"] == "5.0%"


def test_build_universe_stock_table_keeps_desc_market_cap_order() -> None:
    sector_universe = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB"],
            "company_name": ["Alpha", "Beta"],
        }
    )
    status_frame = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB"],
            "market_cap": [1_000_000_000, 2_000_000_000],
            "start": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "end": pd.to_datetime(["2025-01-01", "2025-01-01"]),
        }
    )

    result = build_universe_stock_table(sector_universe, status_frame)

    assert result["ticker"].tolist() == ["BBB", "AAA"]
    assert result.loc[0, "market_cap_display"] == "$2.00b"


def test_build_stock_volatility_table_formats_vol_columns() -> None:
    filtered_universe = pd.DataFrame(
        {
            "ticker": ["AAA"],
            "company_name": ["Alpha"],
        }
    )
    status_frame = pd.DataFrame(
        {
            "ticker": ["AAA"],
            "market_cap": [2_000_000_000],
            "start": pd.to_datetime(["2024-01-01"]),
            "end": pd.to_datetime(["2025-01-01"]),
        }
    )
    volatility_frame = pd.DataFrame(
        {
            "ticker": ["AAA"],
            "realized_vol_1m": [0.10],
            "realized_vol_3m": [0.20],
            "realized_vol_6m": [0.30],
            "realized_vol_1y": [0.40],
        }
    )

    result = build_stock_volatility_table(filtered_universe, status_frame, volatility_frame)

    assert result.loc[0, "vol_1m_display"] == "10.0%"
    assert result.loc[0, "vol_1y_display"] == "40.0%"


def test_build_trend_signals_table_formats_signal_columns() -> None:
    filtered_universe = pd.DataFrame(
        {
            "ticker": ["AAA"],
            "company_name": ["Alpha"],
        }
    )
    trend_frame = pd.DataFrame(
        {
            "ticker": ["AAA"],
            "market_cap": [3_000_000_000],
            "trend_signal": [1.234],
            "trend_raw": [0.456],
            "ma_confirm": [0.75],
            "tsmom_63": [0.12],
            "tsmom_126": [0.23],
            "tsmom_252": [0.34],
            "relmom_12_1": [0.45],
        }
    )

    result = build_trend_signals_table(filtered_universe, trend_frame)

    assert result.loc[0, "market_cap_display"] == "$3.00b"
    assert result.loc[0, "trend_signal_display"] == "1.23"
    assert result.loc[0, "ma_confirm_display"] == "75.0%"
