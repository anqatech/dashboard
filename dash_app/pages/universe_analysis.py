import dash
import dash_ag_grid as dag
from dash import Input, Output, State, callback, dcc, html

from dashboard_core.analytics import (
    build_sector_summary,
    build_sub_industry_summary,
    build_universe_stock_table,
)
from dashboard_core.data import filter_universe
from dashboard_core.formatters import format_market_cap_billions_whole
from dash_app.grid_theme import GRID_THEME
from dash_app.market_data import (
    build_select_options,
    get_initial_market_filters,
    get_status_frame,
    get_universe,
)
from dash_app.screener_page import build_column_defs, dataframe_to_row_data
from dash_app.sector_page import build_summary_card


PAGE_KEY = "universe-analysis"


dash.register_page(__name__, path="/universe-analysis", name="Universe Analysis", order=1)


def build_table(table_id: str, min_height: str = "300px") -> dag.AgGrid:
    return dag.AgGrid(
        id=table_id,
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
        style={"width": "100%", "minHeight": min_height},
    )


def layout() -> html.Div:
    universe = get_universe()
    initial_sector, initial_sub_industry = get_initial_market_filters()
    sector_options = build_select_options(sorted(universe["gics_sector"].unique().tolist()))
    sub_industry_options = build_select_options(
        sorted(filter_universe(universe, initial_sector)["gics_sub_industry"].unique().tolist())
    )

    return html.Div(
        [
            html.Div(id=f"{PAGE_KEY}-load-trigger", style={"display": "none"}),
            html.Div(id=f"{PAGE_KEY}-error", className="inline-error"),
            html.Div(
                [
                    build_summary_card("Tickers", f"{PAGE_KEY}-ticker-count"),
                    build_summary_card("GICS sectors", f"{PAGE_KEY}-sector-count"),
                    build_summary_card("Sub-industries", f"{PAGE_KEY}-subindustry-count"),
                    build_summary_card("Total market cap", f"{PAGE_KEY}-total-market-cap"),
                ],
                className="summary-grid",
            ),
            html.Div(
                [
                    html.H2("Sector summary", className="table-section-title"),
                    build_table(f"{PAGE_KEY}-sector-grid", min_height="260px"),
                ],
                className="table-section",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Sector", className="control-label"),
                            dcc.Dropdown(
                                id=f"{PAGE_KEY}-sector",
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
                                id=f"{PAGE_KEY}-sub-industry",
                                options=sub_industry_options,
                                value=initial_sub_industry,
                                clearable=False,
                                persistence=True,
                                persistence_type="session",
                                className="dash-dropdown",
                            ),
                        ],
                        className="control-card",
                    ),
                ],
                className="table-filters-grid table-section",
            ),
            html.Div(
                [
                    html.H2(id=f"{PAGE_KEY}-subindustry-title", className="table-section-title"),
                    build_table(f"{PAGE_KEY}-subindustry-grid", min_height="220px"),
                ],
                className="table-section",
            ),
            html.Div(
                [
                    html.H2(id=f"{PAGE_KEY}-stocks-title", className="table-section-title"),
                    build_table(f"{PAGE_KEY}-stocks-grid", min_height="360px"),
                ],
                className="table-section",
            ),
        ],
        className="content-stack",
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
    options = sorted(sector_universe["gics_sub_industry"].unique().tolist())
    next_value = current_sub_industry if current_sub_industry in options else options[0]
    return build_select_options(options), next_value


