from functools import lru_cache

import dash
import dash_ag_grid as dag
from dash import Input, Output, State, callback, ctx, dcc, html
import pandas as pd
import plotly.graph_objects as go

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
from dash_app.grid_theme import GRID_THEME
from dashboard_core.paths import DAILY_BARS_DIR, PERFORMANCE_FRAME_PATH, UNIVERSE_PATH, VOLATILITY_FRAME_PATH


dash.register_page(__name__, path="/", name="Graphs", order=0)


@lru_cache(maxsize=1)
def get_universe() -> pd.DataFrame:
    return load_universe_data(UNIVERSE_PATH)


@lru_cache(maxsize=1)
def get_performance_frame() -> pd.DataFrame:
    return load_performance_data(
        PERFORMANCE_FRAME_PATH,
        columns=["market_cap", "log_return_ytd"],
    )


@lru_cache(maxsize=1)
def get_volatility_frame() -> pd.DataFrame:
    return load_volatility_data(
        VOLATILITY_FRAME_PATH,
        columns=["realized_vol_6m"],
    )


@lru_cache(maxsize=512)
def get_daily_bars_frame(ticker: str) -> pd.DataFrame:
    return load_daily_bars(ticker, DAILY_BARS_DIR)


@lru_cache(maxsize=1)
def get_universe_lookup() -> dict[str, dict[str, str]]:
    return build_universe_lookup(get_universe())


def build_select_options(values: list[str]) -> list[dict[str, str]]:
    return [{"label": value, "value": value} for value in values]


def build_ticker_options(frame: pd.DataFrame) -> list[dict[str, str]]:
    sorted_frame = frame.sort_values(["ticker", "company_name"]).reset_index(drop=True)
    return [
        {
            "label": f"{row.ticker} - {row.company_name}",
            "value": row.ticker,
        }
        for row in sorted_frame.itertuples()
    ]


def get_initial_filters() -> tuple[str, str, str]:
    universe = get_universe()
    sector = sorted(universe["gics_sector"].unique().tolist())[0]
    sector_universe = filter_universe(universe, sector)
    sub_industry = sorted(sector_universe["gics_sub_industry"].unique().tolist())[0]
    ticker_universe = filter_universe(universe, sector, sub_industry)
    ticker = ticker_universe.sort_values(["ticker", "company_name"]).iloc[0]["ticker"]
    return sector, sub_industry, ticker


def build_metric_card(
    label: str,
    value_id: str,
    delta_id: str | None = None,
) -> html.Div:
    children = [
        html.Div(label, className="metric-label"),
        html.Div(id=value_id, className="metric-value"),
    ]
    if delta_id is not None:
        children.append(html.Div(id=delta_id, className="metric-delta metric-delta-neutral"))
    return html.Div(children, className="metric-card")


def build_empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="#101826",
        font={"color": "#f4f4f4"},
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 40, "r": 20, "t": 20, "b": 40},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 16, "color": "#cfd7e6"},
            }
        ],
    )
    return figure


def build_candlestick_figure(prices: pd.DataFrame, ticker: str) -> go.Figure:
    figure = go.Figure(
        data=[
            go.Candlestick(
                x=prices["date"],
                open=prices["open"],
                high=prices["high"],
                low=prices["low"],
                close=prices["close"],
                increasing_line_color="#2ecc71",
                decreasing_line_color="#ff5c5c",
                increasing_fillcolor="#2ecc71",
                decreasing_fillcolor="#ff5c5c",
                name=ticker,
            )
        ]
    )
    figure.update_layout(
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="#101826",
        font={"color": "#f4f4f4"},
        margin={"l": 50, "r": 20, "t": 20, "b": 40},
        height=420,
        xaxis={
            "showgrid": False,
            "rangeslider": {"visible": False},
            "title": "",
        },
        yaxis={
            "title": "Price",
            "gridcolor": "rgba(255, 255, 255, 0.12)",
            "zeroline": False,
        },
        hovermode="x unified",
    )
    return figure


