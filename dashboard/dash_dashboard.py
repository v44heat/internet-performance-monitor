"""
dash_dashboard.py
=================
Alternative dashboard built with Dash + dash-bootstrap-components.
Offers a responsive layout with a collapsible sidebar, live-updating
graphs (via dcc.Interval), metric cards, filters, search, and a
light/dark theme switcher — a second, independently deployable web
surface for Internet Performance Monitor Pro.

Run with:
    python dashboard/dash_dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dash
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback_context, dcc, html

from config.constants import APP_NAME, APP_VERSION, DateRangePreset
from core.database import database
from core.scheduler import test_runner
from core.statistics import results_to_dataframe
from dashboard.charts import (
    build_gauge,
    build_health_score_gauge,
    build_history_line_chart,
    build_multi_metric_chart,
)
from dashboard.theme import get_plotly_template
from utils.formatter import format_percentage, format_ping, format_speed
from utils.helpers import resolve_date_range

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    title=APP_NAME,
)
server = app.server  # exposed for WSGI deployment


# --------------------------------------------------------------------------
# Layout building blocks
# --------------------------------------------------------------------------
def _sidebar() -> html.Div:
    nav_items = [
        ("Dashboard", "fa-gauge-high", "/"),
        ("History", "fa-clock-rotate-left", "/history"),
        ("Analytics", "fa-chart-line", "/analytics"),
    ]
    links = [
        dbc.NavLink(
            [html.I(className=f"fa-solid {icon} me-2"), label],
            href=href,
            active="exact",
            className="text-light py-2",
        )
        for label, icon, href in nav_items
    ]
    return html.Div(
        [
            html.H4(f"🌐 {APP_NAME}", className="text-light px-3 pt-3"),
            html.Small(f"v{APP_VERSION}", className="text-secondary px-3"),
            html.Hr(className="text-secondary"),
            dbc.Nav(links, vertical=True, pills=True, className="px-2"),
            html.Hr(className="text-secondary"),
            dbc.Switch(id="theme-switch", label="Light Mode", value=False, className="px-3 text-light"),
            dbc.Button(
                "Run Test Now",
                id="run-test-btn",
                color="primary",
                className="mx-3 mt-3",
            ),
            html.Div(id="test-status", className="px-3 mt-2 text-secondary small"),
        ],
        style={
            "width": "230px",
            "position": "fixed",
            "height": "100vh",
            "backgroundColor": "#131826",
            "borderRight": "1px solid #232B3E",
        },
    )


def _metric_card(label: str, value_id: str, icon: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div([html.I(className=f"fa-solid {icon} me-2"), label], className="text-secondary small text-uppercase"),
                html.H3(id=value_id, className="mt-2 mb-0"),
            ]
        ),
        className="shadow-sm",
        style={"backgroundColor": "#131826", "border": "1px solid #232B3E", "borderRadius": "14px"},
    )


def _content() -> html.Div:
    return html.Div(
        [
            dcc.Location(id="url"),
            dcc.Interval(id="live-interval", interval=15_000, n_intervals=0),
            html.Div(id="page-content", className="p-4"),
        ],
        style={"marginLeft": "230px"},
    )


app.layout = html.Div([_sidebar(), _content()], style={"backgroundColor": "#0B0F19", "minHeight": "100vh"})


# --------------------------------------------------------------------------
# Page layouts
# --------------------------------------------------------------------------
def _dashboard_page() -> html.Div:
    return html.Div(
        [
            html.H2("Live Dashboard", className="text-light mb-3"),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="download-gauge", config={"displaylogo": False}), md=4),
                    dbc.Col(dcc.Graph(id="upload-gauge", config={"displaylogo": False}), md=4),
                    dbc.Col(dcc.Graph(id="health-gauge", config={"displaylogo": False}), md=4),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(_metric_card("Ping", "ping-value", "fa-tower-broadcast"), md=4),
                    dbc.Col(_metric_card("Packet Loss", "loss-value", "fa-chart-simple"), md=4),
                    dbc.Col(_metric_card("ISP", "isp-value", "fa-network-wired"), md=4),
                ],
                className="mt-3 g-3",
            ),
            dbc.Row(dbc.Col(dcc.Graph(id="trend-chart", config={"displaylogo": False})), className="mt-4"),
        ]
    )


def _history_page() -> html.Div:
    return html.Div(
        [
            html.H2("Test History", className="text-light mb-3"),
            dbc.Row(
                [
                    dbc.Col(dbc.Input(id="search-isp", placeholder="Search by ISP...", type="text"), md=4),
                    dbc.Col(dbc.Input(id="search-server", placeholder="Search by server...", type="text"), md=4),
                    dbc.Col(dbc.Button("Search", id="search-btn", color="primary"), md=2),
                ],
                className="mb-3 g-2",
            ),
            html.Div(id="history-table"),
        ]
    )


def _analytics_page() -> html.Div:
    return html.Div(
        [
            html.H2("Analytics", className="text-light mb-3"),
            dbc.Row(
                dbc.Col(
                    dcc.Dropdown(
                        id="range-filter",
                        options=[
                            {"label": "Last Hour", "value": DateRangePreset.LAST_HOUR.value},
                            {"label": "Today", "value": DateRangePreset.TODAY.value},
                            {"label": "Last 7 Days", "value": DateRangePreset.LAST_7_DAYS.value},
                            {"label": "Last 30 Days", "value": DateRangePreset.LAST_30_DAYS.value},
                        ],
                        value=DateRangePreset.LAST_7_DAYS.value,
                        clearable=False,
                        style={"color": "#000"},
                    ),
                    md=4,
                ),
                className="mb-3",
            ),
            dcc.Graph(id="ping-history-chart", config={"displaylogo": False}),
            dcc.Graph(id="loss-history-chart", config={"displaylogo": False}),
        ]
    )


# --------------------------------------------------------------------------
# Callbacks
# --------------------------------------------------------------------------
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname: str) -> html.Div:
    if pathname == "/history":
        return _history_page()
    if pathname == "/analytics":
        return _analytics_page()
    return _dashboard_page()


@app.callback(
    Output("download-gauge", "figure"),
    Output("upload-gauge", "figure"),
    Output("health-gauge", "figure"),
    Output("ping-value", "children"),
    Output("loss-value", "children"),
    Output("isp-value", "children"),
    Output("trend-chart", "figure"),
    Input("live-interval", "n_intervals"),
)
def update_live_dashboard(_n: int):
    latest = database.get_latest_result()
    theme_name = "dark"

    if latest is None:
        empty = build_gauge(0, "No Data", 100, "", "Poor", theme_name)
        return empty, empty, empty, "—", "—", "—", build_multi_metric_chart(pd.DataFrame(), theme_name)

    dl_gauge = build_gauge(latest.download_speed, "Download", 300, "Mbps", "Excellent", theme_name)
    ul_gauge = build_gauge(latest.upload_speed, "Upload", 100, "Mbps", "Excellent", theme_name)
    health_gauge = build_health_score_gauge(latest.internet_score, theme_name)

    df = results_to_dataframe(database.get_all_results(limit=50))
    trend = build_multi_metric_chart(df, theme_name)

    return (
        dl_gauge,
        ul_gauge,
        health_gauge,
        format_ping(latest.ping),
        format_percentage(latest.packet_loss),
        latest.isp or "Unknown",
        trend,
    )


@app.callback(
    Output("test-status", "children"),
    Input("run-test-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_test_now(n_clicks: int | None):
    if not n_clicks:
        return ""
    result = test_runner.run_full_test()
    if result.success:
        return f"✅ Test complete — score {result.test_result.internet_score:.0f}/100"
    return f"⚠️ {result.error_message}"


@app.callback(
    Output("history-table", "children"),
    Input("search-btn", "n_clicks"),
    State("search-isp", "value"),
    State("search-server", "value"),
    prevent_initial_call=False,
)
def update_history_table(_n_clicks, isp_value, server_value):
    results = database.search_results(isp=isp_value or None, server=server_value or None)
    df = results_to_dataframe(results)

    if df.empty:
        return dbc.Alert("No results found.", color="secondary")

    return dbc.Table.from_dataframe(
        df.tail(100), striped=True, bordered=False, hover=True, dark=True, responsive=True
    )


@app.callback(
    Output("ping-history-chart", "figure"),
    Output("loss-history-chart", "figure"),
    Input("range-filter", "value"),
)
def update_analytics_charts(preset_value: str):
    preset = DateRangePreset(preset_value)
    start, end = resolve_date_range(preset)
    results = database.get_results_in_range(start, end)
    df = results_to_dataframe(results)

    ping_chart = build_history_line_chart(df, "ping", "Ping History", "ms", "dark")
    loss_chart = build_history_line_chart(df, "packet_loss", "Packet Loss History", "%", "dark")
    return ping_chart, loss_chart


if __name__ == "__main__":
    app.run(debug=True, port=8050)
