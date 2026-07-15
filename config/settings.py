"""
settings.py
===========
Handles persisted, user-configurable application settings such as
theme choice, monitoring interval, notification thresholds, database
path, export folder, and auto-startup behavior.

Settings are persisted as JSON on disk so they survive application
restarts. A single `Settings` dataclass instance is the source of
truth; `SettingsManager` is responsible for loading/saving it.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from config.constants import (
    BASE_DIR,
    DATABASE_PATH,
    EXPORTS_DIR,
    MonitorInterval,
)

logger = logging.getLogger(__name__)

SETTINGS_FILE: Path = BASE_DIR / "config" / "user_settings.json"


@dataclass
class NotificationThresholds:
    """Thresholds beyond which the notifier should alert the user."""

    max_ping_ms: float = 100.0
    max_packet_loss_pct: float = 5.0
    min_download_mbps: float = 10.0
    min_upload_mbps: float = 5.0
    notify_on_poor_internet: bool = True
    notify_on_disconnect: bool = True
    notify_on_restore: bool = True


@dataclass
class Settings:
    """All user-configurable application settings."""

    theme: str = "dark"
    monitoring_interval_seconds: int = MonitorInterval.FIVE_MINUTES.value
    database_path: str = str(DATABASE_PATH)
    export_folder: str = str(EXPORTS_DIR)
    auto_startup: bool = False
    notifications_enabled: bool = True
    notification_thresholds: NotificationThresholds = field(
        default_factory=NotificationThresholds
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Settings":
        thresholds_data = data.get("notification_thresholds", {})
        thresholds = NotificationThresholds(**thresholds_data)
        return Settings(
            theme=data.get("theme", "dark"),
            monitoring_interval_seconds=data.get(
                "monitoring_interval_seconds",
                MonitorInterval.FIVE_MINUTES.value,
            ),
            database_path=data.get("database_path", str(DATABASE_PATH)),
            export_folder=data.get("export_folder", str(EXPORTS_DIR)),
            auto_startup=data.get("auto_startup", False),
            notifications_enabled=data.get("notifications_enabled", True),
            notification_thresholds=thresholds,
        )


class SettingsManager:
    """Loads, saves, and provides access to the application Settings."""

    def __init__(self, settings_path: Path = SETTINGS_FILE) -> None:
        self._path = settings_path
        self._settings: Settings = self._load()

    def _load(self) -> Settings:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                logger.info("Loaded settings from %s", self._path)
                return Settings.from_dict(data)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(
                    "Failed to load settings (%s); using defaults", exc
                )
        return Settings()

    def save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(self._settings.to_dict(), fh, indent=2)
            logger.info("Settings saved to %s", self._path)
        except OSError as exc:
            logger.error("Failed to save settings: %s", exc)

    @property
    def settings(self) -> Settings:
        return self._settings

    def update(self, **kwargs: Any) -> None:
        """Update one or more settings fields and persist immediately."""
        for key, value in kwargs.items():
            if hasattr(self._settings, key):
                setattr(self._settings, key, value)
            else:
                logger.warning("Unknown settings field: %s", key)
        self.save()

    def update_thresholds(self, **kwargs: Any) -> None:
        """Update notification threshold fields and persist immediately."""
        thresholds = self._settings.notification_thresholds
        for key, value in kwargs.items():
            if hasattr(thresholds, key):
                setattr(thresholds, key, value)
            else:
                logger.warning("Unknown threshold field: %s", key)
        self.save()

    def reset_to_defaults(self) -> None:
        self._settings = Settings()
        self.save()


# Module-level singleton for convenient shared access across the app.
settings_manager = SettingsManager()
