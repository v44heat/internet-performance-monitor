"""
desktop/main_window.py
======================
Main application window for the Internet Performance Monitor Pro
PySide6 desktop client. Composes the sidebar, gauges, metric cards,
history table, and settings form into a single stacked-page window,
and runs network tests on a background QThread so the UI never
freezes (per project requirements).

Run with:
    python desktop/main_window.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QObject, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config.constants import APP_NAME, Status
from config.settings import settings_manager
from core.database import database
from core.scheduler import FullTestResult, monitor_scheduler, test_runner
from desktop.gauges import GaugeWidget
from desktop.history import HistoryPage
from desktop.settings import SettingsPage
from desktop.sidebar import Sidebar
from desktop.styles import get_app_stylesheet
from desktop.widgets import Card, MetricCard
from utils.formatter import format_percentage, format_ping, format_score, score_to_stars
from utils.logger import get_logger

logger = get_logger(__name__)

STATUS_COLOR_MAP = {
    Status.EXCELLENT.value: "#22C55E",
    Status.GOOD.value: "#84CC16",
    Status.AVERAGE.value: "#F59E0B",
    Status.POOR.value: "#EF4444",
}


class TestWorker(QObject):
    """
    Runs a full network test cycle on a dedicated QThread so the Qt
    event loop / UI remains responsive during the (potentially
    multi-second) speed test.
    """

    finished = Signal(object)  # emits FullTestResult

    def run(self) -> None:
        result = test_runner.run_full_test()
        self.finished.emit(result)


class DashboardPage(QWidget):
    """Main live dashboard page: gauges + metric cards + run-test button."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        top_row = QHBoxLayout()
        header = QLabel("📊 Live Dashboard")
        header.setStyleSheet("font-size:22px; font-weight:700;")
        self.run_button = QPushButton("🚀 Run Speed Test Now")
        self.run_button.setFixedWidth(220)
        top_row.addWidget(header)
        top_row.addStretch()
        top_row.addWidget(self.run_button)
        layout.addLayout(top_row)

        gauge_row = QHBoxLayout()
        self.download_gauge = GaugeWidget("Download", "Mbps", max_value=300)
        self.upload_gauge = GaugeWidget("Upload", "Mbps", max_value=100)
        self.health_gauge = GaugeWidget("Health Score", "/100", max_value=100)
        for gauge in (self.download_gauge, self.upload_gauge, self.health_gauge):
            card = Card()
            card_layout = QVBoxLayout(card)
            card_layout.addWidget(gauge)
            gauge_row.addWidget(card)
        layout.addLayout(gauge_row)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)
        self.ping_card = MetricCard("Ping")
        self.jitter_card = MetricCard("Jitter")
        self.loss_card = MetricCard("Packet Loss")
        self.isp_card = MetricCard("ISP / Server")
        cards_grid.addWidget(self.ping_card, 0, 0)
        cards_grid.addWidget(self.jitter_card, 0, 1)
        cards_grid.addWidget(self.loss_card, 0, 2)
        cards_grid.addWidget(self.isp_card, 0, 3)
        layout.addLayout(cards_grid)

        layout.addStretch()

    def display_result(self, result) -> None:
        self.download_gauge.set_value(result.download_speed, Status.EXCELLENT.value)
        self.upload_gauge.set_value(result.upload_speed, Status.EXCELLENT.value)
        self.health_gauge.set_value(result.internet_score, Status.EXCELLENT.value)

        self.ping_card.set_value(format_ping(result.ping))
        self.jitter_card.set_value(f"{result.jitter:.1f} ms")
        self.loss_card.set_value(format_percentage(result.packet_loss))
        self.isp_card.set_value(f"{result.isp or '—'}")


class MainWindow(QMainWindow):
    """Top-level application window composing sidebar + stacked pages."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 780)
        self.setStyleSheet(get_app_stylesheet(settings_manager.settings.theme))

        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._switch_page)
        root_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.history_page = HistoryPage()
        self.settings_page = SettingsPage()

        self._pages = {
            "dashboard": self.dashboard_page,
            "history": self.history_page,
            "analytics": self.history_page,  # reuses history/table view for now
            "export": self.settings_page,
            "settings": self.settings_page,
        }
        for page in {self.dashboard_page, self.history_page, self.settings_page}:
            self.stack.addWidget(page)

        root_layout.addWidget(self.stack, stretch=1)
        self.setCentralWidget(central)

        self.dashboard_page.run_button.clicked.connect(self.run_test_now)
        self._thread: QThread | None = None
        self._worker: TestWorker | None = None

        self._load_latest_result()

        # Periodically refresh the dashboard with the latest DB result,
        # covering updates produced by the background monitoring scheduler.
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_latest_result)
        self._refresh_timer.start(10_000)

    def _switch_page(self, key: str) -> None:
        page = self._pages.get(key, self.dashboard_page)
        if key == "history":
            self.history_page.refresh()
        self.stack.setCurrentWidget(page)

    def _load_latest_result(self) -> None:
        latest = database.get_latest_result()
        if latest is not None:
            self.dashboard_page.display_result(latest)

    def run_test_now(self) -> None:
        """Kick off a full test cycle on a background thread."""
        self.sidebar.set_connection_status("Testing")
        self.dashboard_page.run_button.setEnabled(False)
        self.dashboard_page.run_button.setText("Testing…")

        self._thread = QThread()
        self._worker = TestWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_test_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _on_test_finished(self, result: FullTestResult) -> None:
        self.dashboard_page.run_button.setEnabled(True)
        self.dashboard_page.run_button.setText("🚀 Run Speed Test Now")

        if result.success:
            self.sidebar.set_connection_status("Connected")
            self.dashboard_page.display_result(result.test_result)
        else:
            self.sidebar.set_connection_status("Disconnected")
            logger.warning("Test failed: %s", result.error_message)

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        monitor_scheduler.shutdown()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
