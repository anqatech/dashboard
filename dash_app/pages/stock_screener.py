import dash
from dash import Input, Output, State, callback
import pandas as pd

from dashboard_core.analytics import build_stock_screener_table
from dashboard_core.data import filter_universe
from dash_app.market_data import (
    build_select_options,
    get_performance_frame,
    get_status_frame,
    get_universe,
)
from dash_app.screener_page import build_column_defs, build_screener_layout, dataframe_to_row_data


PAGE_KEY = "stock-screener"


dash.register_page(__name__, path="/stock-screener", name="Stock Screener", order=2)

layout = build_screener_layout(
    PAGE_KEY,
    "Stock Screener",
    "Browse the universe by sector and sub-industry, then scan returns, price, market cap, and dataset coverage.",
)


@callback(
    Output(f"{PAGE_KEY}-sub-industry", "options"),
    Output(f"{PAGE_KEY}-sub-industry", "value"),
    Input(f"{PAGE_KEY}-sector", "value"),
    State(f"{PAGE_KEY}-sub-industry", "value"),
)
def update_sub_industries(selected_sector: str, current_sub_industry: str | None):
    universe = get_universe()
    available_sectors = sorted(universe["gics_sector"].unique().tolist())
    normalized_sector = selected_sector if selected_sector in available_sectors else available_sectors[0]
    sector_universe = filter_universe(universe, normalized_sector)
    options = ["All"] + sorted(sector_universe["gics_sub_industry"].unique().tolist())
    next_value = current_sub_industry if current_sub_industry in options else "All"
    return build_select_options(options), next_value


@callback(
    Output(f"{PAGE_KEY}-grid", "rowData"),
    Output(f"{PAGE_KEY}-grid", "columnDefs"),
    Input(f"{PAGE_KEY}-sector", "value"),
    Input(f"{PAGE_KEY}-sub-industry", "value"),
)
def update_grid(selected_sector: str, selected_sub_industry: str):
    filtered_stocks = build_stock_screener_table(
        filter_universe(get_universe(), selected_sector, selected_sub_industry),
        get_status_frame(),
        get_performance_frame(),
    )
    filtered_stocks["latest_price_display"] = filtered_stocks["latest_price_display"].map(
        lambda value: "" if pd.isna(value) else f"${float(value):,.2f}"
    )
    row_data = dataframe_to_row_data(
        filtered_stocks,
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
        ],
    )
    column_defs = build_column_defs(
        [
            {"field": "ticker", "headerName": "Ticker", "pinned": "left", "minWidth": 110},
            {"field": "company_name", "headerName": "Company", "minWidth": 220},
            {"field": "market_cap_display", "headerName": "Market cap", "minWidth": 140},
            {"field": "latest_price_display", "headerName": "Price", "minWidth": 110},
            {"field": "1D", "headerName": "1D", "minWidth": 95},
            {"field": "1W", "headerName": "1W", "minWidth": 95},
            {"field": "1M", "headerName": "1M", "minWidth": 95},
            {"field": "YTD", "headerName": "YTD", "minWidth": 95},
            {"field": "1Y", "headerName": "1Y", "minWidth": 95},
            {"field": "3Y", "headerName": "3Y", "minWidth": 95},
            {"field": "start", "headerName": "Dataset start", "minWidth": 130},
            {"field": "end", "headerName": "Dataset end", "minWidth": 130},
        ]
    )
    return row_data, column_defs
