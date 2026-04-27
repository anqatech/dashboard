import dash

from dash_app.page_shell import placeholder_page


dash.register_page(__name__, path="/sector-sharpe", name="Sector Sharpe", order=7)

layout = placeholder_page(
    "Sector Sharpe",
    "This page will reuse the shared annualized sector Sharpe calculation already extracted from Streamlit.",
)
