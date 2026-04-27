from pathlib import Path

from dash import Dash, dcc, html, page_container, page_registry


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
    return html.Nav(links, className="top-nav")


app.layout = html.Div(
    [
        html.Header(
            [
                html.Div("Stock Dashboard", className="app-title"),
                build_navigation(),
            ],
            className="app-header",
        ),
        html.Main(page_container, className="page-shell"),
    ],
    className="app-root",
)


if __name__ == "__main__":
    app.run(debug=False)
