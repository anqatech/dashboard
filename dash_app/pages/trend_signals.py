import dash

from dash_app.page_shell import placeholder_page


dash.register_page(__name__, path="/trend-signals", name="Trend Signals", order=4)

layout = placeholder_page(
    "Trend Signals",
    "This page is scaffolded and ready to be wired onto the existing trend signal table builder in dashboard_core.",
)
