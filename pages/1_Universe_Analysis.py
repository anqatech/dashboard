from pathlib import Path

import pandas as pd
import streamlit as st

from ui_state import render_persistent_selectbox


DEFAULT_UNIVERSE_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/sp500/tickers_enriched.csv")
STATUS_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-database-status-with-market-cap.parquet")
REQUIRED_COLUMNS = {
    "ticker",
    "company_name",
    "gics_sector",
    "gics_sub_industry",
}
STATUS_REQUIRED_COLUMNS = {"ticker", "market_cap", "start", "end"}


@st.cache_data
def load_universe_data(csv_path: str) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV is missing required columns: {missing_list}")

    cleaned = frame.copy()
    cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    cleaned["gics_sub_industry"] = cleaned["gics_sub_industry"].fillna("Unknown").astype(str).str.strip()
    cleaned["company_name"] = cleaned["company_name"].fillna("").astype(str).str.strip()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    return cleaned


@st.cache_data
def load_status_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = STATUS_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Status parquet is missing required columns: {missing_list}")

    cleaned = frame.loc[:, ["ticker", "market_cap", "start", "end"]].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    cleaned["start"] = pd.to_datetime(cleaned["start"], errors="coerce")
    cleaned["end"] = pd.to_datetime(cleaned["end"], errors="coerce")
    return cleaned.drop_duplicates(subset=["ticker"])


def format_market_cap_billions(value: float) -> str:
    if pd.isna(value):
        return ""
    billions = float(value) / 1_000_000_000
    return f"${billions:,.2f}b"


def format_market_cap_billions_whole(value: float) -> str:
    if pd.isna(value):
        return ""
    billions = float(value) / 1_000_000_000
    return f"${billions:,.0f}b"


def format_percent(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value) * 100:,.1f}%"


st.set_page_config(page_title="Universe Analysis", layout="wide")

st.title("Universe Analysis")
st.caption("Explore the enriched ticker universe by GICS sector, sub-industry, and stock list.")

try:
    universe = load_universe_data(str(DEFAULT_UNIVERSE_PATH))
except FileNotFoundError:
    st.error(f"Could not find the universe file at `{DEFAULT_UNIVERSE_PATH}`.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load the universe file: {exc}")
    st.stop()

try:
    status_frame = load_status_data(str(STATUS_FRAME_PATH))
except FileNotFoundError:
    st.error(f"Could not find the status parquet file at `{STATUS_FRAME_PATH}`.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load the status parquet file: {exc}")
    st.stop()

universe_with_status = universe.merge(status_frame, on="ticker", how="left")
sp500_total_market_cap = universe_with_status["market_cap"].sum()

metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
metric_col_1.metric("Tickers", f"{len(universe):,}")
metric_col_2.metric("GICS sectors", universe["gics_sector"].nunique())
metric_col_3.metric("Sub-industries", universe["gics_sub_industry"].nunique())
metric_col_4.metric("Total market cap", format_market_cap_billions_whole(sp500_total_market_cap))

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
    sector_summary["total_market_cap"] / sp500_total_market_cap
    if sp500_total_market_cap
    else 0.0
)
sector_summary["market_cap_weight_display"] = sector_summary["market_cap_weight"].apply(format_percent)
sector_summary = sector_summary.sort_values(
    ["market_cap_weight", "gics_sector"],
    ascending=[False, True],
).reset_index(drop=True)

st.subheader("Sector summary")
st.dataframe(
    sector_summary[
        [
            "gics_sector",
            "ticker_count",
            "sub_industry_count",
            "total_market_cap_display",
            "market_cap_weight_display",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "gics_sector": "GICS sector",
        "ticker_count": st.column_config.NumberColumn("Stocks", format="%d"),
        "sub_industry_count": st.column_config.NumberColumn("Sub-industries", format="%d"),
        "total_market_cap_display": "Total market cap",
        "market_cap_weight_display": "Ratio",
    },
)

available_sectors = sector_summary["gics_sector"].tolist()
selected_sector = render_persistent_selectbox(
    "Select a GICS sector",
    available_sectors,
    state_key="universe_sector",
    widget_key="_universe_sector",
)

sector_universe = universe.loc[universe["gics_sector"] == selected_sector].copy()
sub_industry_summary = (
    sector_universe.groupby("gics_sub_industry", dropna=False)
    .agg(
        ticker_count=("ticker", "count"),
    )
    .reset_index()
    .sort_values(["ticker_count", "gics_sub_industry"], ascending=[False, True])
)

st.subheader(f"Sub-industries in {selected_sector}")
st.dataframe(
    sub_industry_summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        "gics_sub_industry": "Sub-industry",
        "ticker_count": st.column_config.NumberColumn("Stocks", format="%d"),
    },
)

available_sub_industries = sub_industry_summary["gics_sub_industry"].tolist()
selected_sub_industry = render_persistent_selectbox(
    "Select a sub-industry",
    available_sub_industries,
    state_key="universe_sub_industry",
    widget_key="_universe_sub_industry",
)

filtered_stocks = (
    sector_universe.loc[sector_universe["gics_sub_industry"] == selected_sub_industry]
    .reset_index(drop=True)
)
filtered_stocks = filtered_stocks.merge(status_frame, on="ticker", how="left")
filtered_stocks["market_cap_display"] = filtered_stocks["market_cap"].apply(format_market_cap_billions)
filtered_stocks = filtered_stocks.sort_values(
    ["market_cap", "ticker", "company_name"],
    ascending=[False, True, True],
    na_position="last",
).reset_index(drop=True)

st.subheader(f"Stocks in {selected_sector} / {selected_sub_industry}")
st.dataframe(
    filtered_stocks[
        [
            "ticker",
            "company_name",
            "market_cap_display",
            "start",
            "end",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "ticker": "Ticker",
        "company_name": "Company",
        "market_cap_display": "Market cap",
        "start": st.column_config.DateColumn("Dataset start"),
        "end": st.column_config.DateColumn("Dataset end"),
    },
)
