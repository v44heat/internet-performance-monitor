"""
desktop/styles.py
==================
Thin wrapper exposing the shared QSS stylesheet (from config.theme) to
the PySide6 desktop application, plus a few desktop-only style
constants (card shadow, animation durations).
"""

from __future__ import annotations

from config.theme import Theme, get_theme, build_qss_stylesheet

ANIMATION_DURATION_MS = 220
CARD_BLUR_RADIUS = 24
CARD_SHADOW_OFFSET = 4


def get_app_stylesheet(theme_name: str = "dark") -> str:
    """Return the full QSS stylesheet string for the given theme name."""
    theme = get_theme(theme_name)
    return build_qss_stylesheet(theme)


def get_theme_object(theme_name: str = "dark") -> Theme:
    return get_theme(theme_name)
