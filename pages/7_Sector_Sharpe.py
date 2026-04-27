import streamlit as st

from dashboard_core.analytics import build_sector_sharpe_table
from dashboard_core.data import load_performance_data, load_three_month_returns, load_volatility_data
from dashboard_core.formatters import format_market_cap_billions
from dashboard_core.paths import DAILY_BARS_DIR, PERFORMANCE_FRAME_PATH, VOLATILITY_FRAME_PATH


@st.cache_data
def get_performance_frame():
    return load_performance_data(
        PERFORMANCE_FRAME_PATH,
        columns=["gics_sector", "market_cap", "log_return_1y"],
    )


@st.cache_data
def get_volatility_frame():
    return load_volatility_data(
        VOLATILITY_FRAME_PATH,
        columns=["gics_sector", "market_cap", "realized_vol_3m", "realized_vol_1y"],
    )


@st.cache_data
def get_returns_3m_frame():
    return load_three_month_returns(DAILY_BARS_DIR)


st.set_page_config(page_title="Sector Sharpe", layout="wide")

st.title("Sector Sharpe")
st.caption(
    "Risk-adjusted sector view using annualized Sharpe ratios, market-cap-weighted returns, realized volatility, and a 0% risk-free-rate assumption."
)

try:
    performance_frame = get_performance_frame()
    volatility_frame = get_volatility_frame()
    returns_3m_frame = get_returns_3m_frame()
except FileNotFoundError as exc:
    st.error(f"Missing input file: {exc.filename}")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load sector Sharpe inputs: {exc}")
    st.stop()

sector_sharpe = build_sector_sharpe_table(performance_frame, volatility_frame, returns_3m_frame)

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
metric_col_1.metric("Sectors", f"{sector_sharpe['gics_sector'].nunique():,}")
metric_col_2.metric("Stocks", f"{len(performance_frame):,}")
metric_col_3.metric("Total market cap", format_market_cap_billions(sector_sharpe["total_market_cap"].sum()))

st.dataframe(
    sector_sharpe[
        [
            "gics_sector",
            "stock_count",
            "total_market_cap_display",
            "weight_display",
            "performance_3m_display",
            "performance_1y_display",
            "vol_3m_display",
            "sharpe_3m_display",
            "sharpe_1y_display",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "gics_sector": "GICS sector",
        "stock_count": st.column_config.NumberColumn("Stocks", format="%d"),
        "total_market_cap_display": "Total market cap",
        "weight_display": "Weight",
        "performance_3m_display": "3M",
        "performance_1y_display": "1Y",
        "vol_3m_display": "vol_3m",
        "sharpe_3m_display": "ann_sharpe_3m",
        "sharpe_1y_display": "ann_sharpe_1y",
    },
)
