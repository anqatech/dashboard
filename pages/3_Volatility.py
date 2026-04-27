import streamlit as st

from dashboard_core.analytics import build_stock_volatility_table
from dashboard_core.data import filter_universe, load_status_data, load_universe_data, load_volatility_data
from dashboard_core.paths import STATUS_FRAME_PATH, UNIVERSE_PATH, VOLATILITY_FRAME_PATH
from ui_state import render_persistent_selectbox

@st.cache_data
def get_universe():
    return load_universe_data(UNIVERSE_PATH)


@st.cache_data
def get_status_frame():
    return load_status_data(STATUS_FRAME_PATH, columns=["market_cap"])


@st.cache_data
def get_volatility_frame():
    return load_volatility_data(
        VOLATILITY_FRAME_PATH,
        columns=[
            "latest_close",
            "realized_vol_1m",
            "realized_vol_3m",
            "realized_vol_6m",
            "realized_vol_1y",
        ],
    )


st.set_page_config(page_title="Volatility", layout="wide")

st.title("Volatility")
st.caption("Filter the universe by GICS sector and sub-industry.")

try:
    universe = get_universe()
    status_frame = get_status_frame()
    volatility_frame = get_volatility_frame()
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

sector_universe = filter_universe(universe, selected_sector)
available_sub_industries = ["All"] + sorted(sector_universe["gics_sub_industry"].unique().tolist())

with filter_col_2:
    selected_sub_industry = render_persistent_selectbox(
        "Select a sub-industry",
        available_sub_industries,
        state_key="shared_market_sub_industry",
        widget_key="_volatility_sub_industry",
        default="All",
    )

filtered_stocks = build_stock_volatility_table(
    filter_universe(universe, selected_sector, selected_sub_industry),
    status_frame,
    volatility_frame,
)

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
