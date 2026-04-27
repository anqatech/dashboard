import streamlit as st

from dashboard_core.analytics import (
    build_sector_summary,
    build_sub_industry_summary,
    build_universe_stock_table,
)
from dashboard_core.data import filter_universe, load_status_data, load_universe_data
from dashboard_core.formatters import format_market_cap_billions_whole
from dashboard_core.paths import STATUS_FRAME_PATH, UNIVERSE_PATH
from ui_state import render_persistent_selectbox

@st.cache_data
def get_universe():
    return load_universe_data(UNIVERSE_PATH)


@st.cache_data
def get_status_frame():
    return load_status_data(STATUS_FRAME_PATH, columns=["market_cap", "start", "end"])


st.set_page_config(page_title="Universe Analysis", layout="wide")

st.title("Universe Analysis")
st.caption("Explore the enriched ticker universe by GICS sector, sub-industry, and stock list.")

try:
    universe = get_universe()
except FileNotFoundError:
    st.error(f"Could not find the universe file at `{UNIVERSE_PATH}`.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load the universe file: {exc}")
    st.stop()

try:
    status_frame = get_status_frame()
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

sector_summary = build_sector_summary(universe_with_status)

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

sector_universe = filter_universe(universe, selected_sector)
sub_industry_summary = build_sub_industry_summary(sector_universe)

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

filtered_stocks = build_universe_stock_table(
    filter_universe(universe, selected_sector, selected_sub_industry),
    status_frame,
)

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
