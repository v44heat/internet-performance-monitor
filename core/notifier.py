"""
notifier.py
===========
Sends desktop notifications via `plyer` when internet quality crosses
user-configured thresholds (poor internet, high ping, high packet
loss, disconnection, connection restored). Debounces repeat
notifications so the user isn't spammed on every single test cycle.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from plyer import notification

from config.constants import APP_NAME, NotificationType
from config.settings import NotificationThresholds
from core.database import Database, database
from utils.logger import get_logger

logger = get_logger(__name__)

_DEBOUNCE_SECONDS = 300  # Don't repeat the same notification within 5 minutes


@dataclass
class NotificationEvent:
    notification_type: NotificationType
    title: str
    message: str


class Notifier:
    """Evaluates test results against thresholds and fires notifications."""

    def __init__(self, db: Database | None = None) -> None:
        self._db = db or database
        self._last_sent: dict[NotificationType, float] = {}
        self._was_disconnected = False

    def _debounced(self, notification_type: NotificationType) -> bool:
        last = self._last_sent.get(notification_type, 0.0)
        return (time.time() - last) < _DEBOUNCE_SECONDS

    def _send(self, event: NotificationEvent) -> None:
        if self._debounced(event.notification_type):
            logger.debug("Notification debounced: %s", event.notification_type)
            return
        try:
            notification.notify(
                title=event.title,
                message=event.message,
                app_name=APP_NAME,
                timeout=10,
            )
            self._last_sent[event.notification_type] = time.time()
            self._db.log_event("INFO", "notification", event.message)
            logger.info("Notification sent: %s - %s", event.title, event.message)
        except Exception as exc:  # pragma: no cover - platform dependent
            logger.error("Failed to send notification: %s", exc)

    def notify_disconnected(self) -> None:
        self._was_disconnected = True
        self._send(
            NotificationEvent(
                NotificationType.DISCONNECTED,
                "Internet Disconnected",
                "Your internet connection appears to be down.",
            )
        )

    def notify_restored(self) -> None:
        if self._was_disconnected:
            self._send(
                NotificationEvent(
                    NotificationType.CONNECTION_RESTORED,
                    "Connection Restored",
                    "Your internet connection has been restored.",
                )
            )
            self._was_disconnected = False

    def evaluate_result(
        self,
        download_mbps: float,
        upload_mbps: float,
        ping_ms: float,
        packet_loss_pct: float,
        thresholds: NotificationThresholds,
    ) -> None:
        """
        Compare a completed test result against configured thresholds
        and fire the appropriate notifications.
        """
        if not thresholds.notify_on_poor_internet and not thresholds.notify_on_disconnect:
            return

        if thresholds.notify_on_poor_internet:
            if download_mbps < thresholds.min_download_mbps or upload_mbps < thresholds.min_upload_mbps:
                self._send(
                    NotificationEvent(
                        NotificationType.POOR_INTERNET,
                        "Poor Internet Quality",
                        f"Download: {download_mbps:.1f} Mbps, "
                        f"Upload: {upload_mbps:.1f} Mbps — below your thresholds.",
                    )
                )

            if ping_ms > thresholds.max_ping_ms:
                self._send(
                    NotificationEvent(
                        NotificationType.HIGH_PING,
                        "High Ping Detected",
                        f"Current ping is {ping_ms:.0f} ms, "
                        f"above your {thresholds.max_ping_ms:.0f} ms threshold.",
                    )
                )

            if packet_loss_pct > thresholds.max_packet_loss_pct:
                self._send(
                    NotificationEvent(
                        NotificationType.HIGH_PACKET_LOSS,
                        "High Packet Loss",
                        f"Packet loss is {packet_loss_pct:.1f}%, "
                        f"above your {thresholds.max_packet_loss_pct:.1f}% threshold.",
                    )
                )

        if thresholds.notify_on_restore:
            self.notify_restored()


# Module-level singleton for convenient shared access.
notifier = Notifier()