def build_daily_bars_table(prices: pd.DataFrame) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    table_frame = prices.copy()
    table_frame["Date"] = table_frame["date"].dt.strftime("%Y-%m-%d")
    table_frame["Open"] = table_frame["open"].map(lambda value: f"${float(value):,.2f}")
    table_frame["High"] = table_frame["high"].map(lambda value: f"${float(value):,.2f}")
    table_frame["Low"] = table_frame["low"].map(lambda value: f"${float(value):,.2f}")
    table_frame["Close"] = table_frame["close"].map(lambda value: f"${float(value):,.2f}")
    table_frame["Volume"] = table_frame["volume"].map(
        lambda value: "" if pd.isna(value) else f"{int(value):,}"
    )

    selected_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
    if "vwap" in table_frame.columns:
        table_frame["VWAP"] = table_frame["vwap"].map(
            lambda value: "" if pd.isna(value) else f"${float(value):,.2f}"
        )
        selected_columns.append("VWAP")
    if "transactions" in table_frame.columns:
        table_frame["Transactions"] = table_frame["transactions"].map(
            lambda value: "" if pd.isna(value) else f"{int(value):,}"
        )
        selected_columns.append("Transactions")

    display_frame = table_frame.loc[:, selected_columns]
    columns = [{"field": column, "headerName": column, "sortable": True, "filter": True} for column in selected_columns]
    return display_frame.to_dict("records"), columns


def ytd_delta_class(value: float) -> str:
    if pd.isna(value):
        return "metric-delta metric-delta-neutral"
    if value > 0:
        return "metric-delta metric-delta-positive"
    if value < 0:
        return "metric-delta metric-delta-negative"
    return "metric-delta metric-delta-neutral"


def day_change_delta_class(change_pct: float) -> str:
    if change_pct > 0:
        return "metric-delta metric-delta-positive"
    if change_pct < 0:
        return "metric-delta metric-delta-negative"
    return "metric-delta metric-delta-neutral"


def layout() -> html.Div:
    universe = get_universe()
    initial_sector, initial_sub_industry, initial_ticker = get_initial_filters()
    sector_options = build_select_options(sorted(universe["gics_sector"].unique().tolist()))
    sub_industry_options = build_select_options(
        sorted(filter_universe(universe, initial_sector)["gics_sub_industry"].unique().tolist())
    )
    ticker_options = build_ticker_options(filter_universe(universe, initial_sector, initial_sub_industry))

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Ticker lookup", className="control-label"),
                            dcc.Input(
                                id="graphs-ticker-lookup",
                                type="text",
                                placeholder="Enter a ticker like AAPL",
                                debounce=True,
                                persistence=True,
                                persistence_type="session",
                                className="text-input",
                            ),
                        ],
                        className="control-card control-card-lookup",
                    ),
                    html.Div(
                        [
                            html.Label("Sector", className="control-label"),
                            dcc.Dropdown(
                                id="graphs-sector",
                                options=sector_options,
                                value=initial_sector,
                                clearable=False,
                                persistence=True,
                                persistence_type="session",
                                className="dash-dropdown",
                            ),
                        ],
                        className="control-card",
                    ),
                    html.Div(
                        [
                            html.Label("Sub-industry", className="control-label"),
                            dcc.Dropdown(
                                id="graphs-sub-industry",
                                options=sub_industry_options,
                                value=initial_sub_industry,
                                clearable=False,
                                persistence=True,
                                persistence_type="session",
                                className="dash-dropdown",
                            ),
                        ],
                        className="control-card control-card-wide",
                    ),
                ],
                className="controls-grid controls-grid-top",
            ),
            html.Div(id="graphs-lookup-error", className="inline-error"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Ticker", className="control-label"),
                            dcc.Dropdown(
                                id="graphs-ticker",
                                options=ticker_options,
                                value=initial_ticker,
                                clearable=False,
                                persistence=True,
                                persistence_type="session",
                                className="dash-dropdown",
                            ),
                        ],
                        className="control-card control-card-ticker",
                    ),
                    html.Div(
                        [
                            html.Label("Window", className="control-label"),
                            dcc.Dropdown(
                                id="graphs-window",
                                options=build_select_options(list(TIME_WINDOW_OPTIONS.keys())),
                                value="1Y",
                                clearable=False,
                                persistence=True,
                                persistence_type="session",
                                className="dash-dropdown",
                            ),
                        ],
                        className="control-card control-card-window",
                    ),
                ],
                className="controls-grid controls-grid-bottom",
            ),
            html.Div(
                [
                    build_metric_card("Latest close", "metric-latest-close"),
                    build_metric_card("Day change", "metric-day-change", "metric-day-change-delta"),
                    build_metric_card("YTD change", "metric-ytd-change", "metric-ytd-delta"),
                    build_metric_card("6M realized vol", "metric-vol-6m"),
                    build_metric_card("Market cap", "metric-market-cap"),
                ],
                className="metrics-grid",
            ),
            html.Div(id="graphs-classification", className="classification-copy"),
            html.H2(id="graphs-chart-title", className="chart-title"),
            dcc.Graph(id="graphs-chart", figure=build_empty_figure("Select a ticker to view the chart.")),
            html.H3("Daily bars", className="section-heading"),
            dag.AgGrid(
                id="graphs-daily-bars",
                columnDefs=[],
                rowData=[],
                className="table-grid",
                defaultColDef={
                    "resizable": True,
                    "sortable": True,
                    "filter": True,
                    "minWidth": 120,
                    "suppressHeaderMenuButton": True,
                },
                columnSize="sizeToFit",
                dashGridOptions={
                    "theme": GRID_THEME,
                    "pagination": True,
                    "paginationPageSize": 20,
                    "paginationPageSizeSelector": False,
                    "domLayout": "autoHeight",
                },
                style={"width": "100%"},
            ),
        ],
        className="content-stack",
    )


