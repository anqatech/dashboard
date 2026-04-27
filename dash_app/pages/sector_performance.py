import dash
from dash import Input, Output, callback

from dashboard_core.formatters import format_market_cap_billions
from dash_app.market_data import get_sector_performance_table
from dash_app.screener_page import build_column_defs, dataframe_to_row_data
from dash_app.sector_page import build_sector_layout


PAGE_KEY = "sector-performance"


dash.register_page(__name__, path="/sector-performance", name="Sector Performance", order=5)

layout = build_sector_layout(
    PAGE_KEY,
    "Sector Performance",
    "Market-cap-weighted sector performance based on the local stock return frame.",
)


@callback(
    Output(f"{PAGE_KEY}-error", "children"),
    Output(f"{PAGE_KEY}-sector-count", "children"),
    Output(f"{PAGE_KEY}-stock-count", "children"),
    Output(f"{PAGE_KEY}-total-market-cap", "children"),
    Output(f"{PAGE_KEY}-grid", "rowData"),
    Output(f"{PAGE_KEY}-grid", "columnDefs"),
    Input(f"{PAGE_KEY}-load-trigger", "children"),
)
def load_sector_performance(_):
    try:
        sector_performance = get_sector_performance_table()
    except FileNotFoundError as exc:
        return f"Missing input file: {exc.filename}", "", "", "", [], []
    except ValueError as exc:
        return str(exc), "", "", "", [], []
    except Exception as exc:
        return f"Failed to load sector performance data: {exc}", "", "", "", [], []

    row_data = dataframe_to_row_data(
        sector_performance,
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
        ],
    )
    column_defs = build_column_defs(
        [
            {"field": "gics_sector", "headerName": "GICS sector", "minWidth": 220, "pinned": "left"},
            {"field": "stock_count", "headerName": "Stocks", "minWidth": 100},
            {"field": "total_market_cap_display", "headerName": "Total market cap", "minWidth": 150},
            {"field": "weight_display", "headerName": "Weight", "minWidth": 110},
            {"field": "1D", "headerName": "1D", "minWidth": 95},
            {"field": "1W", "headerName": "1W", "minWidth": 95},
            {"field": "1M", "headerName": "1M", "minWidth": 95},
            {"field": "YTD", "headerName": "YTD", "minWidth": 95},
            {"field": "1Y", "headerName": "1Y", "minWidth": 95},
            {"field": "3Y", "headerName": "3Y", "minWidth": 95},
        ]
    )
    return (
        "",
        f"{sector_performance['gics_sector'].nunique():,}",
        f"{int(sector_performance['stock_count'].sum()):,}",
        format_market_cap_billions(sector_performance["total_market_cap"].sum()),
        row_data,
        column_defs,
    )
