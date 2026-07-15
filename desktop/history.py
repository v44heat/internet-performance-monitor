"""
desktop/history.py
==================
History page for the PySide6 desktop application: a searchable,
filterable table of all stored test results, backed directly by
`core.database.Database.search_results`.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.database import Database, database
from utils.formatter import format_datetime, format_percentage, format_ping, format_speed

COLUMN_HEADERS = [
    "Date/Time", "Download", "Upload", "Ping", "Jitter", "Packet Loss", "ISP", "Server", "Score",
]


class HistoryPage(QWidget):
    """Displays a searchable/filterable table of historical test results."""

    def __init__(self, db: Database | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = db or database

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QLabel("🕓 Test History")
        header.setStyleSheet("font-size:22px; font-weight:700;")
        layout.addWidget(header)

        filter_row = QHBoxLayout()
        self.isp_input = QLineEdit()
        self.isp_input.setPlaceholderText("Search ISP...")
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("Search server...")
        self.range_combo = QComboBox()
        self.range_combo.addItems(["All Time", "Today", "This Week", "This Month"])
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.refresh)

        filter_row.addWidget(self.isp_input)
        filter_row.addWidget(self.server_input)
        filter_row.addWidget(self.range_combo)
        filter_row.addWidget(search_btn)
        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(COLUMN_HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        """Re-query the database using the current filter inputs and repopulate the table."""
        isp = self.isp_input.text().strip() or None
        server = self.server_input.text().strip() or None

        results = self._db.search_results(isp=isp, server=server)
        self.table.setRowCount(len(results))

        for row_idx, result in enumerate(results):
            values = [
                format_datetime(result.datetime_str),
                format_speed(result.download_speed),
                format_speed(result.upload_speed),
                format_ping(result.ping),
                f"{result.jitter:.1f} ms",
                format_percentage(result.packet_loss),
                result.isp or "—",
                result.server or "—",
                f"{result.internet_score:.0f}/100",
            ]
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)
