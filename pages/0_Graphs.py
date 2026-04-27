import altair as alt
import pandas as pd
import streamlit as st

from dashboard_core.analytics import TIME_WINDOW_OPTIONS, filter_prices_by_window
from dashboard_core.data import (
    build_universe_lookup,
    filter_universe,
    load_daily_bars,
    load_performance_data,
    load_universe_data,
    load_volatility_data,
)
from dashboard_core.formatters import (
    format_log_return_as_percent,
    format_market_cap_billions,
    format_percent,
)
from dashboard_core.paths import DAILY_BARS_DIR, PERFORMANCE_FRAME_PATH, UNIVERSE_PATH, VOLATILITY_FRAME_PATH
from ui_state import render_persistent_selectbox

@st.cache_data
def get_universe():
    return load_universe_data(UNIVERSE_PATH)


@st.cache_data
def get_daily_bars(ticker: str):
    return load_daily_bars(ticker, DAILY_BARS_DIR)


@st.cache_data
def get_performance_frame():
    return load_performance_data(
        PERFORMANCE_FRAME_PATH,
        columns=["market_cap", "log_return_ytd"],
    )


@st.cache_data
def get_volatility_frame():
    return load_volatility_data(
        VOLATILITY_FRAME_PATH,
        columns=["realized_vol_6m"],
    )


def build_candlestick_chart(prices: pd.DataFrame) -> alt.Chart:
    min_low = float(prices["low"].min())
    max_high = float(prices["high"].max())
    price_span = max_high - min_low
    padding = max(price_span * 0.2, max_high * 0.01, 1.0)
    y_min = min_low - padding
    y_max = max_high + padding

    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0

    candle_count = len(prices)
    if candle_count <= 70:
        candle_size = 8
    elif candle_count <= 140:
        candle_size = 5
    elif candle_count <= 280:
        candle_size = 3
    elif candle_count <= 800:
        candle_size = 2
    else:
        candle_size = 1

    chart_data = prices.copy()
    chart_data["candle_color"] = chart_data.apply(
        lambda row: "#2ca02c" if row["close"] >= row["open"] else "#d62728",
        axis=1,
    )

    wick = (
        alt.Chart(chart_data)
        .mark_rule()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y(
                "low:Q",
                title="Price",
                scale=alt.Scale(domain=[y_min, y_max], zero=False),
            ),
            y2="high:Q",
            color=alt.Color("candle_color:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("open:Q", title="Open", format=",.2f"),
                alt.Tooltip("high:Q", title="High", format=",.2f"),
                alt.Tooltip("low:Q", title="Low", format=",.2f"),
                alt.Tooltip("close:Q", title="Close", format=",.2f"),
                alt.Tooltip("volume:Q", title="Volume", format=",.0f"),
            ],
        )
    )

    candle = (
        alt.Chart(chart_data)
        .mark_bar(size=candle_size)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("open:Q", title="Price"),
            y2="close:Q",
            color=alt.Color("candle_color:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("open:Q", title="Open", format=",.2f"),
                alt.Tooltip("high:Q", title="High", format=",.2f"),
                alt.Tooltip("low:Q", title="Low", format=",.2f"),
                alt.Tooltip("close:Q", title="Close", format=",.2f"),
                alt.Tooltip("volume:Q", title="Volume", format=",.0f"),
            ],
        )
    )

    return (wick + candle).properties(height=320).interactive()
def sync_graph_filters_from_lookup(universe_lookup: dict[str, dict[str, str]]) -> None:
    raw_value = st.session_state.get("_graphs_ticker_lookup", "")
    lookup_ticker = raw_value.strip().upper()
    st.session_state["graphs_ticker_lookup"] = lookup_ticker

    if not lookup_ticker:
        st.session_state["graphs_ticker_lookup_error"] = ""
        return

    ticker_details = universe_lookup.get(lookup_ticker)
    if ticker_details is None:
        st.session_state["graphs_ticker_lookup_error"] = f"Ticker `{lookup_ticker}` was not found in the universe."
        return

    st.session_state["graphs_ticker_lookup_error"] = ""
    st.session_state["graphs_sector"] = ticker_details["gics_sector"]
    st.session_state["graphs_sub_industry"] = ticker_details["gics_sub_industry"]
    st.session_state["graphs_ticker"] = lookup_ticker


