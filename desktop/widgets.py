"""
desktop/widgets.py
==================
Reusable PySide6 widgets shared across the desktop application's
pages: glass-style metric cards, a status pill, and a soft drop-shadow
helper — implementing the "rounded corners / glassmorphism / smooth
animation" visual language requested for the desktop app.
"""

from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from desktop.styles import ANIMATION_DURATION_MS, CARD_BLUR_RADIUS


def apply_card_shadow(widget: QWidget) -> None:
    """Attach a soft drop shadow to a widget to reinforce card depth."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(CARD_BLUR_RADIUS)
    effect.setXOffset(0)
    effect.setYOffset(4)
    effect.setColor(QColor(0, 0, 0, 120))
    widget.setGraphicsEffect(effect)


class Card(QFrame):
    """A rounded, drop-shadowed container frame used throughout the app."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        apply_card_shadow(self)


class MetricCard(Card):
    """
    A card displaying a single labeled metric value with an optional
    color-coded status pill beneath it (e.g. "Download: 150.2 Mbps —
    Excellent").
    """

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        self.label_widget = QLabel(label.upper())
        self.label_widget.setObjectName("secondary")
        self.label_widget.setStyleSheet("font-size:11px; letter-spacing:1px; font-weight:600;")

        self.value_widget = QLabel("—")
        self.value_widget.setObjectName("metricValue")

        self.status_widget = QLabel("")
        self.status_widget.setStyleSheet("font-size:11px; font-weight:600; padding:2px 0;")

        layout.addWidget(self.label_widget)
        layout.addWidget(self.value_widget)
        layout.addWidget(self.status_widget)

    def set_value(self, value: str, status: str = "", status_color: str = "#94A3B8") -> None:
        self.value_widget.setText(value)
        self.status_widget.setText(status)
        self.status_widget.setStyleSheet(
            f"font-size:11px; font-weight:600; padding:2px 0; color:{status_color};"
        )


class StatusPill(QWidget):
    """A small rounded pill widget indicating connection/monitoring status."""

    STATUS_COLORS = {
        "Connected": "#22C55E",
        "Disconnected": "#EF4444",
        "Testing": "#F59E0B",
        "Monitoring": "#3B82F6",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        self.dot = QLabel("●")
        self.text = QLabel("Connected")
        self.text.setStyleSheet("font-weight:600; font-size:12px;")

        layout.addWidget(self.dot)
        layout.addWidget(self.text)
        self.set_status("Connected")

    def set_status(self, status: str) -> None:
        color = self.STATUS_COLORS.get(status, "#94A3B8")
        self.dot.setStyleSheet(f"color:{color}; font-size:10px;")
        self.text.setText(status)
        self.text.setStyleSheet(f"font-weight:600; font-size:12px; color:{color};")
        self.setStyleSheet(
            f"background-color:{color}22; border:1px solid {color}55; border-radius:14px;"
        )


def fade_in(widget: QWidget) -> QPropertyAnimation:
    """Return a configured fade-in QPropertyAnimation for a widget's opacity."""
    from PySide6.QtWidgets import QGraphicsOpacityEffect

    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(ANIMATION_DURATION_MS)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start()
    return animation
