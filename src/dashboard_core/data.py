from pathlib import Path
import math
from typing import Iterable

import pandas as pd

from dashboard_core.paths import (
    DAILY_BARS_DIR,
    PERFORMANCE_FRAME_PATH,
    STATUS_FRAME_PATH,
    TREND_FRAME_PATH,
    UNIVERSE_PATH,
    VOLATILITY_FRAME_PATH,
)


UNIVERSE_REQUIRED_COLUMNS = {
    "ticker",
    "company_name",
    "gics_sector",
    "gics_sub_industry",
}


def _missing_columns(frame: pd.DataFrame, required_columns: Iterable[str]) -> set[str]:
    return set(required_columns).difference(frame.columns)


def _raise_for_missing_columns(
    frame: pd.DataFrame,
    required_columns: Iterable[str],
    dataset_name: str,
) -> None:
    missing_columns = _missing_columns(frame, required_columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"{dataset_name} is missing required columns: {missing_list}")


def _normalize_universe_columns(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    cleaned["company_name"] = cleaned["company_name"].fillna("").astype(str).str.strip()
    cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    cleaned["gics_sub_industry"] = cleaned["gics_sub_industry"].fillna("Unknown").astype(str).str.strip()
    return cleaned.sort_values(["gics_sector", "gics_sub_industry", "ticker"]).reset_index(drop=True)


def _normalize_ticker_column(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    return cleaned


def load_universe_data(csv_path: Path | str = UNIVERSE_PATH) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    _raise_for_missing_columns(frame, UNIVERSE_REQUIRED_COLUMNS, "Universe CSV")
    return _normalize_universe_columns(frame)


def load_status_data(
    parquet_path: Path | str = STATUS_FRAME_PATH,
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    selected_columns = ["ticker", *(columns or ["market_cap", "start", "end"])]
    frame = pd.read_parquet(parquet_path)
    _raise_for_missing_columns(frame, selected_columns, "Status parquet")

    cleaned = _normalize_ticker_column(frame.loc[:, selected_columns].copy())
    if "start" in cleaned.columns:
        cleaned["start"] = pd.to_datetime(cleaned["start"], errors="coerce")
    if "end" in cleaned.columns:
        cleaned["end"] = pd.to_datetime(cleaned["end"], errors="coerce")
    return cleaned.drop_duplicates(subset=["ticker"])


def load_performance_data(
    parquet_path: Path | str = PERFORMANCE_FRAME_PATH,
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    selected_columns = ["ticker", *(columns or [])]
    frame = pd.read_parquet(parquet_path)
    _raise_for_missing_columns(frame, selected_columns, "Performance parquet")

    cleaned = _normalize_ticker_column(frame.loc[:, selected_columns].copy())
    if "gics_sector" in cleaned.columns:
        cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


def load_volatility_data(
    parquet_path: Path | str = VOLATILITY_FRAME_PATH,
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    selected_columns = ["ticker", *(columns or [])]
    frame = pd.read_parquet(parquet_path)
    _raise_for_missing_columns(frame, selected_columns, "Volatility parquet")

    cleaned = _normalize_ticker_column(frame.loc[:, selected_columns].copy())
    if "gics_sector" in cleaned.columns:
        cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


def load_trend_data(
    parquet_path: Path | str = TREND_FRAME_PATH,
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    selected_columns = ["ticker", *(columns or [])]
    frame = pd.read_parquet(parquet_path)
    _raise_for_missing_columns(frame, selected_columns, "Trend parquet")

    cleaned = _normalize_ticker_column(frame.loc[:, selected_columns].copy())
    return cleaned.drop_duplicates(subset=["ticker"])


def load_daily_bars(
    ticker: str,
    daily_bars_dir: Path | str = DAILY_BARS_DIR,
) -> pd.DataFrame:
    parquet_path = Path(daily_bars_dir) / f"{ticker}.parquet"
    frame = pd.read_parquet(parquet_path)
    expected_columns = {"date", "open", "high", "low", "close", "volume"}
    _raise_for_missing_columns(frame, expected_columns, f"Daily bars file for {ticker}")

    cleaned = frame.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    return cleaned.sort_values("date").reset_index(drop=True)


def load_three_month_returns(daily_bars_dir: Path | str = DAILY_BARS_DIR) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for parquet_path in sorted(Path(daily_bars_dir).glob("*.parquet")):
        frame = pd.read_parquet(parquet_path, columns=["ticker", "date", "close"])
        if frame.empty or len(frame) < 64:
            continue

        cleaned = frame.copy()
        cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
        cleaned = cleaned.sort_values("date").reset_index(drop=True)
        latest_close = float(cleaned["close"].iloc[-1])
        reference_close = float(cleaned["close"].iloc[-64])
        if latest_close <= 0 or reference_close <= 0:
            continue

        rows.append(
            {
                "ticker": str(cleaned["ticker"].iloc[-1]).strip(),
                "log_return_3m": math.log(latest_close / reference_close),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["ticker", "log_return_3m"])

    return pd.DataFrame(rows).drop_duplicates(subset=["ticker"])


def build_universe_lookup(universe: pd.DataFrame) -> dict[str, dict[str, str]]:
    return (
        universe.loc[:, ["ticker", "company_name", "gics_sector", "gics_sub_industry"]]
        .drop_duplicates(subset=["ticker"])
        .set_index("ticker")
        .to_dict(orient="index")
    )


def filter_universe(
    universe: pd.DataFrame,
    sector: str,
    sub_industry: str | None = None,
) -> pd.DataFrame:
    filtered = universe.loc[universe["gics_sector"] == sector].copy()
    if sub_industry is not None and sub_industry != "All":
        filtered = filtered.loc[filtered["gics_sub_industry"] == sub_industry].copy()
    return filtered.reset_index(drop=True)
