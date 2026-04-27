import streamlit as st

from dashboard_core.analytics import build_sector_performance_table
from dashboard_core.data import load_performance_data
from dashboard_core.formatters import format_market_cap_billions
from dashboard_core.paths import PERFORMANCE_FRAME_PATH
@st.cache_data
def get_performance_frame():
    return load_performance_data(
        PERFORMANCE_FRAME_PATH,
        columns=[
            "gics_sector",
            "market_cap",
            "log_return_1d",
            "log_return_1w",
            "log_return_1m",
            "log_return_ytd",
            "log_return_1y",
            "log_return_3y",
        ],
    )


st.set_page_config(page_title="Sector Performance", layout="wide")

st.title("Sector Performance")
st.caption("Market-cap-weighted sector performance based on the local stock return frame.")

try:
    performance_frame = get_performance_frame()
except FileNotFoundError:
    st.error(f"Could not find the performance parquet file at `{PERFORMANCE_FRAME_PATH}`.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load the performance parquet file: {exc}")
    st.stop()

sector_performance = build_sector_performance_table(performance_frame)

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Sectors", f"{sector_performance['gics_sector'].nunique():,}")
metric_col_2.metric("Stocks", f"{len(performance_frame):,}")
metric_col_3.metric("Total market cap", format_market_cap_billions(sector_performance["total_market_cap"].sum()))

st.dataframe(
    sector_performance[
        [
            "gics_sector",
            "stock_count",
            "total_market_cap_display",
            "weight_display",
            "1D",
            "1W",
            "1M",
            "YTD",
            "1Y",
            "3Y",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "gics_sector": "GICS sector",
        "stock_count": st.column_config.NumberColumn("Stocks", format="%d"),
        "total_market_cap_display": "Total market cap",
        "weight_display": "Weight",
        "1D": "1D",
        "1W": "1W",
        "1M": "1M",
        "YTD": "YTD",
        "1Y": "1Y",
        "3Y": "3Y",
    },
)
