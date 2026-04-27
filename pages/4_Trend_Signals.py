from pathlib import Path

import pandas as pd
import streamlit as st

from ui_state import render_persistent_selectbox


DEFAULT_UNIVERSE_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/sp500/tickers_enriched.csv")
TREND_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-trend-signals.parquet")
UNIVERSE_REQUIRED_COLUMNS = {
    "ticker",
    "company_name",
    "gics_sector",
    "gics_sub_industry",
}
TREND_REQUIRED_COLUMNS = {
    "ticker",
    "market_cap",
    "latest_close",
    "trend_signal",
    "trend_raw",
    "ma_confirm",
    "tsmom_63",
    "tsmom_126",
    "tsmom_252",
    "relmom_12_1",
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
def load_trend_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = TREND_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Trend parquet is missing required columns: {missing_list}")

    selected_columns = [
        "ticker",
        "market_cap",
        "latest_close",
        "trend_signal",
        "trend_raw",
        "ma_confirm",
        "tsmom_63",
        "tsmom_126",
        "tsmom_252",
        "relmom_12_1",
    ]
    cleaned = frame.loc[:, selected_columns].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
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


def format_score(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.2f}"


st.set_page_config(page_title="Trend Signals", layout="wide")

st.title("Trend Signals")
st.caption("Filter the universe by GICS sector and sub-industry.")

try:
    universe = load_universe_data(str(DEFAULT_UNIVERSE_PATH))
    trend_frame = load_trend_data(str(TREND_FRAME_PATH))
except FileNotFoundError as exc:
    st.error(f"Missing input file: {exc.filename}")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load trend data: {exc}")
    st.stop()

available_sectors = sorted(universe["gics_sector"].unique().tolist())
filter_col_1, filter_col_2 = st.columns(2)

with filter_col_1:
    selected_sector = render_persistent_selectbox(
        "Select a GICS sector",
        available_sectors,
        state_key="shared_market_sector",
        widget_key="_trend_signals_sector",
    )

sector_universe = universe.loc[universe["gics_sector"] == selected_sector].copy()
available_sub_industries = ["All"] + sorted(sector_universe["gics_sub_industry"].unique().tolist())

with filter_col_2:
    selected_sub_industry = render_persistent_selectbox(
        "Select a sub-industry",
        available_sub_industries,
        state_key="shared_market_sub_industry",
        widget_key="_trend_signals_sub_industry",
        default="All",
    )

if selected_sub_industry == "All":
    filtered_stocks = sector_universe.copy()
else:
    filtered_stocks = sector_universe.loc[
        sector_universe["gics_sub_industry"] == selected_sub_industry
    ].copy()

filtered_stocks = filtered_stocks.merge(trend_frame, on="ticker", how="left")
filtered_stocks["market_cap_display"] = filtered_stocks["market_cap"].apply(format_market_cap_billions)
filtered_stocks["trend_signal_display"] = filtered_stocks["trend_signal"].apply(format_score)
filtered_stocks["trend_raw_display"] = filtered_stocks["trend_raw"].apply(format_score)
filtered_stocks["ma_confirm_display"] = filtered_stocks["ma_confirm"].apply(format_percent)
filtered_stocks["tsmom_63_display"] = filtered_stocks["tsmom_63"].apply(format_percent)
filtered_stocks["tsmom_126_display"] = filtered_stocks["tsmom_126"].apply(format_percent)
filtered_stocks["tsmom_252_display"] = filtered_stocks["tsmom_252"].apply(format_percent)
filtered_stocks["relmom_12_1_display"] = filtered_stocks["relmom_12_1"].apply(format_percent)
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
            "trend_signal_display",
            "trend_raw_display",
            "ma_confirm_display",
            "tsmom_63_display",
            "tsmom_126_display",
            "tsmom_252_display",
            "relmom_12_1_display",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "ticker": "Ticker",
        "company_name": "Company",
        "market_cap_display": "Market cap",
        "latest_close": st.column_config.NumberColumn("Price", format="$%.2f"),
        "trend_signal_display": "trend_signal",
        "trend_raw_display": "trend_raw",
        "ma_confirm_display": "ma_confirm",
        "tsmom_63_display": "tsmom_63",
        "tsmom_126_display": "tsmom_126",
        "tsmom_252_display": "tsmom_252",
        "relmom_12_1_display": "relmom_12_1",
    },
)
