from pathlib import Path
import math

import altair as alt
import pandas as pd
import streamlit as st

from ui_state import render_persistent_selectbox


UNIVERSE_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/sp500/tickers_enriched.csv")
DAILY_BARS_DIR = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/daily-bars")
PERFORMANCE_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-performance-metrics.parquet")
VOLATILITY_FRAME_PATH = Path("/Users/jalalelhazzat/Documents/Codex-Projects/jnbooks/data/frames/daily-bars-realized-volatility.parquet")
REQUIRED_COLUMNS = {"ticker", "company_name", "gics_sector", "gics_sub_industry"}
PERFORMANCE_REQUIRED_COLUMNS = {"ticker", "market_cap", "log_return_ytd"}
VOLATILITY_REQUIRED_COLUMNS = {"ticker", "realized_vol_6m"}
TIME_WINDOW_OPTIONS = {
    "3M": 63,
    "6M": 126,
    "1Y": 252,
    "3Y": 756,
    "5Y": 1260,
    "Max": None,
}


@st.cache_data
def load_universe_data(csv_path: str) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"CSV is missing required columns: {missing_list}")

    cleaned = frame.copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    cleaned["company_name"] = cleaned["company_name"].fillna("").astype(str).str.strip()
    cleaned["gics_sector"] = cleaned["gics_sector"].fillna("Unknown").astype(str).str.strip()
    cleaned["gics_sub_industry"] = cleaned["gics_sub_industry"].fillna("Unknown").astype(str).str.strip()
    return cleaned.sort_values(["gics_sector", "gics_sub_industry", "ticker"]).reset_index(drop=True)


@st.cache_data
def load_daily_bars(ticker: str) -> pd.DataFrame:
    parquet_path = DAILY_BARS_DIR / f"{ticker}.parquet"
    frame = pd.read_parquet(parquet_path)
    expected_columns = {"date", "open", "high", "low", "close", "volume"}
    missing_columns = expected_columns.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Daily bars file for {ticker} is missing required columns: {missing_list}")

    cleaned = frame.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    return cleaned.sort_values("date").reset_index(drop=True)


@st.cache_data
def load_performance_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = PERFORMANCE_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Performance frame is missing required columns: {missing_list}")

    cleaned = frame.loc[:, ["ticker", "market_cap", "log_return_ytd"]].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


@st.cache_data
def load_volatility_data(parquet_path: str) -> pd.DataFrame:
    frame = pd.read_parquet(parquet_path)
    missing_columns = VOLATILITY_REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Volatility frame is missing required columns: {missing_list}")

    cleaned = frame.loc[:, ["ticker", "realized_vol_6m"]].copy()
    cleaned["ticker"] = cleaned["ticker"].fillna("").astype(str).str.strip()
    return cleaned.drop_duplicates(subset=["ticker"])


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


def filter_prices_by_window(prices: pd.DataFrame, selected_window: str) -> pd.DataFrame:
    window_size = TIME_WINDOW_OPTIONS[selected_window]
    if window_size is None:
        return prices.copy()
    return prices.tail(window_size).reset_index(drop=True)


def format_market_cap_billions(value: float) -> str:
    if pd.isna(value):
        return ""
    billions = float(value) / 1_000_000_000
    return f"${billions:,.2f}b"


def format_log_return_as_percent(value: float) -> str:
    if pd.isna(value):
        return ""
    simple_return = math.exp(float(value)) - 1
    return f"{simple_return * 100:,.1f}%"


def format_percent(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value) * 100:,.1f}%"


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
    universe = load_universe_data(str(UNIVERSE_PATH))
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
    performance_frame = load_performance_data(str(PERFORMANCE_FRAME_PATH))
    volatility_frame = load_volatility_data(str(VOLATILITY_FRAME_PATH))
except FileNotFoundError as exc:
    st.error(f"Missing input file: {exc.filename}")
    st.stop()
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Failed to load metric frames: {exc}")
    st.stop()

universe_lookup = (
    universe.loc[:, ["ticker", "company_name", "gics_sector", "gics_sub_industry"]]
    .drop_duplicates(subset=["ticker"])
    .set_index("ticker")
    .to_dict(orient="index")
)

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

sector_universe = universe.loc[universe["gics_sector"] == selected_sector].copy()
available_sub_industries = sorted(sector_universe["gics_sub_industry"].unique().tolist())
with filter_row_1_col_2:
    selected_sub_industry = render_persistent_selectbox(
        "Sub-industry",
        available_sub_industries,
        state_key="graphs_sub_industry",
        widget_key="_graphs_sub_industry",
    )

sub_industry_universe = sector_universe.loc[
    sector_universe["gics_sub_industry"] == selected_sub_industry
].copy()
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
    prices = load_daily_bars(selected_ticker)
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
