import math

import pandas as pd
import pytest

from dashboard_core.data import (
    build_universe_lookup,
    filter_universe,
    load_daily_bars,
    load_performance_data,
    load_status_data,
    load_three_month_returns,
    load_trend_data,
    load_universe_data,
    load_volatility_data,
)


def test_load_universe_data_normalizes_and_sorts(tmp_path) -> None:
    csv_path = tmp_path / "universe.csv"
    pd.DataFrame(
        {
            "ticker": [" bbb ", None, "AAA"],
            "company_name": [" Beta ", "Gamma", " Alpha "],
            "gics_sector": ["Tech", None, "Health"],
            "gics_sub_industry": ["Software", None, "Biotech"],
        }
    ).to_csv(csv_path, index=False)

    result = load_universe_data(csv_path)

    assert result["ticker"].tolist() == ["AAA", "bbb", ""]
    assert result["gics_sector"].tolist() == ["Health", "Tech", "Unknown"]


def test_load_universe_data_raises_for_missing_columns(tmp_path) -> None:
    csv_path = tmp_path / "bad_universe.csv"
    pd.DataFrame({"ticker": ["AAA"]}).to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="Universe CSV is missing required columns"):
        load_universe_data(csv_path)


def test_load_status_data_normalizes_dates_and_deduplicates(tmp_path) -> None:
    parquet_path = tmp_path / "status.parquet"
    pd.DataFrame(
        {
            "ticker": [" AAA ", "AAA", "BBB"],
            "market_cap": [1.0, 2.0, 3.0],
            "start": ["2024-01-01", "2024-02-01", "2024-03-01"],
            "end": ["2025-01-01", "2025-02-01", "2025-03-01"],
        }
    ).to_parquet(parquet_path, index=False)

    result = load_status_data(parquet_path, columns=["market_cap", "start", "end"])

    assert result["ticker"].tolist() == ["AAA", "BBB"]
    assert str(result.loc[0, "start"].date()) == "2024-01-01"


def test_load_performance_and_volatility_data_normalize_sector_and_deduplicate(tmp_path) -> None:
    perf_path = tmp_path / "performance.parquet"
    vol_path = tmp_path / "vol.parquet"
    pd.DataFrame(
        {
            "ticker": [" AAA ", "AAA", "BBB"],
            "gics_sector": [None, "Tech", "Health"],
            "latest_close": [1.0, 2.0, 3.0],
        }
    ).to_parquet(perf_path, index=False)
    pd.DataFrame(
        {
            "ticker": [" AAA ", "AAA", "BBB"],
            "gics_sector": [None, "Tech", "Health"],
            "realized_vol_1m": [0.1, 0.2, 0.3],
        }
    ).to_parquet(vol_path, index=False)

    perf = load_performance_data(perf_path, columns=["gics_sector", "latest_close"])
    vol = load_volatility_data(vol_path, columns=["gics_sector", "realized_vol_1m"])

    assert perf["ticker"].tolist() == ["AAA", "BBB"]
    assert perf.loc[0, "gics_sector"] == "Unknown"
    assert vol.loc[0, "gics_sector"] == "Unknown"


def test_load_trend_data_deduplicates_by_ticker(tmp_path) -> None:
    parquet_path = tmp_path / "trend.parquet"
    pd.DataFrame(
        {
            "ticker": [" AAA ", "AAA", "BBB"],
            "trend_signal": [1.0, 2.0, 3.0],
        }
    ).to_parquet(parquet_path, index=False)

    result = load_trend_data(parquet_path, columns=["trend_signal"])

    assert result["ticker"].tolist() == ["AAA", "BBB"]
    assert result.loc[0, "trend_signal"] == 1.0


def test_load_daily_bars_sorts_by_date(tmp_path) -> None:
    parquet_path = tmp_path / "AAA.parquet"
    pd.DataFrame(
        {
            "date": ["2024-01-03", "2024-01-01", "2024-01-02"],
            "open": [1.0, 1.0, 1.0],
            "high": [1.0, 1.0, 1.0],
            "low": [1.0, 1.0, 1.0],
            "close": [1.0, 1.0, 1.0],
            "volume": [1, 1, 1],
        }
    ).to_parquet(parquet_path, index=False)

    result = load_daily_bars("AAA", tmp_path)

    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == ["2024-01-01", "2024-01-02", "2024-01-03"]


def test_load_three_month_returns_builds_expected_log_return(tmp_path) -> None:
    dates = pd.date_range("2024-01-01", periods=70, freq="D")
    pd.DataFrame(
        {
            "ticker": ["AAA"] * len(dates),
            "date": dates,
            "close": [100.0] * 7 + [110.0] * (len(dates) - 7),
        }
    ).to_parquet(tmp_path / "AAA.parquet", index=False)

    result = load_three_month_returns(tmp_path)

    assert result["ticker"].tolist() == ["AAA"]
    assert result.loc[0, "log_return_3m"] == pytest.approx(math.log(110.0 / 100.0))


def test_build_universe_lookup_and_filter_universe() -> None:
    universe = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB", "CCC"],
            "company_name": ["Alpha", "Beta", "Gamma"],
            "gics_sector": ["Tech", "Tech", "Health"],
            "gics_sub_industry": ["Software", "Hardware", "Biotech"],
        }
    )

    lookup = build_universe_lookup(universe)
    filtered_sector = filter_universe(universe, "Tech")
    filtered_sub_industry = filter_universe(universe, "Tech", "Hardware")

    assert lookup["AAA"]["company_name"] == "Alpha"
    assert filtered_sector["ticker"].tolist() == ["AAA", "BBB"]
    assert filtered_sub_industry["ticker"].tolist() == ["BBB"]
