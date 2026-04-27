import streamlit as st

from dashboard_core.analytics import build_sector_volatility_table
from dashboard_core.data import load_volatility_data
from dashboard_core.formatters import format_market_cap_billions
from dashboard_core.paths import VOLATILITY_FRAME_PATH
@st.cache_data
def get_volatility_frame():
    return load_volatility_data(
        VOLATILITY_FRAME_PATH,
        columns=[
            "gics_sector",
            "market_cap",
            "realized_vol_1m",
            "realized_vol_3m",
            "realized_vol_6m",
            "realized_vol_1y",
        ],
    )


st.set_page_config(page_title="Sector Volatility", layout="wide")

st.title("Sector Volatility")
st.caption("Market-cap-weighted realized volatility by sector based on the local stock volatility frame.")

try:
    volatility_frame = get_volatility_frame()
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
