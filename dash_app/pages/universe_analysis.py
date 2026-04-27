import dash

from dash_app.page_shell import placeholder_page


dash.register_page(__name__, path="/universe-analysis", name="Universe Analysis", order=1)

layout = placeholder_page(
    "Universe Analysis",
    "This page will reuse the shared universe and status loaders from dashboard_core while we port the summary tables to Dash.",
)