@callback(
    Output(f"{PAGE_KEY}-error", "children"),
    Output(f"{PAGE_KEY}-ticker-count", "children"),
    Output(f"{PAGE_KEY}-sector-count", "children"),
    Output(f"{PAGE_KEY}-subindustry-count", "children"),
    Output(f"{PAGE_KEY}-total-market-cap", "children"),
    Output(f"{PAGE_KEY}-sector-grid", "rowData"),
    Output(f"{PAGE_KEY}-sector-grid", "columnDefs"),
    Output(f"{PAGE_KEY}-subindustry-title", "children"),
    Output(f"{PAGE_KEY}-subindustry-grid", "rowData"),
    Output(f"{PAGE_KEY}-subindustry-grid", "columnDefs"),
    Output(f"{PAGE_KEY}-stocks-title", "children"),
    Output(f"{PAGE_KEY}-stocks-grid", "rowData"),
    Output(f"{PAGE_KEY}-stocks-grid", "columnDefs"),
    Input(f"{PAGE_KEY}-load-trigger", "children"),
    Input(f"{PAGE_KEY}-sector", "value"),
    Input(f"{PAGE_KEY}-sub-industry", "value"),
)
def update_universe_page(_, selected_sector: str, selected_sub_industry: str):
    try:
        universe = get_universe()
        status_frame = get_status_frame()
    except FileNotFoundError as exc:
        return f"Missing input file: {exc.filename}", "", "", "", "", [], [], "", [], [], "", [], []
    except ValueError as exc:
        return str(exc), "", "", "", "", [], [], "", [], [], "", [], []
    except Exception as exc:
        return f"Failed to load universe analysis data: {exc}", "", "", "", "", [], [], "", [], [], "", [], []

    available_sectors = sorted(universe["gics_sector"].unique().tolist())
    normalized_sector = selected_sector if selected_sector in available_sectors else available_sectors[0]
    sector_universe = filter_universe(universe, normalized_sector)

    sub_industry_summary = build_sub_industry_summary(sector_universe)
    available_sub_industries = sub_industry_summary["gics_sub_industry"].tolist()
    normalized_sub_industry = (
        selected_sub_industry if selected_sub_industry in available_sub_industries else available_sub_industries[0]
    )

    universe_with_status = universe.merge(status_frame, on="ticker", how="left")
    total_market_cap = universe_with_status["market_cap"].sum()
    sector_summary = build_sector_summary(universe_with_status)
    filtered_stocks = build_universe_stock_table(
        filter_universe(universe, normalized_sector, normalized_sub_industry),
        status_frame,
    )

    sector_row_data = dataframe_to_row_data(
        sector_summary,
        [
            "gics_sector",
            "ticker_count",
            "sub_industry_count",
            "total_market_cap_display",
            "market_cap_weight_display",
        ],
    )
    sector_column_defs = build_column_defs(
        [
            {"field": "gics_sector", "headerName": "GICS sector", "minWidth": 220, "pinned": "left"},
            {"field": "ticker_count", "headerName": "Stocks", "minWidth": 100},
            {"field": "sub_industry_count", "headerName": "Sub-industries", "minWidth": 130},
            {"field": "total_market_cap_display", "headerName": "Total market cap", "minWidth": 150},
            {"field": "market_cap_weight_display", "headerName": "Ratio", "minWidth": 100},
        ]
    )

    subindustry_row_data = dataframe_to_row_data(sub_industry_summary, ["gics_sub_industry", "ticker_count"])
    subindustry_column_defs = build_column_defs(
        [
            {"field": "gics_sub_industry", "headerName": "Sub-industry", "minWidth": 260, "pinned": "left"},
            {"field": "ticker_count", "headerName": "Stocks", "minWidth": 100},
        ]
    )

    stocks_row_data = dataframe_to_row_data(
        filtered_stocks,
        ["ticker", "company_name", "market_cap_display", "start", "end"],
    )
    stocks_column_defs = build_column_defs(
        [
            {"field": "ticker", "headerName": "Ticker", "minWidth": 110, "pinned": "left"},
            {"field": "company_name", "headerName": "Company", "minWidth": 240},
            {"field": "market_cap_display", "headerName": "Market cap", "minWidth": 140},
            {"field": "start", "headerName": "Dataset start", "minWidth": 130},
            {"field": "end", "headerName": "Dataset end", "minWidth": 130},
        ]
    )

    return (
        "",
        f"{len(universe):,}",
        f"{universe['gics_sector'].nunique():,}",
        f"{universe['gics_sub_industry'].nunique():,}",
        format_market_cap_billions_whole(total_market_cap),
        sector_row_data,
        sector_column_defs,
        f"Sub-industries in {normalized_sector}",
        subindustry_row_data,
        subindustry_column_defs,
        f"Stocks in {normalized_sector} / {normalized_sub_industry}",
        stocks_row_data,
        stocks_column_defs,
    )
