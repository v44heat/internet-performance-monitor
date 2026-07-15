"""
theme.py
========
Design-system definitions shared across the Streamlit dashboard, Dash
dashboard, and PySide6 desktop application. Centralizing palette,
typography, and spacing tokens keeps every surface visually consistent
and makes global re-theming a one-file change.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColorPalette:
    """A single palette of colors for either dark or light mode."""

    background: str
    surface: str
    surface_alt: str
    primary: str
    primary_alt: str
    accent: str
    text_primary: str
    text_secondary: str
    border: str
    success: str
    warning: str
    danger: str
    info: str
    glass_overlay: str


DARK_PALETTE = ColorPalette(
    background="#0B0F19",
    surface="#131826",
    surface_alt="#1B2233",
    primary="#6366F1",
    primary_alt="#818CF8",
    accent="#22D3EE",
    text_primary="#F8FAFC",
    text_secondary="#94A3B8",
    border="#232B3E",
    success="#22C55E",
    warning="#F59E0B",
    danger="#EF4444",
    info="#3B82F6",
    glass_overlay="rgba(255, 255, 255, 0.04)",
)

LIGHT_PALETTE = ColorPalette(
    background="#F4F6FB",
    surface="#FFFFFF",
    surface_alt="#EEF1F8",
    primary="#4F46E5",
    primary_alt="#6366F1",
    accent="#0EA5E9",
    text_primary="#0F172A",
    text_secondary="#475569",
    border="#E2E8F0",
    success="#16A34A",
    warning="#D97706",
    danger="#DC2626",
    info="#2563EB",
    glass_overlay="rgba(15, 23, 42, 0.04)",
)


@dataclass(frozen=True)
class Typography:
    font_family: str = (
        "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    )
    font_family_mono: str = "'JetBrains Mono', 'Consolas', monospace"
    size_xs: str = "0.75rem"
    size_sm: str = "0.875rem"
    size_base: str = "1rem"
    size_lg: str = "1.25rem"
    size_xl: str = "1.5rem"
    size_2xl: str = "2rem"
    size_3xl: str = "2.75rem"
    weight_regular: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700


@dataclass(frozen=True)
class Spacing:
    xs: str = "4px"
    sm: str = "8px"
    md: str = "16px"
    lg: str = "24px"
    xl: str = "32px"
    xxl: str = "48px"
    radius_sm: str = "8px"
    radius_md: str = "14px"
    radius_lg: str = "20px"
    radius_pill: str = "999px"


@dataclass(frozen=True)
class Theme:
    """A fully composed theme (palette + typography + spacing)."""

    name: str
    palette: ColorPalette
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)


DARK_THEME = Theme(name="dark", palette=DARK_PALETTE)
LIGHT_THEME = Theme(name="light", palette=LIGHT_PALETTE)

THEMES: dict[str, Theme] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


def get_theme(name: str) -> Theme:
    """Return the Theme object for the given name, defaulting to dark."""
    return THEMES.get(name, DARK_THEME)


def build_css_variables(theme: Theme) -> str:
    """
    Build a block of CSS custom properties (variables) from a Theme.
    Consumed by the Streamlit and Dash dashboards for consistent styling.
    """
    p = theme.palette
    t = theme.typography
    s = theme.spacing
    return f"""
    :root {{
        --bg: {p.background};
        --surface: {p.surface};
        --surface-alt: {p.surface_alt};
        --primary: {p.primary};
        --primary-alt: {p.primary_alt};
        --accent: {p.accent};
        --text-primary: {p.text_primary};
        --text-secondary: {p.text_secondary};
        --border: {p.border};
        --success: {p.success};
        --warning: {p.warning};
        --danger: {p.danger};
        --info: {p.info};
        --glass-overlay: {p.glass_overlay};
        --font-family: {t.font_family};
        --font-mono: {t.font_family_mono};
        --radius-sm: {s.radius_sm};
        --radius-md: {s.radius_md};
        --radius-lg: {s.radius_lg};
    }}
    """


def build_qss_stylesheet(theme: Theme) -> str:
    """
    Build a Qt Style Sheet (QSS) string from a Theme for use in the
    PySide6 desktop application.
    """
    p = theme.palette
    s = theme.spacing
    return f"""
    QWidget {{
        background-color: {p.background};
        color: {p.text_primary};
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }}
    QFrame#card {{
        background-color: {p.surface};
        border: 1px solid {p.border};
        border-radius: {s.radius_lg};
    }}
    QFrame#sidebar {{
        background-color: {p.surface};
        border-right: 1px solid {p.border};
    }}
    QPushButton {{
        background-color: {p.primary};
        color: white;
        border: none;
        border-radius: {s.radius_md};
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {p.primary_alt};
    }}
    QPushButton:pressed {{
        background-color: {p.primary};
    }}
    QPushButton#navButton {{
        background-color: transparent;
        color: {p.text_secondary};
        text-align: left;
        padding: 10px 14px;
        border-radius: {s.radius_md};
        font-weight: 500;
    }}
    QPushButton#navButton:checked {{
        background-color: {p.surface_alt};
        color: {p.text_primary};
    }}
    QLabel {{
        color: {p.text_primary};
    }}
    QLabel#secondary {{
        color: {p.text_secondary};
    }}
    QLabel#metricValue {{
        font-size: 28px;
        font-weight: 700;
    }}
    QScrollBar:vertical {{
        background: {p.background};
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {p.border};
        border-radius: 4px;
    }}
    QTableWidget {{
        background-color: {p.surface};
        gridline-color: {p.border};
        border: 1px solid {p.border};
        border-radius: {s.radius_md};
    }}
    QHeaderView::section {{
        background-color: {p.surface_alt};
        color: {p.text_secondary};
        border: none;
        padding: 6px;
        font-weight: 600;
    }}
    """
