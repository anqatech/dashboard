import math

import pandas as pd

from dashboard_core.formatters import (
    format_log_return_as_percent,
    format_market_cap_billions,
    format_percent,
    format_score,
)


TIME_WINDOW_OPTIONS = {
    "3M": 63,
    "6M": 126,
    "1Y": 252,
    "3Y": 756,
    "5Y": 1260,
    "Max": None,
}


def filter_prices_by_window(prices: pd.DataFrame, selected_window: str) -> pd.DataFrame:
    window_size = TIME_WINDOW_OPTIONS[selected_window]
    if window_size is None:
        return prices.copy()
    return prices.tail(window_size).reset_index(drop=True)


def weighted_average(
    group: pd.DataFrame,
    column: str,
    weight_column: str = "market_cap",
) -> float:
    valid = group.loc[group[column].notna() & group[weight_column].notna() & (group[weight_column] > 0)].copy()
    if valid.empty:
        return float("nan")

    weights = valid[weight_column]
    return float((valid[column] * weights).sum() / weights.sum())


def weighted_simple_return(
    group: pd.DataFrame,
    column: str,
    weight_column: str = "market_cap",
) -> float:
    valid = group.loc[group[column].notna() & group[weight_column].notna() & (group[weight_column] > 0)].copy()
    if valid.empty:
        return float("nan")

    weights = valid[weight_column]
    simple_returns = valid[column].apply(lambda value: math.exp(float(value)) - 1.0)
    return float((simple_returns * weights).sum() / weights.sum())


