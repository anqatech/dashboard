import dash_ag_grid as dag
from dash import html

from dash_app.grid_theme import GRID_THEME


def build_sector_layout(
    page_key: str,
    title: str,
    description: str,
) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Div(title, className="table-page-title"),
                    html.Div(description, className="table-page-description"),
                ],
                className="table-page-header",
            ),
            html.Div(id=f"{page_key}-load-trigger", style={"display": "none"}),
            html.Div(id=f"{page_key}-error", className="inline-error"),
            html.Div(
                [
                    build_summary_card("Sectors", f"{page_key}-sector-count"),
                    build_summary_card("Stocks", f"{page_key}-stock-count"),
                    build_summary_card("Total market cap", f"{page_key}-total-market-cap"),
                ],
                className="summary-grid",
            ),
            dag.AgGrid(
                id=f"{page_key}-grid",
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
                columnSize="responsiveSizeToFit",
                dashGridOptions={
                    "theme": GRID_THEME,
                    "pagination": True,
                    "paginationPageSize": 25,
                    "paginationPageSizeSelector": False,
                    "domLayout": "autoHeight",
                    "animateRows": False,
                },
                style={"width": "100%", "minHeight": "520px"},
            ),
        ],
        className="content-stack",
    )


def build_summary_card(label: str, value_id: str) -> html.Div:
    return html.Div(
        [
            html.Div(label, className="summary-label"),
            html.Div(id=value_id, className="summary-value"),
        ],
        className="summary-card",
    )
