import streamlit as st

from dashboard_core.analytics import build_stock_screener_table
from dashboard_core.data import filter_universe, load_performance_data, load_status_data, load_universe_data
from dashboard_core.paths import PERFORMANCE_FRAME_PATH, STATUS_FRAME_PATH, UNIVERSE_PATH
from ui_state import render_persistent_selectbox

@st.cache_data
def get_universe():
    return load_universe_data(UNIVERSE_PATH)


@st.cache_data
def get_status_frame():
    return load_status_data(STATUS_FRAME_PATH, columns=["market_cap", "start", "end"])


@st.cache_data
def get_performance_frame():
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


st.set_page_config(page_title="Stock Screener", layout="wide")

st.title("Stock Screener")
st.caption("Filter the universe by GICS sector and sub-industry.")

try:
    universe = get_universe()
    status_frame = get_status_frame()
    performance_frame = get_performance_frame()
except FileNotFoundError as exc:
    st.error(f"Missing input file: {exc.filename}")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load screener data: {exc}")
    st.stop()

available_sectors = sorted(universe["gics_sector"].unique().tolist())
filter_col_1, filter_col_2 = st.columns(2)

with filter_col_1:
    selected_sector = render_persistent_selectbox(
        "Select a GICS sector",
        available_sectors,
        state_key="shared_market_sector",
        widget_key="_stock_screener_sector",
    )

sector_universe = filter_universe(universe, selected_sector)
available_sub_industries = ["All"] + sorted(sector_universe["gics_sub_industry"].unique().tolist())

with filter_col_2:
    selected_sub_industry = render_persistent_selectbox(
        "Select a sub-industry",
        available_sub_industries,
        state_key="shared_market_sub_industry",
        widget_key="_stock_screener_sub_industry",
        default="All",
    )

filtered_stocks = build_stock_screener_table(
    filter_universe(universe, selected_sector, selected_sub_industry),
    status_frame,
    performance_frame,
)

st.dataframe(
    filtered_stocks[
        [
            "ticker",
            "company_name",
            "market_cap_display",
            "latest_price_display",
            "1D",
            "1W",
            "1M",
            "YTD",
            "1Y",
            "3Y",
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
        "latest_price_display": st.column_config.NumberColumn("Price", format="$%.2f"),
        "start": st.column_config.DateColumn("Dataset start"),
        "end": st.column_config.DateColumn("Dataset end"),
    },
)
