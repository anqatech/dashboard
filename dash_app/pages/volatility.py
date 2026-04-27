import dash

from dash_app.page_shell import placeholder_page


dash.register_page(__name__, path="/volatility", name="Volatility", order=3)

layout = placeholder_page(
    "Volatility",
    "This page will share the same sector and sub-industry filtering pattern as the Dash stock screener.",
)
