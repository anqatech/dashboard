import streamlit as st

from dashboard_core.analytics import build_trend_signals_table
from dashboard_core.data import filter_universe, load_trend_data, load_universe_data
from dashboard_core.paths import TREND_FRAME_PATH, UNIVERSE_PATH
from ui_state import render_persistent_selectbox

@st.cache_data
def get_universe():
    return load_universe_data(UNIVERSE_PATH)


@st.cache_data
def get_trend_frame():
    return load_trend_data(
        TREND_FRAME_PATH,
        columns=[
            "market_cap",
            "latest_close",
            "trend_signal",
            "trend_raw",
            "ma_confirm",
            "tsmom_63",
            "tsmom_126",
            "tsmom_252",
            "relmom_12_1",
        ],
    )


st.set_page_config(page_title="Trend Signals", layout="wide")

st.title("Trend Signals")
st.caption("Filter the universe by GICS sector and sub-industry.")

try:
    universe = get_universe()
    trend_frame = get_trend_frame()
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

sector_universe = filter_universe(universe, selected_sector)
available_sub_industries = ["All"] + sorted(sector_universe["gics_sub_industry"].unique().tolist())

with filter_col_2:
    selected_sub_industry = render_persistent_selectbox(
        "Select a sub-industry",
        available_sub_industries,
        state_key="shared_market_sub_industry",
        widget_key="_trend_signals_sub_industry",
        default="All",
    )

filtered_stocks = build_trend_signals_table(
    filter_universe(universe, selected_sector, selected_sub_industry),
    trend_frame,
)

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
