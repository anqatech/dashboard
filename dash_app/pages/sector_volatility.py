import dash

from dash_app.page_shell import placeholder_page


dash.register_page(__name__, path="/sector-volatility", name="Sector Volatility", order=6)

layout = placeholder_page(
    "Sector Volatility",
    "This page will present the market-cap-weighted realized volatility table from dashboard_core in Dash.",
)
