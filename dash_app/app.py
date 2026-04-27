from pathlib import Path

from dash import Dash, Input, Output, State, callback, dcc, html, page_container, page_registry


APP_DIR = Path(__file__).parent

app = Dash(
    __name__,
    use_pages=True,
    pages_folder=str(APP_DIR / "pages"),
    suppress_callback_exceptions=True,
    title="Stock Dashboard",
)

server = app.server


def build_navigation() -> html.Div:
    pages = sorted(page_registry.values(), key=lambda page: page.get("order", 999))
    links = [
        dcc.Link(page["name"], href=page["path"], className="nav-link")
        for page in pages
    ]
    return html.Nav(links, className="side-nav")


def build_sidebar() -> html.Aside:
    return html.Aside(
        [
            html.Div(
                [
                    html.Button(
                        "←",
                        id="sidebar-toggle",
                        className="sidebar-toggle",
                        n_clicks=0,
                        title="Collapse sidebar",
                    ),
                ],
                className="sidebar-toolbar",
            ),
            build_navigation(),
        ],
        className="app-sidebar",
    )


app.layout = html.Div(
    [
        dcc.Store(id="sidebar-collapsed", storage_type="session", data=False),
        html.Div(
            [
                build_sidebar(),
                html.Main(page_container, className="page-shell"),
            ],
            id="app-shell",
            className="app-shell",
        ),
    ],
    className="app-root",
)


@callback(
    Output("sidebar-collapsed", "data"),
    Input("sidebar-toggle", "n_clicks"),
    State("sidebar-collapsed", "data"),
    prevent_initial_call=True,
)
def toggle_sidebar(n_clicks: int, is_collapsed: bool) -> bool:
    if not n_clicks:
        return is_collapsed
    return not bool(is_collapsed)


@callback(
    Output("app-shell", "className"),
    Output("sidebar-toggle", "children"),
    Output("sidebar-toggle", "title"),
    Input("sidebar-collapsed", "data"),
)
def sync_sidebar_state(is_collapsed: bool) -> tuple[str, str, str]:
    if is_collapsed:
        return "app-shell is-collapsed", "→", "Expand sidebar"
    return "app-shell", "←", "Collapse sidebar"


if __name__ == "__main__":
    app.run(debug=False)
