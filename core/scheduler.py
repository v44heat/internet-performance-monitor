"""
scheduler.py
============
Orchestrates full network test runs (download, upload, ping, jitter,
packet loss, ISP info, health score) and schedules them to run
automatically on a configurable interval using APScheduler's
background thread scheduler, so the UI thread is never blocked.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable, Optional

import speedtest
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import SettingsManager, settings_manager
from core.database import Database, TestResult, database
from core.download_test import DownloadTestError, run_download_test
from core.internet_health import calculate_internet_health
from core.jitter import JitterCalculationError, calculate_jitter
from core.network_info import get_network_info
from core.notifier import Notifier, notifier
from core.packet_loss import run_packet_loss_test
from core.ping_test import PingTestError, run_ping_test
from core.upload_test import UploadTestError, run_upload_test
from utils.helpers import is_connected
from utils.logger import get_logger

logger = get_logger(__name__)

JOB_ID = "internet_monitor_job"


@dataclass
class FullTestResult:
    """Aggregated outcome of a complete test cycle."""

    test_result: TestResult
    success: bool
    error_message: str = ""


class TestRunner:
    """Executes a single complete network performance test cycle."""

    def __init__(self, db: Database | None = None, notify: Notifier | None = None) -> None:
        self._db = db or database
        self._notifier = notify or notifier

    def run_full_test(self) -> FullTestResult:
        """
        Run download, upload, ping, jitter, packet loss, and ISP info
        tests, compute the health score, persist the result, and
        trigger any applicable notifications.
        """
        if not is_connected():
            logger.warning("No internet connection detected; aborting test")
            self._notifier.notify_disconnected()
            empty = TestResult(
                download_speed=0,
                upload_speed=0,
                ping=0,
                jitter=0,
                packet_loss=100,
                internet_score=0,
            )
            return FullTestResult(
                test_result=empty, success=False, error_message="No internet connection"
            )

        try:
            client = speedtest.Speedtest()
            client.get_best_server()

            download = run_download_test(shared_client=client)
            upload = run_upload_test(shared_client=client)
            ping_result = run_ping_test()
            jitter_result = calculate_jitter(ping_result.samples_ms)
            packet_loss_result = run_packet_loss_test()
            net_info = get_network_info(shared_client=client)

            health = calculate_internet_health(
                download_mbps=download.speed_mbps,
                upload_mbps=upload.speed_mbps,
                ping_ms=ping_result.average_ms,
                jitter_ms=jitter_result.average_ms,
                packet_loss_pct=packet_loss_result.loss_percentage,
            )

            result = TestResult(
                download_speed=download.speed_mbps,
                upload_speed=upload.speed_mbps,
                ping=ping_result.average_ms,
                jitter=jitter_result.average_ms,
                packet_loss=packet_loss_result.loss_percentage,
                isp=net_info.isp,
                server=net_info.server_name,
                city=net_info.city,
                country=net_info.country,
                ip_address=net_info.ip_address,
                network_type=net_info.network_type,
                internet_score=health.score,
            )

            self._db.insert_result(result)
            self._notifier.notify_restored()

            thresholds = settings_manager.settings.notification_thresholds
            if settings_manager.settings.notifications_enabled:
                self._notifier.evaluate_result(
                    download_mbps=download.speed_mbps,
                    upload_mbps=upload.speed_mbps,
                    ping_ms=ping_result.average_ms,
                    packet_loss_pct=packet_loss_result.loss_percentage,
                    thresholds=thresholds,
                )

            logger.info("Full test cycle completed successfully, score=%.1f", health.score)
            return FullTestResult(test_result=result, success=True)

        except (DownloadTestError, UploadTestError, PingTestError, JitterCalculationError) as exc:
            logger.error("Test cycle failed: %s", exc)
            self._db.log_event("ERROR", "monitoring", str(exc))
            empty = TestResult(
                download_speed=0, upload_speed=0, ping=0, jitter=0, packet_loss=100, internet_score=0
            )
            return FullTestResult(test_result=empty, success=False, error_message=str(exc))
        except Exception as exc:  # pragma: no cover - defensive catch-all
            logger.exception("Unexpected error during test cycle")
            self._db.log_event("ERROR", "monitoring", f"Unexpected error: {exc}")
            empty = TestResult(
                download_speed=0, upload_speed=0, ping=0, jitter=0, packet_loss=100, internet_score=0
            )
            return FullTestResult(test_result=empty, success=False, error_message=str(exc))


class MonitorScheduler:
    """
    Wraps APScheduler's BackgroundScheduler to run TestRunner cycles
    on a configurable interval without blocking the calling UI thread.
    """

    def __init__(
        self,
        runner: TestRunner | None = None,
        settings: SettingsManager | None = None,
    ) -> None:
        self._runner = runner or TestRunner()
        self._settings = settings or settings_manager
        self._scheduler = BackgroundScheduler()
        self._lock = threading.Lock()
        self._on_result_callbacks: list[Callable[[FullTestResult], None]] = []
        self._is_running = False

    def add_result_listener(self, callback: Callable[[FullTestResult], None]) -> None:
        """Register a callback invoked on the scheduler thread after each test."""
        self._on_result_callbacks.append(callback)

    def _job(self) -> None:
        result = self._runner.run_full_test()
        for callback in self._on_result_callbacks:
            try:
                callback(result)
            except Exception:  # pragma: no cover - defensive
                logger.exception("Result listener raised an exception")

    def start(self, interval_seconds: Optional[int] = None) -> None:
        """Start (or restart) continuous monitoring at the given interval."""
        with self._lock:
            interval = interval_seconds or self._settings.settings.monitoring_interval_seconds

            if self._scheduler.get_job(JOB_ID):
                self._scheduler.remove_job(JOB_ID)

            self._scheduler.add_job(
                self._job,
                trigger=IntervalTrigger(seconds=interval),
                id=JOB_ID,
                replace_existing=True,
                max_instances=1,
            )

            if not self._scheduler.running:
                self._scheduler.start()

            self._is_running = True
            logger.info("Monitoring scheduler started with interval=%ds", interval)

    def stop(self) -> None:
        with self._lock:
            if self._scheduler.get_job(JOB_ID):
                self._scheduler.remove_job(JOB_ID)
            self._is_running = False
            logger.info("Monitoring scheduler stopped")

    def shutdown(self) -> None:
        with self._lock:
            if self._scheduler.running:
                self._scheduler.shutdown(wait=False)
            self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def run_once_async(self) -> None:
        """Run a single test cycle immediately on a background thread."""
        thread = threading.Thread(target=self._job, daemon=True)
        thread.start()


# Module-level singletons for shared access across dashboards/desktop app.
test_runner = TestRunner()
monitor_scheduler = MonitorScheduler(runner=test_runner)
