from pathlib import Path
import math

import pandas as pd
import streamlit as st


PERFORMANCE_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-performance-metrics.parquet")
VOLATILITY_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-realized-volatility.parquet")
DAILY_BARS_DIR = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/daily-bars")
PERFORMANCE_REQUIRED_COLUMNS = {
    "ticker",
    "gics_sector",
    "market_cap",
    "log_return_1y",
}
VOLATILITY_REQUIRED_COLUMNS = {
    "ticker",
    "gics_sector",
    "market_cap",
    "realized_vol_3m",
    "realized_vol_1y",
}


@st.cache_data
def load_performance_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = PERFORMANCE_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Performance parquet is missing required columns: {missing_list}")

    selected_columns = ["ticker", "gics_sector", "market_cap", "log_return_1y"]
    cleaned = frame.loc[:, selected_columns].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


@st.cache_data
def load_volatility_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = VOLATILITY_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Volatility parquet is missing required columns: {missing_list}")

    selected_columns = ["ticker", "gics_sector", "market_cap", "realized_vol_3m", "realized_vol_1y"]
    cleaned = frame.loc[:, selected_columns].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


@st.cache_data
def load_three_month_returns(daily_bars_dir: str) -> pd.DataFrame:
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

    return pd.DataFrame(rows).drop_duplicates(subset=["ticker"])


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


def weighted_average(group: pd.DataFrame, column: str) -> float:
    valid = group.loc[group[column].notna() & group["market_cap"].notna() & (group["market_cap"] > 0)].copy()
    if valid.empty:
        return float("nan")

    weights = valid["market_cap"]
    return float((valid[column] * weights).sum() / weights.sum())


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
    sector_summary["sharpe_1y"] = (sector_summary["performance_1y"] / sector_summary["vol_1y"]) * math.sqrt(1)

    sp500_total_market_cap = sector_summary["total_market_cap"].sum()
    sector_summary["weight"] = (
        sector_summary["total_market_cap"] / sp500_total_market_cap if sp500_total_market_cap else 0.0
    )
    sector_summary["total_market_cap_display"] = sector_summary["total_market_cap"].apply(format_market_cap_billions)
    sector_summary["weight_display"] = sector_summary["weight"].apply(format_percent)
    sector_summary["performance_3m_display"] = sector_summary["performance_3m"].apply(format_percent)
    sector_summary["performance_1y_display"] = sector_summary["performance_1y"].apply(format_percent)
    sector_summary["vol_3m_display"] = sector_summary["vol_3m"].apply(format_percent)
    sector_summary["sharpe_3m_display"] = sector_summary["sharpe_3m"].apply(
        lambda value: "" if pd.isna(value) else f"{float(value):.2f}"
    )
    sector_summary["sharpe_1y_display"] = sector_summary["sharpe_1y"].apply(
        lambda value: "" if pd.isna(value) else f"{float(value):.2f}"
    )

    return sector_summary.sort_values(
        ["sharpe_1y", "total_market_cap", "gics_sector"],
        ascending=[False, False, True],
        na_position="last",
    ).reset_index(drop=True)


st.set_page_config(page_title="Sector Sharpe", layout="wide")

st.title("Sector Sharpe")
st.caption(
    "Risk-adjusted sector view using annualized Sharpe ratios, market-cap-weighted returns, realized volatility, and a 0% risk-free-rate assumption."
)

try:
    performance_frame = load_performance_data(str(PERFORMANCE_FRAME_PATH))
    volatility_frame = load_volatility_data(str(VOLATILITY_FRAME_PATH))
    returns_3m_frame = load_three_month_returns(str(DAILY_BARS_DIR))
except FileNotFoundError as exc:
    st.error(f"Missing input file: {exc.filename}")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load sector Sharpe inputs: {exc}")
    st.stop()

sector_sharpe = build_sector_sharpe_table(performance_frame, volatility_frame, returns_3m_frame)

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Sectors", f"{sector_sharpe['gics_sector'].nunique():,}")
metric_col_2.metric("Stocks", f"{len(performance_frame):,}")
metric_col_3.metric("Total market cap", format_market_cap_billions(sector_sharpe["total_market_cap"].sum()))

st.dataframe(
    sector_sharpe[
        [
            "gics_sector",
            "stock_count",
            "total_market_cap_display",
            "weight_display",
            "performance_3m_display",
            "performance_1y_display",
            "vol_3m_display",
            "sharpe_3m_display",
            "sharpe_1y_display",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "gics_sector": "GICS sector",
        "stock_count": st.column_config.NumberColumn("Stocks", format="%d"),
        "total_market_cap_display": "Total market cap",
        "weight_display": "Weight",
        "performance_3m_display": "3M",
        "performance_1y_display": "1Y",
        "vol_3m_display": "vol_3m",
        "sharpe_3m_display": "ann_sharpe_3m",
        "sharpe_1y_display": "ann_sharpe_1y",
    },
)