@callback(
    Output("graphs-lookup-error", "children"),
    Output("graphs-sector", "value"),
    Output("graphs-sub-industry", "options"),
    Output("graphs-sub-industry", "value"),
    Output("graphs-ticker", "options"),
    Output("graphs-ticker", "value"),
    Input("graphs-ticker-lookup", "value"),
    Input("graphs-sector", "value"),
    Input("graphs-sub-industry", "value"),
    State("graphs-ticker", "value"),
)
def sync_graph_filters(
    lookup_value: str | None,
    selected_sector: str | None,
    selected_sub_industry: str | None,
    selected_ticker: str | None,
):
    universe = get_universe()
    available_sectors = sorted(universe["gics_sector"].unique().tolist())
    normalized_sector = selected_sector if selected_sector in available_sectors else available_sectors[0]
    lookup_error = ""

    if ctx.triggered_id == "graphs-ticker-lookup" and lookup_value and lookup_value.strip():
        ticker_lookup = lookup_value.strip().upper()
        ticker_details = get_universe_lookup().get(ticker_lookup)
        if ticker_details is None:
            lookup_error = f"Ticker {ticker_lookup} was not found in the universe."
        else:
            normalized_sector = ticker_details["gics_sector"]
            selected_sub_industry = ticker_details["gics_sub_industry"]
            selected_ticker = ticker_lookup

    sector_universe = filter_universe(universe, normalized_sector)
    options = sorted(sector_universe["gics_sub_industry"].unique().tolist())
    if not options:
        return lookup_error, normalized_sector, [], None, [], None

    normalized_sub_industry = (
        selected_sub_industry if selected_sub_industry in options else options[0]
    )
    ticker_universe = filter_universe(universe, normalized_sector, normalized_sub_industry)
    ticker_options = build_ticker_options(ticker_universe)
    available_tickers = [option["value"] for option in ticker_options]
    if not available_tickers:
        return lookup_error, normalized_sector, build_select_options(options), normalized_sub_industry, [], None

    normalized_ticker = selected_ticker if selected_ticker in available_tickers else available_tickers[0]
    return (
        lookup_error,
        normalized_sector,
        build_select_options(options),
        normalized_sub_industry,
        ticker_options,
        normalized_ticker,
    )