st.set_page_config(page_title="Graphs", layout="wide")
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1 {
        margin-bottom: 0.25rem;
    }
    div[data-testid="stCaptionContainer"] {
        margin-bottom: 0.5rem;
    }
    div[data-testid="stMetric"] {
        padding-top: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    performance_frame = get_performance_frame()
    volatility_frame = get_volatility_frame()
except FileNotFoundError as exc:
    st.error(f"Missing input file: {exc.filename}")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load metric frames: {exc}")
    st.stop()

universe_lookup = build_universe_lookup(universe)

filter_row_1_col_0, filter_row_1_col_1, filter_row_1_col_2 = st.columns([0.9, 1.15, 1.95])

with filter_row_1_col_0:
    st.text_input(
        "Ticker lookup",
        key="_graphs_ticker_lookup",
        value=st.session_state.get("graphs_ticker_lookup", ""),
        placeholder="Enter a ticker like AAPL",
        on_change=sync_graph_filters_from_lookup,
        args=(universe_lookup,),
    )

lookup_error = st.session_state.get("graphs_ticker_lookup_error", "")
if lookup_error:
    st.error(lookup_error)

available_sectors = sorted(universe["gics_sector"].unique().tolist())
with filter_row_1_col_1:
    selected_sector = render_persistent_selectbox(
        "Sector",
        available_sectors,
        state_key="graphs_sector",
        widget_key="_graphs_sector",
    )

sector_universe = filter_universe(universe, selected_sector)
available_sub_industries = sorted(sector_universe["gics_sub_industry"].unique().tolist())
with filter_row_1_col_2:
    selected_sub_industry = render_persistent_selectbox(
        "Sub-industry",
        available_sub_industries,
        state_key="graphs_sub_industry",
        widget_key="_graphs_sub_industry",
    )

sub_industry_universe = filter_universe(universe, selected_sector, selected_sub_industry)
sub_industry_universe = sub_industry_universe.sort_values(["ticker", "company_name"]).reset_index(drop=True)
ticker_options = sub_industry_universe["ticker"].tolist()
company_lookup = dict(zip(sub_industry_universe["ticker"], sub_industry_universe["company_name"]))

filter_row_2_col_1, filter_row_2_col_2 = st.columns([2.6, 0.7])

with filter_row_2_col_1:
    selected_ticker = render_persistent_selectbox(
        "Ticker",
        ticker_options,
        state_key="graphs_ticker",
        widget_key="_graphs_ticker",
        format_func=lambda ticker: f"{ticker} - {company_lookup.get(ticker, '')}",
    )

with filter_row_2_col_2:
    window_options = list(TIME_WINDOW_OPTIONS.keys())
    selected_window = render_persistent_selectbox(
        "Window",
        window_options,
        state_key="graphs_window",
        widget_key="_graphs_window",
        default="1Y",
    )

try:
    prices = get_daily_bars(selected_ticker)
except FileNotFoundError:
    st.error(f"Could not find a daily bars parquet file for `{selected_ticker}` in `{DAILY_BARS_DIR}`.")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load daily bars for {selected_ticker}: {exc}")
    st.stop()

filtered_prices = filter_prices_by_window(prices, selected_window)
if filtered_prices.empty:
    st.error(f"No price data is available for the selected window: {selected_window}.")
    st.stop()

ticker_metrics = performance_frame.loc[performance_frame["ticker"] == selected_ticker]
ticker_volatility = volatility_frame.loc[volatility_frame["ticker"] == selected_ticker]

market_cap = ticker_metrics["market_cap"].iloc[0] if not ticker_metrics.empty else float("nan")
ytd_change = ticker_metrics["log_return_ytd"].iloc[0] if not ticker_metrics.empty else float("nan")
realized_vol_6m = ticker_volatility["realized_vol_6m"].iloc[0] if not ticker_volatility.empty else float("nan")

latest_close = filtered_prices["close"].iloc[-1]
previous_close = filtered_prices["close"].iloc[-2] if len(filtered_prices) > 1 else latest_close
change = latest_close - previous_close
change_pct = (change / previous_close * 100) if previous_close else 0.0

metric_col_1, metric_col_2, metric_col_3, metric_col_4, metric_col_5 = st.columns(5)
metric_col_1.metric("Latest close", f"${latest_close:,.2f}")
metric_col_2.metric("Day change", f"{change:+.2f}", f"{change_pct:+.2f}%")
metric_col_3.metric(
    "YTD change",
    format_log_return_as_percent(ytd_change),
    format_log_return_as_percent(ytd_change),
)
metric_col_4.metric("6M realized vol", format_percent(realized_vol_6m))
metric_col_5.metric("Market cap", format_market_cap_billions(market_cap))

company_name = company_lookup.get(selected_ticker, "")
st.caption(f"{selected_sector} > {selected_sub_industry}")
chart_heading = f"{selected_ticker} closing prices"
if company_name:
    chart_heading = f"{chart_heading} - {company_name}"
st.subheader(chart_heading)
st.altair_chart(build_candlestick_chart(filtered_prices), use_container_width=True)

st.subheader("Daily bars")
st.dataframe(
    filtered_prices,
    use_container_width=True,
    hide_index=True,
    column_config={
        "ticker": "Ticker",
        "date": st.column_config.DateColumn("Date"),
        "open": st.column_config.NumberColumn("Open", format="$%.2f"),
        "high": st.column_config.NumberColumn("High", format="$%.2f"),
        "low": st.column_config.NumberColumn("Low", format="$%.2f"),
        "close": st.column_config.NumberColumn("Close", format="$%.2f"),
        "volume": st.column_config.NumberColumn("Volume", format="%d"),
        "vwap": st.column_config.NumberColumn("VWAP", format="$%.2f"),
        "transactions": st.column_config.NumberColumn("Transactions", format="%d"),
    },
)
