import dash
from dash import Input, Output, State, callback
import pandas as pd

from dashboard_core.analytics import build_trend_signals_table
from dashboard_core.data import filter_universe
from dash_app.market_data import build_select_options, get_trend_frame, get_universe
from dash_app.screener_page import build_column_defs, build_screener_layout, dataframe_to_row_data


PAGE_KEY = "trend-signals"


dash.register_page(__name__, path="/trend-signals", name="Trend Signals", order=4)

layout = build_screener_layout(
    PAGE_KEY,
    "Trend Signals",
    "Scan trend regime and momentum signals with the same filtering and table pattern as the other stock screeners.",
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
    filtered_stocks = build_trend_signals_table(
        filter_universe(get_universe(), selected_sector, selected_sub_industry),
        get_trend_frame(),
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
            "trend_signal_display",
            "trend_raw_display",
            "ma_confirm_display",
            "tsmom_63_display",
            "tsmom_126_display",
            "tsmom_252_display",
            "relmom_12_1_display",
        ],
    )
    column_defs = build_column_defs(
        [
            {"field": "ticker", "headerName": "Ticker", "pinned": "left", "minWidth": 110},
            {"field": "company_name", "headerName": "Company", "minWidth": 220},
            {"field": "market_cap_display", "headerName": "Market cap", "minWidth": 140},
            {"field": "latest_close", "headerName": "Price", "minWidth": 110},
            {"field": "trend_signal_display", "headerName": "trend_signal", "minWidth": 120},
            {"field": "trend_raw_display", "headerName": "trend_raw", "minWidth": 110},
            {"field": "ma_confirm_display", "headerName": "ma_confirm", "minWidth": 120},
            {"field": "tsmom_63_display", "headerName": "tsmom_63", "minWidth": 110},
            {"field": "tsmom_126_display", "headerName": "tsmom_126", "minWidth": 115},
            {"field": "tsmom_252_display", "headerName": "tsmom_252", "minWidth": 115},
            {"field": "relmom_12_1_display", "headerName": "relmom_12_1", "minWidth": 125},
        ]
    )
    return row_data, column_defs
