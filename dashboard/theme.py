"""
dashboard/theme.py
===================
Dashboard-specific theming helpers built on top of `config.theme`.
Provides ready-to-inject CSS for Streamlit (`st.markdown`) and a
Plotly template dict shared by both the Streamlit and Dash dashboards
so every chart matches the app's dark/light aesthetic.
"""

from __future__ import annotations

from config.theme import Theme, build_css_variables, get_theme


def get_streamlit_css(theme_name: str = "dark") -> str:
    """
    Build a full <style> block for injection into Streamlit via
    `st.markdown(..., unsafe_allow_html=True)`. Implements the
    glassmorphism card look, gradient background, and responsive
    metric grid used throughout the dashboard.
    """
    theme = get_theme(theme_name)
    p = theme.palette
    variables = build_css_variables(theme)

    return f"""
    <style>
    {variables}

    html, body, [class*="css"] {{
        font-family: var(--font-family);
    }}

    .stApp {{
        background: radial-gradient(circle at top left, {p.surface_alt} 0%, {p.background} 55%);
        color: var(--text-primary);
    }}

    section[data-testid="stSidebar"] {{
        background-color: {p.surface};
        border-right: 1px solid var(--border);
    }}

    .glass-card {{
        background: {p.glass_overlay};
        backdrop-filter: blur(14px);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 22px 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
        margin-bottom: 16px;
    }}

    .metric-label {{
        color: var(--text-secondary);
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-top: 4px;
    }}

    .status-pill {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: var(--radius-md);
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 8px;
    }}

    .app-title {{
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, var(--primary), var(--accent));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    </style>
    """


def get_plotly_template(theme_name: str = "dark") -> dict:
    """Build a Plotly layout template dict matching the app theme."""
    theme = get_theme(theme_name)
    p = theme.palette
    return {
        "layout": {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": p.text_primary, "family": theme.typography.font_family},
            "colorway": [p.primary, p.accent, p.success, p.warning, p.danger, p.info],
            "xaxis": {"gridcolor": p.border, "zerolinecolor": p.border},
            "yaxis": {"gridcolor": p.border, "zerolinecolor": p.border},
            "legend": {"bgcolor": "rgba(0,0,0,0)"},
            "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        }
    }


def status_color(status: str, theme_name: str = "dark") -> str:
    """Return the theme-appropriate color hex for a Status label."""
    theme = get_theme(theme_name)
    p = theme.palette
    mapping = {
        "Excellent": p.success,
        "Good": "#84CC16",
        "Average": p.warning,
        "Poor": p.danger,
    }
    return mapping.get(status, p.text_secondary)