@callback(
    Output("graphs-classification", "children"),
    Output("metric-latest-close", "children"),
    Output("metric-day-change", "children"),
    Output("metric-day-change-delta", "children"),
    Output("metric-day-change-delta", "className"),
    Output("metric-ytd-change", "children"),
    Output("metric-ytd-delta", "children"),
    Output("metric-ytd-delta", "className"),
    Output("metric-vol-6m", "children"),
    Output("metric-market-cap", "children"),
    Output("graphs-chart-title", "children"),
    Output("graphs-chart", "figure"),
    Output("graphs-daily-bars", "rowData"),
    Output("graphs-daily-bars", "columnDefs"),
    Input("graphs-sector", "value"),
    Input("graphs-sub-industry", "value"),
    Input("graphs-ticker", "value"),
    Input("graphs-window", "value"),
)
def update_graph_view(
    selected_sector: str,
    selected_sub_industry: str,
    selected_ticker: str,
    selected_window: str,
):
    selected_window = selected_window if selected_window in TIME_WINDOW_OPTIONS else "1Y"
    if not selected_ticker:
        empty_figure = build_empty_figure("Select a ticker to view the chart.")
        return (
            "",
            "",
            "",
            "",
            "metric-delta metric-delta-neutral",
            "",
            "",
            "metric-delta metric-delta-neutral",
            "",
            "",
            "No ticker selected",
            empty_figure,
            [],
            [],
        )

    company_lookup = get_universe_lookup()
    company_name = company_lookup.get(selected_ticker, {}).get("company_name", "")

    try:
        prices = get_daily_bars_frame(selected_ticker)
    except FileNotFoundError:
        message = f"Could not find local daily bars for {selected_ticker}."
        empty_figure = build_empty_figure(message)
        return (
            f"{selected_sector} > {selected_sub_industry}",
            "",
            "",
            "",
            "metric-delta metric-delta-neutral",
            "",
            "",
            "metric-delta metric-delta-neutral",
            "",
            "",
            message,
            empty_figure,
            [],
            [],
        )

    filtered_prices = filter_prices_by_window(prices, selected_window)
    if filtered_prices.empty:
        empty_figure = build_empty_figure(f"No price data is available for the selected window: {selected_window}.")
        return (
            f"{selected_sector} > {selected_sub_industry}",
            "",
            "",
            "",
            "metric-delta metric-delta-neutral",
            "",
            "",
            "metric-delta metric-delta-neutral",
            "",
            "",
            f"{selected_ticker} closing prices",
            empty_figure,
            [],
            [],
        )

    performance_frame = get_performance_frame()
    volatility_frame = get_volatility_frame()
    ticker_metrics = performance_frame.loc[performance_frame["ticker"] == selected_ticker]
    ticker_volatility = volatility_frame.loc[volatility_frame["ticker"] == selected_ticker]

    market_cap = ticker_metrics["market_cap"].iloc[0] if not ticker_metrics.empty else float("nan")
    ytd_change = ticker_metrics["log_return_ytd"].iloc[0] if not ticker_metrics.empty else float("nan")
    realized_vol_6m = (
        ticker_volatility["realized_vol_6m"].iloc[0] if not ticker_volatility.empty else float("nan")
    )

    latest_close = float(filtered_prices["close"].iloc[-1])
    previous_close = float(filtered_prices["close"].iloc[-2]) if len(filtered_prices) > 1 else latest_close
    change = latest_close - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0.0

    chart_title = f"{selected_ticker} closing prices"
    if company_name:
        chart_title = f"{chart_title} - {company_name}"

    figure = build_candlestick_figure(filtered_prices, selected_ticker)
    table_data, table_columns = build_daily_bars_table(filtered_prices)
    ytd_display = format_log_return_as_percent(ytd_change)

    return (
        f"{selected_sector} > {selected_sub_industry}",
        f"${latest_close:,.2f}",
        f"{change:+.2f}",
        f"{change_pct:+.2f}%",
        day_change_delta_class(change_pct),
        ytd_display,
        ytd_display,
        ytd_delta_class(ytd_change),
        format_percent(realized_vol_6m),
        format_market_cap_billions(market_cap),
        chart_title,
        figure,
        table_data,
        table_columns,
    )
