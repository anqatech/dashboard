from dash import html


def placeholder_page(title: str, description: str) -> html.Div:
    return html.Div(
        [
            html.H1(title, className="page-title"),
            html.P(description, className="page-description"),
            html.Div(
                [
                    html.H2("Migration status", className="section-title"),
                    html.P(
                        "This page is the Dash scaffold. The next step is to port the matching Streamlit page onto dashboard_core.",
                        className="status-copy",
                    ),
                ],
                className="status-card",
            ),
        ],
        className="content-stack",
    )
