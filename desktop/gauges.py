"""
desktop/gauges.py
=================
Custom-painted circular gauge widget (via QPainter) used for the
Download / Upload / Health Score displays in the PySide6 desktop app.
Supports smooth animated needle transitions between values using
QPropertyAnimation over a Qt Property.
"""

from __future__ import annotations

import math

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, Qt
from PySide6.QtGui import QColor, QConicalGradient, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from config.constants import Status


class GaugeWidget(QWidget):
    """
    An animated circular gauge showing a numeric value against a
    max_value, with a color determined by a Status classification.
    Values are animated smoothly between updates for a polished feel.
    """

    def __init__(
        self,
        title: str,
        unit: str,
        max_value: float = 100.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._unit = unit
        self._max_value = max_value
        self._value = 0.0
        self._display_value = 0.0
        self._status = Status.AVERAGE.value
        self.setMinimumSize(200, 220)

        self._animation = QPropertyAnimation(self, b"displayValue")
        self._animation.setDuration(600)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    # -- Qt Property machinery for animating the displayed value --------
    def _get_display_value(self) -> float:
        return self._display_value

    def _set_display_value(self, value: float) -> None:
        self._display_value = value
        self.update()

    displayValue = Property(float, _get_display_value, _set_display_value)

    # -- Public API -------------------------------------------------------
    def set_value(self, value: float, status: str) -> None:
        """Animate the gauge to a new value with an updated status color."""
        self._status = status
        self._value = max(0.0, min(value, self._max_value))
        self._animation.stop()
        self._animation.setStartValue(self._display_value)
        self._animation.setEndValue(self._value)
        self._animation.start()

    def _status_color(self) -> QColor:
        mapping = {
            Status.EXCELLENT.value: QColor("#22C55E"),
            Status.GOOD.value: QColor("#84CC16"),
            Status.AVERAGE.value: QColor("#F59E0B"),
            Status.POOR.value: QColor("#EF4444"),
        }
        return mapping.get(self._status, QColor("#94A3B8"))

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height() - 40)
        rect = QRectF(
            (self.width() - side) / 2 + 10,
            10,
            side - 20,
            side - 20,
        )

        start_angle = 225 * 16  # Qt angles are in 1/16th degrees
        span_angle = -270 * 16

        # Background track
        track_pen = QPen(QColor("#232B3E"), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, start_angle, span_angle)

        # Value arc
        ratio = 0.0 if self._max_value == 0 else self._display_value / self._max_value
        ratio = max(0.0, min(ratio, 1.0))
        value_pen = QPen(self._status_color(), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(value_pen)
        painter.drawArc(rect, start_angle, int(span_angle * ratio))

        # Center value text
        painter.setPen(QColor("#F8FAFC"))
        value_font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        painter.setFont(value_font)
        value_text = f"{self._display_value:.1f}"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, value_text)

        # Unit text (slightly below center)
        unit_font = QFont("Segoe UI", 10)
        painter.setFont(unit_font)
        painter.setPen(QColor("#94A3B8"))
        unit_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.62, rect.width(), 24)
        painter.drawText(unit_rect, Qt.AlignmentFlag.AlignCenter, self._unit)

        # Title below the gauge
        title_font = QFont("Segoe UI", 11, QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor("#F8FAFC"))
        title_rect = QRectF(0, rect.y() + rect.height() + 6, self.width(), 24)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self._title)

        painter.end()
