"""
cards.py
========
Reusable "glass card" metric card renderers producing HTML snippets
for embedding in Streamlit (`st.markdown(unsafe_allow_html=True)`)
and, with minor adaptation, Dash `html.Div` children.
"""

from __future__ import annotations

from dashboard.theme import status_color


def render_metric_card_html(
    label: str,
    value: str,
    status: str | None = None,
    theme_name: str = "dark",
    icon: str = "",
) -> str:
    """Render a single glassmorphism metric card as an HTML string."""
    status_html = ""
    if status:
        color = status_color(status, theme_name)
        status_html = (
            f'<span class="status-pill" '
            f'style="background:{color}22;color:{color};border:1px solid {color}55;">'
            f"{status}</span>"
        )

    icon_html = f'<span style="margin-right:8px;">{icon}</span>' if icon else ""

    return f"""
    <div class="glass-card">
        <div class="metric-label">{icon_html}{label}</div>
        <div class="metric-value">{value}</div>
        {status_html}
    </div>
    """


def render_stars_card_html(label: str, stars: str, score_text: str) -> str:
    """Render a card showing a star rating alongside a numeric score."""
    return f"""
    <div class="glass-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="font-size:1.6rem;color:#FBBF24;">{stars}</div>
        <div class="metric-label" style="margin-top:6px;">{score_text}</div>
    </div>
    """


def render_info_card_html(title: str, rows: dict[str, str]) -> str:
    """Render a small key/value info card (e.g. ISP information)."""
    rows_html = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:4px 0;">'
        f'<span class="metric-label" style="text-transform:none;">{k}</span>'
        f'<span style="font-weight:600;">{v}</span></div>'
        for k, v in rows.items()
    )
    return f"""
    <div class="glass-card">
        <div class="metric-label" style="margin-bottom:8px;">{title}</div>
        {rows_html}
    </div>
    """


def render_status_bar_html(connection_status: str, theme_name: str = "dark") -> str:
    """Render the always-visible connection/monitoring status bar."""
    color = {
        "Connected": "#22C55E",
        "Disconnected": "#EF4444",
        "Testing": "#F59E0B",
        "Monitoring": "#3B82F6",
    }.get(connection_status, "#94A3B8")

    return f"""
    <div style="display:flex;align-items:center;gap:8px;padding:8px 16px;
                border-radius:999px;background:{color}18;border:1px solid {color}55;
                width:fit-content;">
        <span style="width:8px;height:8px;border-radius:50%;background:{color};
                     display:inline-block;"></span>
        <span style="color:{color};font-weight:600;font-size:0.85rem;">{connection_status}</span>
    </div>
    """
