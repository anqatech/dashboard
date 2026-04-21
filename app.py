import os
from datetime import date, timedelta

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv


API_BASE_URL = "https://api.massive.com"


def fetch_daily_bars(ticker: str, bars_to_show: int, api_key: str) -> pd.DataFrame:
    end_date = date.today()
    start_date = end_date - timedelta(days=max(bars_to_show * 3, 30))

    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            f"{API_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.isoformat()}/{end_date.isoformat()}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            params={
                "adjusted": "true",
                "sort": "asc",
                "limit": 5000,
            },
        )
    response.raise_for_status()

    payload = response.json()
    results = payload.get("results", [])
    if not results:
        raise ValueError(f"No daily bars were returned for ticker '{ticker}'.")

    frame = pd.DataFrame(
        [
            {
                "date": pd.to_datetime(bar["t"], unit="ms"),
                "open": bar["o"],
                "high": bar["h"],
                "low": bar["l"],
                "close": bar["c"],
                "volume": bar["v"],
            }
            for bar in results
        ]
    )
    return frame.tail(bars_to_show).reset_index(drop=True)


load_dotenv()
st.set_page_config(page_title="Stock Dashboard", layout="wide")

st.title("Stock Market Dashboard")
st.caption("Minimal first slice: one ticker, recent daily prices, one chart.")

api_key = os.getenv("MASSIVE_API_KEY", "").strip()
if not api_key:
    st.warning("Set `MASSIVE_API_KEY` in a `.env` file before loading market data.")

with st.form("ticker_form"):
    left_col, right_col = st.columns([2, 1])

    with left_col:
        ticker = st.text_input(
            "Ticker",
            value="AAPL",
            help="Examples: AAPL, MSFT, NVDA",
        ).strip().upper()

    with right_col:
        bars_to_show = st.slider("Bars to show", min_value=10, max_value=90, value=30, step=10)

    submitted = st.form_submit_button("Load daily prices")

if submitted:
    if not api_key:
        st.stop()

    if not ticker:
        st.error("Enter a stock ticker before loading data.")
        st.stop()

    try:
        with st.spinner(f"Loading daily prices for {ticker}..."):
            prices = fetch_daily_bars(ticker=ticker, bars_to_show=bars_to_show, api_key=api_key)
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        st.error(f"Massive returned an HTTP error ({status_code}). Double-check the ticker and API key.")
        st.stop()
    except httpx.RequestError:
        st.error("The request to Massive failed. Check your network connection and try again.")
        st.stop()
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    latest_close = prices["close"].iloc[-1]
    previous_close = prices["close"].iloc[-2] if len(prices) > 1 else latest_close
    change = latest_close - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0.0

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric("Latest close", f"${latest_close:,.2f}")
    metric_col_2.metric("Day change", f"{change:+.2f}", f"{change_pct:+.2f}%")
    metric_col_3.metric("Rows shown", str(len(prices)))

    st.subheader(f"{ticker} closing prices")
    st.line_chart(prices.set_index("date")["close"], height=320)

    st.subheader("Recent daily bars")
    st.dataframe(
        prices,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date"),
            "open": st.column_config.NumberColumn("Open", format="$%.2f"),
            "high": st.column_config.NumberColumn("High", format="$%.2f"),
            "low": st.column_config.NumberColumn("Low", format="$%.2f"),
            "close": st.column_config.NumberColumn("Close", format="$%.2f"),
            "volume": st.column_config.NumberColumn("Volume", format="%d"),
        },
    )
