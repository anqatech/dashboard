import dash_ag_grid as dag
from dash import dcc, html
import pandas as pd

from dash_app.grid_theme import GRID_THEME
from dash_app.market_data import build_select_options, get_initial_market_filters, get_universe


def build_screener_layout(
    page_key: str,
    title: str,
    description: str,
) -> html.Div:
    universe = get_universe()
    initial_sector, initial_sub_industry = get_initial_market_filters()
    sector_options = build_select_options(sorted(universe["gics_sector"].unique().tolist()))
    sub_industry_options = build_select_options(
        ["All"] + sorted(universe.loc[universe["gics_sector"] == initial_sector, "gics_sub_industry"].unique().tolist())
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(title, className="table-page-title"),
                    html.Div(description, className="table-page-description"),
                ],
                className="table-page-header",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Sector", className="control-label"),
                            dcc.Dropdown(
                                id=f"{page_key}-sector",
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
                                id=f"{page_key}-sub-industry",
                                options=sub_industry_options,
                                value="All",
                                clearable=False,
                                persistence=True,
                                persistence_type="session",
                                className="dash-dropdown",
                            ),
                        ],
                        className="control-card",
                    ),
                ],
                className="table-filters-grid",
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


def build_column_defs(specs: list[dict[str, str | int | bool]]) -> list[dict[str, str | int | bool]]:
    return [dict(spec) for spec in specs]


def dataframe_to_row_data(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    display_frame = frame.loc[:, columns].copy()
    for column in display_frame.columns:
        if pd.api.types.is_datetime64_any_dtype(display_frame[column]):
            display_frame[column] = display_frame[column].dt.strftime("%Y-%m-%d")
    return display_frame.to_dict("records")
