import dash
from dash import Input, Output, callback

from dashboard_core.formatters import format_market_cap_billions
from dash_app.market_data import get_sector_sharpe_table
from dash_app.screener_page import build_column_defs, dataframe_to_row_data
from dash_app.sector_page import build_sector_layout


PAGE_KEY = "sector-sharpe"


dash.register_page(__name__, path="/sector-sharpe", name="Sector Sharpe", order=7)

layout = build_sector_layout(
    PAGE_KEY,
    "Sector Sharpe",
    "Risk-adjusted sector view using annualized Sharpe ratios, market-cap-weighted returns, realized volatility, and a 0% risk-free-rate assumption.",
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
def load_sector_sharpe(_):
    try:
        sector_sharpe = get_sector_sharpe_table()
    except FileNotFoundError as exc:
        return f"Missing input file: {exc.filename}", "", "", "", [], []
    except ValueError as exc:
        return str(exc), "", "", "", [], []
    except Exception as exc:
        return f"Failed to load sector Sharpe data: {exc}", "", "", "", [], []

    row_data = dataframe_to_row_data(
        sector_sharpe,
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
        ],
    )
    column_defs = build_column_defs(
        [
            {"field": "gics_sector", "headerName": "GICS sector", "minWidth": 220, "pinned": "left"},
            {"field": "stock_count", "headerName": "Stocks", "minWidth": 100},
            {"field": "total_market_cap_display", "headerName": "Total market cap", "minWidth": 150},
            {"field": "weight_display", "headerName": "Weight", "minWidth": 110},
            {"field": "performance_3m_display", "headerName": "3M", "minWidth": 95},
            {"field": "performance_1y_display", "headerName": "1Y", "minWidth": 95},
            {"field": "vol_3m_display", "headerName": "vol_3m", "minWidth": 110},
            {"field": "sharpe_3m_display", "headerName": "ann_sharpe_3m", "minWidth": 140},
            {"field": "sharpe_1y_display", "headerName": "ann_sharpe_1y", "minWidth": 140},
        ]
    )
    return (
        "",
        f"{sector_sharpe['gics_sector'].nunique():,}",
        f"{int(sector_sharpe['stock_count'].sum()):,}",
        format_market_cap_billions(sector_sharpe["total_market_cap"].sum()),
        row_data,
        column_defs,
    )
