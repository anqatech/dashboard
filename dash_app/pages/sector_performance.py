import dash

from dash_app.page_shell import placeholder_page


dash.register_page(__name__, path="/sector-performance", name="Sector Performance", order=5)

layout = placeholder_page(
    "Sector Performance",
    "This page will present the market-cap-weighted sector return table from dashboard_core in Dash.",
)
