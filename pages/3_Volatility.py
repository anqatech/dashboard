from pathlib import Path

import pandas as pd
import streamlit as st

from ui_state import render_persistent_selectbox


DEFAULT_UNIVERSE_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/sp500/tickers_enriched.csv")
STATUS_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-database-status-with-market-cap.parquet")
VOLATILITY_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-realized-volatility.parquet")
UNIVERSE_REQUIRED_COLUMNS = {
    "ticker",
    "company_name",
    "gics_sector",
    "gics_sub_industry",
}
STATUS_REQUIRED_COLUMNS = {"ticker", "market_cap"}
VOLATILITY_REQUIRED_COLUMNS = {
    "ticker",
    "latest_close",
    "realized_vol_1m",
    "realized_vol_3m",
    "realized_vol_6m",
    "realized_vol_1y",
}


@st.cache_data
def load_universe_data(csv_path: str) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    missing_columns = UNIVERSE_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV is missing required columns: {missing_list}")

    cleaned = frame.copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    cleaned["company_name"] = cleaned["company_name"].fillna("").astype(str).str.strip()
    cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    cleaned["gics_sub_industry"] = cleaned["gics_sub_industry"].fillna("Unknown").astype(str).str.strip()
    return cleaned


@st.cache_data
def load_status_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = STATUS_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Status parquet is missing required columns: {missing_list}")

    cleaned = frame.loc[:, ["ticker", "market_cap"]].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


@st.cache_data
def load_volatility_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = VOLATILITY_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Volatility parquet is missing required columns: {missing_list}")

    selected_columns = [
        "ticker",
        "latest_close",
        "realized_vol_1m",
        "realized_vol_3m",
        "realized_vol_6m",
        "realized_vol_1y",
    ]
    cleaned = frame.loc[:, selected_columns].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


def format_market_cap_billions(value: float) -> str:
    if pd.isna(value):
        return ""
    billions = float(value) / 1_000_000_000
    return f"${billions:,.2f}b"


def format_volatility(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value) * 100:,.1f}%"


st.set_page_config(page_title="Volatility", layout="wide")

st.title("Volatility")
st.caption("Filter the universe by GICS sector and sub-industry.")

try:
    universe = load_universe_data(str(DEFAULT_UNIVERSE_PATH))
    status_frame = load_status_data(str(STATUS_FRAME_PATH))
    volatility_frame = load_volatility_data(str(VOLATILITY_FRAME_PATH))
except FileNotFoundError as exc:
    st.error(f"Missing input file: {exc.filename}")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load volatility data: {exc}")
    st.stop()

available_sectors = sorted(universe["gics_sector"].unique().tolist())
filter_col_1, filter_col_2 = st.columns(2)

with filter_col_1:
    selected_sector = render_persistent_selectbox(
        "Select a GICS sector",
        available_sectors,
        state_key="shared_market_sector",
        widget_key="_volatility_sector",
    )

sector_universe = universe.loc[universe["gics_sector"] == selected_sector].copy()
available_sub_industries = ["All"] + sorted(sector_universe["gics_sub_industry"].unique().tolist())

with filter_col_2:
    selected_sub_industry = render_persistent_selectbox(
        "Select a sub-industry",
        available_sub_industries,
        state_key="shared_market_sub_industry",
        widget_key="_volatility_sub_industry",
        default="All",
    )

if selected_sub_industry == "All":
    filtered_stocks = sector_universe.copy()
else:
    filtered_stocks = sector_universe.loc[
        sector_universe["gics_sub_industry"] == selected_sub_industry
    ].copy()

filtered_stocks = filtered_stocks.merge(status_frame, on="ticker", how="left")
filtered_stocks = filtered_stocks.merge(volatility_frame, on="ticker", how="left")
filtered_stocks["market_cap_display"] = filtered_stocks["market_cap"].apply(format_market_cap_billions)
filtered_stocks["vol_1m_display"] = filtered_stocks["realized_vol_1m"].apply(format_volatility)
filtered_stocks["vol_3m_display"] = filtered_stocks["realized_vol_3m"].apply(format_volatility)
filtered_stocks["vol_6m_display"] = filtered_stocks["realized_vol_6m"].apply(format_volatility)
filtered_stocks["vol_1y_display"] = filtered_stocks["realized_vol_1y"].apply(format_volatility)
filtered_stocks = filtered_stocks.sort_values(
    ["market_cap", "ticker", "company_name"],
    ascending=[False, True, True],
    na_position="last",
).reset_index(drop=True)

st.dataframe(
    filtered_stocks[
        [
            "ticker",
            "company_name",
            "market_cap_display",
            "latest_close",
            "vol_1m_display",
            "vol_3m_display",
            "vol_6m_display",
            "vol_1y_display",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "ticker": "Ticker",
        "company_name": "Company",
        "market_cap_display": "Market cap",
        "latest_close": st.column_config.NumberColumn("Price", format="$%.2f"),
        "vol_1m_display": "vol_1m",
        "vol_3m_display": "vol_3m",
        "vol_6m_display": "vol_6m",
        "vol_1y_display": "vol_1y",
    },
)
