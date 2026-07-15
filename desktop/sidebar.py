"""
desktop/sidebar.py
==================
Left-hand navigation sidebar for the PySide6 desktop application,
featuring the app logo/title, a set of checkable navigation buttons
(Dashboard, History, Analytics, Export, Settings), and the live
connection status pill.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from config.constants import APP_NAME, APP_VERSION
from desktop.widgets import StatusPill

NAV_ITEMS = [
    ("dashboard", "🌐  Dashboard"),
    ("history", "🕓  History"),
    ("analytics", "📈  Analytics"),
    ("export", "⬇️  Export"),
    ("settings", "⚙️  Settings"),
]


class Sidebar(QFrame):
    """Navigation sidebar; emits `page_changed(str)` when a nav item is clicked."""

    page_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(230)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(6)

        title = QLabel(f"🌐 {APP_NAME}")
        title.setWordWrap(True)
        title.setStyleSheet("font-size:16px; font-weight:700;")
        version = QLabel(f"v{APP_VERSION}")
        version.setObjectName("secondary")
        version.setStyleSheet("font-size:11px;")

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addSpacing(20)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setFixedHeight(42)
            btn.clicked.connect(lambda _checked, k=key: self.page_changed.emit(k))
            self._button_group.addButton(btn)
            layout.addWidget(btn)
            if key == "dashboard":
                btn.setChecked(True)

        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.status_pill = StatusPill()
        layout.addWidget(self.status_pill)

    def set_connection_status(self, status: str) -> None:
        self.status_pill.set_status(status)
