"""
charts.py
=========
Builds all Plotly figures used by the dashboards: animated gauges for
download/upload/ping, historical line charts for every tracked metric,
and the internet health score gauge. Every figure honors the shared
theme template from `dashboard/theme.py` and supports zoom, hover, and
legends out of the box (Plotly defaults), plus PNG export via the
built-in modebar.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from dashboard.theme import get_plotly_template, status_color


def _apply_template(fig: go.Figure, theme_name: str) -> go.Figure:
    fig.update_layout(get_plotly_template(theme_name)["layout"])
    return fig


def build_gauge(
    value: float,
    title: str,
    max_value: float,
    unit: str,
    status: str,
    theme_name: str = "dark",
) -> go.Figure:
    """Build an animated circular gauge chart for a single metric."""
    color = status_color(status, theme_name)

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": f" {unit}", "font": {"size": 36}},
            title={"text": title, "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, max_value], "tickwidth": 1},
                "bar": {"color": color, "thickness": 0.3},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, max_value * 0.3], "color": "rgba(239,68,68,0.15)"},
                    {"range": [max_value * 0.3, max_value * 0.7], "color": "rgba(245,158,11,0.15)"},
                    {"range": [max_value * 0.7, max_value], "color": "rgba(34,197,94,0.15)"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=20))
    return _apply_template(fig, theme_name)


def build_health_score_gauge(score: float, theme_name: str = "dark") -> go.Figure:
    """Build the 0-100 Internet Health Score gauge."""
    if score >= 85:
        status = "Excellent"
    elif score >= 65:
        status = "Good"
    elif score >= 40:
        status = "Average"
    else:
        status = "Poor"

    return build_gauge(
        value=score,
        title="Internet Health Score",
        max_value=100,
        unit="/100",
        status=status,
        theme_name=theme_name,
    )


def build_history_line_chart(
    df: pd.DataFrame,
    y_column: str,
    title: str,
    y_label: str,
    theme_name: str = "dark",
    color: str | None = None,
) -> go.Figure:
    """Build an interactive time-series line chart for a metric's history."""
    fig = go.Figure()

    if not df.empty and y_column in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["datetime"],
                y=df[y_column],
                mode="lines+markers",
                name=title,
                line=dict(width=2, color=color),
                fill="tozeroy",
                fillcolor="rgba(99,102,241,0.08)",
                marker=dict(size=4),
                hovertemplate=f"%{{x}}<br>{y_label}: %{{y}}<extra></extra>",
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title=y_label,
        height=340,
        hovermode="x unified",
        showlegend=False,
    )
    return _apply_template(fig, theme_name)


def build_multi_metric_chart(
    df: pd.DataFrame, theme_name: str = "dark"
) -> go.Figure:
    """
    Build a combined chart overlaying download and upload speed history
    on a shared time axis, useful for the main dashboard overview.
    """
    fig = go.Figure()

    if not df.empty:
        fig.add_trace(
            go.Scatter(
                x=df["datetime"], y=df["download_speed"],
                mode="lines", name="Download (Mbps)", line=dict(width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df["datetime"], y=df["upload_speed"],
                mode="lines", name="Upload (Mbps)", line=dict(width=2, dash="dot"),
            )
        )

    fig.update_layout(
        title="Download vs Upload History",
        xaxis_title="Time",
        yaxis_title="Speed (Mbps)",
        height=380,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return _apply_template(fig, theme_name)


def build_score_distribution_chart(df: pd.DataFrame, theme_name: str = "dark") -> go.Figure:
    """Build a histogram of internet health scores for distribution analysis."""
    fig = go.Figure()
    if not df.empty and "internet_score" in df.columns:
        fig.add_trace(
            go.Histogram(
                x=df["internet_score"],
                nbinsx=20,
                marker=dict(line=dict(width=1)),
            )
        )
    fig.update_layout(
        title="Health Score Distribution",
        xaxis_title="Score",
        yaxis_title="Frequency",
        height=320,
    )
    return _apply_template(fig, theme_name)
