import dash
from dash import Input, Output, State, callback
import pandas as pd

from dashboard_core.analytics import build_stock_volatility_table
from dashboard_core.data import filter_universe
from dash_app.market_data import build_select_options, get_status_frame, get_universe, get_volatility_frame
from dash_app.screener_page import build_column_defs, build_screener_layout, dataframe_to_row_data


PAGE_KEY = "volatility"


dash.register_page(__name__, path="/volatility", name="Volatility", order=3)

layout = build_screener_layout(
    PAGE_KEY,
    "Volatility",
    "Compare recent realized volatility across the filtered universe using one consistent screener layout.",
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
    filtered_stocks = build_stock_volatility_table(
        filter_universe(get_universe(), selected_sector, selected_sub_industry),
        get_status_frame(),
        get_volatility_frame(),
    )
    filtered_stocks["latest_close"] = filtered_stocks["latest_close"].map(
        lambda value: "" if pd.isna(value) else f"${float(value):,.2f}"
    )
    row_data = dataframe_to_row_data(
        filtered_stocks,
        [
            "ticker",
            "company_name",
            "market_cap_display",
            "latest_close",
            "vol_1m_display",
            "vol_3m_display",
            "vol_6m_display",
            "vol_1y_display",
        ],
    )
    column_defs = build_column_defs(
        [
            {"field": "ticker", "headerName": "Ticker", "pinned": "left", "minWidth": 110},
            {"field": "company_name", "headerName": "Company", "minWidth": 220},
            {"field": "market_cap_display", "headerName": "Market cap", "minWidth": 140},
            {"field": "latest_close", "headerName": "Price", "minWidth": 110},
            {"field": "vol_1m_display", "headerName": "vol_1m", "minWidth": 100},
            {"field": "vol_3m_display", "headerName": "vol_3m", "minWidth": 100},
            {"field": "vol_6m_display", "headerName": "vol_6m", "minWidth": 100},
            {"field": "vol_1y_display", "headerName": "vol_1y", "minWidth": 100},
        ]
    )
    return row_data, column_defs
