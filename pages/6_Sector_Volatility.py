from pathlib import Path

import pandas as pd
import streamlit as st


VOLATILITY_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-realized-volatility.parquet")
REQUIRED_COLUMNS = {
    "ticker",
    "gics_sector",
    "market_cap",
    "realized_vol_1m",
    "realized_vol_3m",
    "realized_vol_6m",
    "realized_vol_1y",
}


@st.cache_data
def load_volatility_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Volatility parquet is missing required columns: {missing_list}")

    selected_columns = [
        "ticker",
        "gics_sector",
        "market_cap",
        "realized_vol_1m",
        "realized_vol_3m",
        "realized_vol_6m",
        "realized_vol_1y",
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


def weighted_average(group: pd.DataFrame, column: str) -> float:
    valid = group.loc[group[column].notna() & group["market_cap"].notna() & (group["market_cap"] > 0)].copy()
    if valid.empty:
        return float("nan")

    weights = valid["market_cap"]
    return float((valid[column] * weights).sum() / weights.sum())


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


st.set_page_config(page_title="Sector Volatility", layout="wide")

st.title("Sector Volatility")
st.caption("Market-cap-weighted realized volatility by sector based on the local stock volatility frame.")

try:
    volatility_frame = load_volatility_data(str(VOLATILITY_FRAME_PATH))
except FileNotFoundError:
    st.error(f"Could not find the volatility parquet file at `{VOLATILITY_FRAME_PATH}`.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load the volatility parquet file: {exc}")
    st.stop()

sector_volatility = build_sector_volatility_table(volatility_frame)

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Sectors", f"{sector_volatility['gics_sector'].nunique():,}")
metric_col_2.metric("Stocks", f"{len(volatility_frame):,}")
metric_col_3.metric("Total market cap", format_market_cap_billions(sector_volatility["total_market_cap"].sum()))

st.dataframe(
    sector_volatility[
        [
            "gics_sector",
            "stock_count",
            "total_market_cap_display",
            "weight_display",
            "vol_1m_display",
            "vol_3m_display",
            "vol_6m_display",
            "vol_1y_display",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "gics_sector": "GICS sector",
        "stock_count": st.column_config.NumberColumn("Stocks", format="%d"),
        "total_market_cap_display": "Total market cap",
        "weight_display": "Weight",
        "vol_1m_display": "vol_1m",
        "vol_3m_display": "vol_3m",
        "vol_6m_display": "vol_6m",
        "vol_1y_display": "vol_1y",
    },
)
