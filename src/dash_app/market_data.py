from functools import lru_cache

import pandas as pd

from dashboard_core.analytics import (
    build_sector_performance_table,
    build_sector_sharpe_table,
    build_sector_volatility_table,
)
from dashboard_core.data import (
    filter_universe,
    load_performance_data,
    load_status_data,
    load_three_month_returns,
    load_trend_data,
    load_universe_data,
    load_volatility_data,
)
from dashboard_core.paths import (
    DAILY_BARS_DIR,
    PERFORMANCE_FRAME_PATH,
    STATUS_FRAME_PATH,
    TREND_FRAME_PATH,
    UNIVERSE_PATH,
    VOLATILITY_FRAME_PATH,
)


@lru_cache(maxsize=1)
def get_universe() -> pd.DataFrame:
    return load_universe_data(UNIVERSE_PATH)


@lru_cache(maxsize=1)
def get_status_frame() -> pd.DataFrame:
    return load_status_data(STATUS_FRAME_PATH, columns=["market_cap", "start", "end"])


@lru_cache(maxsize=1)
def get_performance_frame() -> pd.DataFrame:
    return load_performance_data(
        PERFORMANCE_FRAME_PATH,
        columns=[
            "latest_close",
            "log_return_1d",
            "log_return_1w",
            "log_return_1m",
            "log_return_ytd",
            "log_return_1y",
            "log_return_3y",
        ],
    )


@lru_cache(maxsize=1)
def get_volatility_frame() -> pd.DataFrame:
    return load_volatility_data(
        VOLATILITY_FRAME_PATH,
        columns=[
            "latest_close",
            "realized_vol_1m",
            "realized_vol_3m",
            "realized_vol_6m",
            "realized_vol_1y",
        ],
    )


@lru_cache(maxsize=1)
def get_trend_frame() -> pd.DataFrame:
    return load_trend_data(
        TREND_FRAME_PATH,
        columns=[
            "market_cap",
            "latest_close",
            "trend_signal",
            "trend_raw",
            "ma_confirm",
            "tsmom_63",
            "tsmom_126",
            "tsmom_252",
            "relmom_12_1",
        ],
    )


@lru_cache(maxsize=1)
def get_sector_performance_table() -> pd.DataFrame:
    performance_frame = load_performance_data(
        PERFORMANCE_FRAME_PATH,
        columns=[
            "gics_sector",
            "market_cap",
            "log_return_1d",
            "log_return_1w",
            "log_return_1m",
            "log_return_ytd",
            "log_return_1y",
            "log_return_3y",
        ],
    )
    return build_sector_performance_table(performance_frame)


@lru_cache(maxsize=1)
def get_sector_volatility_table() -> pd.DataFrame:
    volatility_frame = load_volatility_data(
        VOLATILITY_FRAME_PATH,
        columns=[
            "gics_sector",
            "market_cap",
            "realized_vol_1m",
            "realized_vol_3m",
            "realized_vol_6m",
            "realized_vol_1y",
        ],
    )
    return build_sector_volatility_table(volatility_frame)


@lru_cache(maxsize=1)
def get_sector_sharpe_table() -> pd.DataFrame:
    performance_frame = load_performance_data(
        PERFORMANCE_FRAME_PATH,
        columns=["gics_sector", "market_cap", "log_return_1y"],
    )
    volatility_frame = load_volatility_data(
        VOLATILITY_FRAME_PATH,
        columns=["gics_sector", "market_cap", "realized_vol_3m", "realized_vol_1y"],
    )
    returns_3m_frame = load_three_month_returns(DAILY_BARS_DIR)
    return build_sector_sharpe_table(performance_frame, volatility_frame, returns_3m_frame)


def build_select_options(values: list[str]) -> list[dict[str, str]]:
    return [{"label": value, "value": value} for value in values]


def get_initial_market_filters() -> tuple[str, str]:
    universe = get_universe()
    sector = sorted(universe["gics_sector"].unique().tolist())[0]
    sector_universe = filter_universe(universe, sector)
    sub_industry = sorted(sector_universe["gics_sub_industry"].unique().tolist())[0]
    return sector, sub_industry
