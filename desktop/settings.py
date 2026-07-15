"""
desktop/settings.py
===================
Settings page for the PySide6 desktop application. Lets the user
configure theme, monitoring interval, notification thresholds,
database path, export folder, and auto-startup — all persisted via
`config.settings.settings_manager`.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal

from config.constants import MonitorInterval
from config.settings import SettingsManager, settings_manager
from utils.validators import is_writable_directory


class SettingsPage(QWidget):
    """Full settings form; emits `settings_saved` after a successful save."""

    settings_saved = Signal()

    def __init__(self, manager: SettingsManager | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._manager = manager or settings_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        header = QLabel("⚙️ Settings")
        header.setStyleSheet("font-size:22px; font-weight:700;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(14)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light", "auto"])
        form.addRow("Theme", self.theme_combo)

        self.interval_combo = QComboBox()
        for interval in MonitorInterval:
            self.interval_combo.addItem(interval.label, interval.value)
        form.addRow("Monitoring Interval", self.interval_combo)

        self.db_path_input = QLineEdit()
        db_browse_btn = QPushButton("Browse…")
        db_browse_btn.clicked.connect(self._browse_database_path)
        db_row = QHBoxLayout()
        db_row.addWidget(self.db_path_input)
        db_row.addWidget(db_browse_btn)
        form.addRow("Database Path", db_row)

        self.export_path_input = QLineEdit()
        export_browse_btn = QPushButton("Browse…")
        export_browse_btn.clicked.connect(self._browse_export_folder)
        export_row = QHBoxLayout()
        export_row.addWidget(self.export_path_input)
        export_row.addWidget(export_browse_btn)
        form.addRow("Export Folder", export_row)

        self.auto_startup_check = QCheckBox("Launch automatically on system startup")
        form.addRow("", self.auto_startup_check)

        self.notifications_check = QCheckBox("Enable desktop notifications")
        form.addRow("", self.notifications_check)

        layout.addLayout(form)

        threshold_label = QLabel("Notification Thresholds")
        threshold_label.setStyleSheet("font-size:15px; font-weight:600; margin-top:8px;")
        layout.addWidget(threshold_label)

        threshold_form = QFormLayout()
        self.max_ping_slider = self._make_slider(20, 300)
        self.max_loss_slider = self._make_slider(0, 20)
        self.min_download_slider = self._make_slider(1, 200)
        threshold_form.addRow("Max Ping (ms)", self.max_ping_slider)
        threshold_form.addRow("Max Packet Loss (%)", self.max_loss_slider)
        threshold_form.addRow("Min Download (Mbps)", self.min_download_slider)
        layout.addLayout(threshold_form)

        save_btn = QPushButton("💾 Save Settings")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        layout.addStretch()

        self._load_current_settings()

    @staticmethod
    def _make_slider(minimum: int, maximum: int) -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        return slider

    def _browse_database_path(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Select Database File", filter="SQLite DB (*.db)")
        if path:
            self.db_path_input.setText(path)

    def _browse_export_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if path:
            self.export_path_input.setText(path)

    def _load_current_settings(self) -> None:
        s = self._manager.settings
        self.theme_combo.setCurrentText(s.theme)
        idx = self.interval_combo.findData(s.monitoring_interval_seconds)
        if idx >= 0:
            self.interval_combo.setCurrentIndex(idx)
        self.db_path_input.setText(s.database_path)
        self.export_path_input.setText(s.export_folder)
        self.auto_startup_check.setChecked(s.auto_startup)
        self.notifications_check.setChecked(s.notifications_enabled)

        t = s.notification_thresholds
        self.max_ping_slider.setValue(int(t.max_ping_ms))
        self.max_loss_slider.setValue(int(t.max_packet_loss_pct))
        self.min_download_slider.setValue(int(t.min_download_mbps))

    def _save(self) -> None:
        export_folder = self.export_path_input.text().strip()
        if export_folder and not is_writable_directory(export_folder):
            QMessageBox.warning(self, "Invalid Path", "The export folder is not writable.")
            return

        self._manager.update(
            theme=self.theme_combo.currentText(),
            monitoring_interval_seconds=self.interval_combo.currentData(),
            database_path=self.db_path_input.text().strip(),
            export_folder=export_folder,
            auto_startup=self.auto_startup_check.isChecked(),
            notifications_enabled=self.notifications_check.isChecked(),
        )
        self._manager.update_thresholds(
            max_ping_ms=float(self.max_ping_slider.value()),
            max_packet_loss_pct=float(self.max_loss_slider.value()),
            min_download_mbps=float(self.min_download_slider.value()),
        )
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved.")
        self.settings_saved.emit()
