from pathlib import Path
import math

import pandas as pd
import streamlit as st


PERFORMANCE_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-performance-metrics.parquet")
REQUIRED_COLUMNS = {
    "ticker",
    "gics_sector",
    "market_cap",
    "log_return_1d",
    "log_return_1w",
    "log_return_1m",
    "log_return_ytd",
    "log_return_1y",
    "log_return_3y",
}


@st.cache_data
def load_performance_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Performance parquet is missing required columns: {missing_list}")

    selected_columns = [
        "ticker",
        "gics_sector",
        "market_cap",
        "log_return_1d",
        "log_return_1w",
        "log_return_1m",
        "log_return_ytd",
        "log_return_1y",
        "log_return_3y",
    ]
    cleaned = frame.loc[:, selected_columns].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


def format_market_cap_billions(value: float) -> str:
    if pd.isna(value):
        return ""
    billions = float(value) / 1_000_000_000
    return f"${billions:,.2f}b"


def format_percent(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value) * 100:,.1f}%"


def weighted_simple_return(group: pd.DataFrame, column: str) -> float:
    valid = group.loc[group[column].notna() & group["market_cap"].notna() & (group["market_cap"] > 0)].copy()
    if valid.empty:
        return float("nan")

    weights = valid["market_cap"]
    simple_returns = valid[column].apply(lambda value: math.exp(float(value)) - 1.0)
    return float((simple_returns * weights).sum() / weights.sum())


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


st.set_page_config(page_title="Sector Performance", layout="wide")

st.title("Sector Performance")
st.caption("Market-cap-weighted sector performance based on the local stock return frame.")

try:
    performance_frame = load_performance_data(str(PERFORMANCE_FRAME_PATH))
except FileNotFoundError:
    st.error(f"Could not find the performance parquet file at `{PERFORMANCE_FRAME_PATH}`.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load the performance parquet file: {exc}")
    st.stop()

sector_performance = build_sector_performance_table(performance_frame)

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Sectors", f"{sector_performance['gics_sector'].nunique():,}")
metric_col_2.metric("Stocks", f"{len(performance_frame):,}")
metric_col_3.metric("Total market cap", format_market_cap_billions(sector_performance["total_market_cap"].sum()))

st.dataframe(
    sector_performance[
        [
            "gics_sector",
            "stock_count",
            "total_market_cap_display",
            "weight_display",
            "1D",
            "1W",
            "1M",
            "YTD",
            "1Y",
            "3Y",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "gics_sector": "GICS sector",
        "stock_count": st.column_config.NumberColumn("Stocks", format="%d"),
        "total_market_cap_display": "Total market cap",
        "weight_display": "Weight",
        "1D": "1D",
        "1W": "1W",
        "1M": "1M",
        "YTD": "YTD",
        "1Y": "1Y",
        "3Y": "3Y",
    },
)
