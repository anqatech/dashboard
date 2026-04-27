import dash
from dash import Input, Output, callback

from dashboard_core.formatters import format_market_cap_billions
from dash_app.market_data import get_sector_volatility_table
from dash_app.screener_page import build_column_defs, dataframe_to_row_data
from dash_app.sector_page import build_sector_layout


PAGE_KEY = "sector-volatility"


dash.register_page(__name__, path="/sector-volatility", name="Sector Volatility", order=6)

layout = build_sector_layout(
    PAGE_KEY,
    "Sector Volatility",
    "Market-cap-weighted realized volatility by sector based on the local stock volatility frame.",
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
def load_sector_volatility(_):
    try:
        sector_volatility = get_sector_volatility_table()
    except FileNotFoundError as exc:
        return f"Missing input file: {exc.filename}", "", "", "", [], []
    except ValueError as exc:
        return str(exc), "", "", "", [], []
    except Exception as exc:
        return f"Failed to load sector volatility data: {exc}", "", "", "", [], []

    row_data = dataframe_to_row_data(
        sector_volatility,
        [
            "gics_sector",
            "stock_count",
            "total_market_cap_display",
            "weight_display",
            "vol_1m_display",
            "vol_3m_display",
            "vol_6m_display",
            "vol_1y_display",
        ],
    )
    column_defs = build_column_defs(
        [
            {"field": "gics_sector", "headerName": "GICS sector", "minWidth": 220, "pinned": "left"},
            {"field": "stock_count", "headerName": "Stocks", "minWidth": 100},
            {"field": "total_market_cap_display", "headerName": "Total market cap", "minWidth": 150},
            {"field": "weight_display", "headerName": "Weight", "minWidth": 110},
            {"field": "vol_1m_display", "headerName": "vol_1m", "minWidth": 110},
            {"field": "vol_3m_display", "headerName": "vol_3m", "minWidth": 110},
            {"field": "vol_6m_display", "headerName": "vol_6m", "minWidth": 110},
            {"field": "vol_1y_display", "headerName": "vol_1y", "minWidth": 110},
        ]
    )
    return (
        "",
        f"{sector_volatility['gics_sector'].nunique():,}",
        f"{int(sector_volatility['stock_count'].sum()):,}",
        format_market_cap_billions(sector_volatility["total_market_cap"].sum()),
        row_data,
        column_defs,
    )