def build_sector_summary(universe_with_status: pd.DataFrame) -> pd.DataFrame:
    sp500_total_market_cap = universe_with_status["market_cap"].sum()
    sector_summary = (
        universe_with_status.groupby("gics_sector", dropna=False)
        .agg(
            ticker_count=("ticker", "count"),
            sub_industry_count=("gics_sub_industry", "nunique"),
            total_market_cap=("market_cap", "sum"),
        )
        .reset_index()
    )
    sector_summary["total_market_cap_display"] = sector_summary["total_market_cap"].apply(format_market_cap_billions)
    sector_summary["market_cap_weight"] = (
        sector_summary["total_market_cap"] / sp500_total_market_cap if sp500_total_market_cap else 0.0
    )
    sector_summary["market_cap_weight_display"] = sector_summary["market_cap_weight"].apply(format_percent)
    return sector_summary.sort_values(
        ["market_cap_weight", "gics_sector"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_sub_industry_summary(sector_universe: pd.DataFrame) -> pd.DataFrame:
    return (
        sector_universe.groupby("gics_sub_industry", dropna=False)
        .agg(ticker_count=("ticker", "count"))
        .reset_index()
        .sort_values(["ticker_count", "gics_sub_industry"], ascending=[False, True])
        .reset_index(drop=True)
    )


def build_universe_stock_table(sector_universe: pd.DataFrame, status_frame: pd.DataFrame) -> pd.DataFrame:
    filtered_stocks = sector_universe.merge(status_frame, on="ticker", how="left")
    filtered_stocks["market_cap_display"] = filtered_stocks["market_cap"].apply(format_market_cap_billions)
    return filtered_stocks.sort_values(
        ["market_cap", "ticker", "company_name"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)


def build_stock_screener_table(
    filtered_universe: pd.DataFrame,
    status_frame: pd.DataFrame,
    performance_frame: pd.DataFrame,
) -> pd.DataFrame:
    filtered_stocks = filtered_universe.merge(status_frame, on="ticker", how="left")
    filtered_stocks = filtered_stocks.merge(performance_frame, on="ticker", how="left")
    filtered_stocks["market_cap_display"] = filtered_stocks["market_cap"].apply(format_market_cap_billions)
    filtered_stocks["latest_price_display"] = filtered_stocks["latest_close"]
    filtered_stocks["1D"] = filtered_stocks["log_return_1d"].apply(format_log_return_as_percent)
    filtered_stocks["1W"] = filtered_stocks["log_return_1w"].apply(format_log_return_as_percent)
    filtered_stocks["1M"] = filtered_stocks["log_return_1m"].apply(format_log_return_as_percent)
    filtered_stocks["YTD"] = filtered_stocks["log_return_ytd"].apply(format_log_return_as_percent)
    filtered_stocks["1Y"] = filtered_stocks["log_return_1y"].apply(format_log_return_as_percent)
    filtered_stocks["3Y"] = filtered_stocks["log_return_3y"].apply(format_log_return_as_percent)
    return filtered_stocks.sort_values(
        ["market_cap", "ticker", "company_name"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)


def build_stock_volatility_table(
    filtered_universe: pd.DataFrame,
    status_frame: pd.DataFrame,
    volatility_frame: pd.DataFrame,
) -> pd.DataFrame:
    filtered_stocks = filtered_universe.merge(status_frame, on="ticker", how="left")
    filtered_stocks = filtered_stocks.merge(volatility_frame, on="ticker", how="left")
    filtered_stocks["market_cap_display"] = filtered_stocks["market_cap"].apply(format_market_cap_billions)
    filtered_stocks["vol_1m_display"] = filtered_stocks["realized_vol_1m"].apply(format_percent)
    filtered_stocks["vol_3m_display"] = filtered_stocks["realized_vol_3m"].apply(format_percent)
    filtered_stocks["vol_6m_display"] = filtered_stocks["realized_vol_6m"].apply(format_percent)
    filtered_stocks["vol_1y_display"] = filtered_stocks["realized_vol_1y"].apply(format_percent)
    return filtered_stocks.sort_values(
        ["market_cap", "ticker", "company_name"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)


def build_trend_signals_table(
    filtered_universe: pd.DataFrame,
    trend_frame: pd.DataFrame,
) -> pd.DataFrame:
    filtered_stocks = filtered_universe.merge(trend_frame, on="ticker", how="left")
    filtered_stocks["market_cap_display"] = filtered_stocks["market_cap"].apply(format_market_cap_billions)
    filtered_stocks["trend_signal_display"] = filtered_stocks["trend_signal"].apply(format_score)
    filtered_stocks["trend_raw_display"] = filtered_stocks["trend_raw"].apply(format_score)
    filtered_stocks["ma_confirm_display"] = filtered_stocks["ma_confirm"].apply(format_percent)
    filtered_stocks["tsmom_63_display"] = filtered_stocks["tsmom_63"].apply(format_percent)
    filtered_stocks["tsmom_126_display"] = filtered_stocks["tsmom_126"].apply(format_percent)
    filtered_stocks["tsmom_252_display"] = filtered_stocks["tsmom_252"].apply(format_percent)
    filtered_stocks["relmom_12_1_display"] = filtered_stocks["relmom_12_1"].apply(format_percent)
    return filtered_stocks.sort_values(
        ["market_cap", "ticker", "company_name"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)


def build_sector_performance_table(frame: pd.DataFrame) -> pd.DataFrame:
    sector_summary = (
        frame.groupby("gics_sector", dropna=False)
        .agg(
            stock_count=("ticker", "count"),
            total_market_cap=("market_cap", "sum"),
        )
        .reset_index()
    )

    for column, output_name in [
        ("log_return_1d", "return_1d"),
        ("log_return_1w", "return_1w"),
        ("log_return_1m", "return_1m"),
        ("log_return_ytd", "return_ytd"),
        ("log_return_1y", "return_1y"),
        ("log_return_3y", "return_3y"),
    ]:
        weighted_returns = (
            frame.groupby("gics_sector", dropna=False)
            .apply(
                lambda group, source_column=column: weighted_simple_return(group, source_column),
                include_groups=False,
            )
            .rename(output_name)
            .reset_index()
        )
        sector_summary = sector_summary.merge(weighted_returns, on="gics_sector", how="left")

    sp500_total_market_cap = sector_summary["total_market_cap"].sum()
    sector_summary["weight"] = (
        sector_summary["total_market_cap"] / sp500_total_market_cap if sp500_total_market_cap else 0.0
    )
    sector_summary["total_market_cap_display"] = sector_summary["total_market_cap"].apply(format_market_cap_billions)
    sector_summary["weight_display"] = sector_summary["weight"].apply(format_percent)
    sector_summary["1D"] = sector_summary["return_1d"].apply(format_percent)
    sector_summary["1W"] = sector_summary["return_1w"].apply(format_percent)
    sector_summary["1M"] = sector_summary["return_1m"].apply(format_percent)
    sector_summary["YTD"] = sector_summary["return_ytd"].apply(format_percent)
    sector_summary["1Y"] = sector_summary["return_1y"].apply(format_percent)
    sector_summary["3Y"] = sector_summary["return_3y"].apply(format_percent)

    return sector_summary.sort_values(
        ["total_market_cap", "gics_sector"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_sector_volatility_table(frame: pd.DataFrame) -> pd.DataFrame:
    sector_summary = (
        frame.groupby("gics_sector", dropna=False)
        .agg(
            stock_count=("ticker", "count"),
            total_market_cap=("market_cap", "sum"),
        )
        .reset_index()
    )

    for column, output_name in [
        ("realized_vol_1m", "vol_1m"),
        ("realized_vol_3m", "vol_3m"),
        ("realized_vol_6m", "vol_6m"),
        ("realized_vol_1y", "vol_1y"),
    ]:
        weighted_values = (
            frame.groupby("gics_sector", dropna=False)
            .apply(
                lambda group, source_column=column: weighted_average(group, source_column),
                include_groups=False,
            )
            .rename(output_name)
            .reset_index()
        )
        sector_summary = sector_summary.merge(weighted_values, on="gics_sector", how="left")

    sp500_total_market_cap = sector_summary["total_market_cap"].sum()
    sector_summary["weight"] = (
        sector_summary["total_market_cap"] / sp500_total_market_cap if sp500_total_market_cap else 0.0
    )
    sector_summary["total_market_cap_display"] = sector_summary["total_market_cap"].apply(format_market_cap_billions)
    sector_summary["weight_display"] = sector_summary["weight"].apply(format_percent)
    sector_summary["vol_1m_display"] = sector_summary["vol_1m"].apply(format_percent)
    sector_summary["vol_3m_display"] = sector_summary["vol_3m"].apply(format_percent)
    sector_summary["vol_6m_display"] = sector_summary["vol_6m"].apply(format_percent)
    sector_summary["vol_1y_display"] = sector_summary["vol_1y"].apply(format_percent)

    return sector_summary.sort_values(
        ["total_market_cap", "gics_sector"],
        ascending=[False, True],
    ).reset_index(drop=True)


def build_sector_sharpe_table(
    performance_frame: pd.DataFrame,
    volatility_frame: pd.DataFrame,
    returns_3m_frame: pd.DataFrame,
) -> pd.DataFrame:
    combined = performance_frame.merge(
        volatility_frame.loc[:, ["ticker", "realized_vol_3m", "realized_vol_1y"]],
        on="ticker",
        how="left",
    )
    combined = combined.merge(returns_3m_frame, on="ticker", how="left")

    sector_summary = (
        combined.groupby("gics_sector", dropna=False)
        .agg(
            stock_count=("ticker", "count"),
            total_market_cap=("market_cap", "sum"),
        )
        .reset_index()
    )

    weighted_aggregations = [
        ("log_return_3m", "performance_3m", weighted_simple_return),
        ("log_return_1y", "performance_1y", weighted_simple_return),
        ("realized_vol_3m", "vol_3m", weighted_average),
        ("realized_vol_1y", "vol_1y", weighted_average),
    ]
    for source_column, output_name, aggregator in weighted_aggregations:
        weighted_values = (
            combined.groupby("gics_sector", dropna=False)
            .apply(
                lambda group, col=source_column, fn=aggregator: fn(group, col),
                include_groups=False,
            )
            .rename(output_name)
            .reset_index()
        )
        sector_summary = sector_summary.merge(weighted_values, on="gics_sector", how="left")

    sector_summary["sharpe_3m"] = (sector_summary["performance_3m"] / sector_summary["vol_3m"]) * math.sqrt(4)
    sector_summary["sharpe_1y"] = sector_summary["performance_1y"] / sector_summary["vol_1y"]

    sp500_total_market_cap = sector_summary["total_market_cap"].sum()
    sector_summary["weight"] = (
        sector_summary["total_market_cap"] / sp500_total_market_cap if sp500_total_market_cap else 0.0
    )
    sector_summary["total_market_cap_display"] = sector_summary["total_market_cap"].apply(format_market_cap_billions)
    sector_summary["weight_display"] = sector_summary["weight"].apply(format_percent)
    sector_summary["performance_3m_display"] = sector_summary["performance_3m"].apply(format_percent)
    sector_summary["performance_1y_display"] = sector_summary["performance_1y"].apply(format_percent)
    sector_summary["vol_3m_display"] = sector_summary["vol_3m"].apply(format_percent)
    sector_summary["sharpe_3m_display"] = sector_summary["sharpe_3m"].apply(format_score)
    sector_summary["sharpe_1y_display"] = sector_summary["sharpe_1y"].apply(format_score)

    return sector_summary.sort_values(
        ["sharpe_1y", "total_market_cap", "gics_sector"],
        ascending=[False, False, True],
        na_position="last",
    ).reset_index(drop=True)
