import dash

from dash_app.page_shell import placeholder_page


dash.register_page(__name__, path="/stock-screener", name="Stock Screener", order=2)

layout = placeholder_page(
    "Stock Screener",
    "This will be one of the first reusable table-driven pages to port because its logic already lives in dashboard_core.",
)
