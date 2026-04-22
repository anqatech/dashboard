from pathlib import Path

import pandas as pd
import streamlit as st


DEFAULT_UNIVERSE_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/sp500/tickers_enriched.csv")
REQUIRED_COLUMNS = {
    "ticker",
    "company_name",
    "gics_sector",
    "gics_sub_industry",
    "headquarters_state",
    "date_added",
}


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
    cleaned["headquarters_state"] = cleaned["headquarters_state"].fillna("Unknown").astype(str).str.strip()
    cleaned["date_added"] = pd.to_datetime(cleaned["date_added"], errors="coerce")

    return cleaned


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

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Tickers", f"{len(universe):,}")
metric_col_2.metric("GICS sectors", universe["gics_sector"].nunique())
metric_col_3.metric("Sub-industries", universe["gics_sub_industry"].nunique())

sector_summary = (
    universe.groupby("gics_sector", dropna=False)
    .agg(
        ticker_count=("ticker", "count"),
        sub_industry_count=("gics_sub_industry", "nunique"),
    )
    .reset_index()
    .sort_values(["ticker_count", "gics_sector"], ascending=[False, True])
)

st.subheader("Sector summary")
st.dataframe(
    sector_summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        "gics_sector": "GICS sector",
        "ticker_count": st.column_config.NumberColumn("Stocks", format="%d"),
        "sub_industry_count": st.column_config.NumberColumn("Sub-industries", format="%d"),
    },
)

available_sectors = sector_summary["gics_sector"].tolist()
selected_sector = st.selectbox("Select a GICS sector", options=available_sectors, index=0)

sector_universe = universe.loc[universe["gics_sector"] == selected_sector].copy()
sub_industry_summary = (
    sector_universe.groupby("gics_sub_industry", dropna=False)
    .agg(
        ticker_count=("ticker", "count"),
        earliest_added=("date_added", "min"),
        latest_added=("date_added", "max"),
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
        "earliest_added": st.column_config.DateColumn("Earliest date added"),
        "latest_added": st.column_config.DateColumn("Latest date added"),
    },
)

available_sub_industries = sub_industry_summary["gics_sub_industry"].tolist()
selected_sub_industry = st.selectbox(
    "Select a sub-industry",
    options=available_sub_industries,
    index=0,
)

filtered_stocks = (
    sector_universe.loc[sector_universe["gics_sub_industry"] == selected_sub_industry]
    .sort_values(["ticker", "company_name"], ascending=[True, True])
    .reset_index(drop=True)
)

st.subheader(f"Stocks in {selected_sector} / {selected_sub_industry}")
st.dataframe(
    filtered_stocks[
        [
            "ticker",
            "company_name",
            "headquarters_state",
            "date_added",
            "founded_year",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "ticker": "Ticker",
        "company_name": "Company",
        "headquarters_state": "HQ state",
        "date_added": st.column_config.DateColumn("Date added"),
        "founded_year": "Founded year",
    },
)
