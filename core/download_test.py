"""
download_test.py
================
Wraps the `speedtest-cli` library to measure download bandwidth in
Mbps, expose a color-coded status classification, and gracefully
degrade with clear errors when no server or internet connection is
available.
"""

from __future__ import annotations

from dataclasses import dataclass

import speedtest

from config.constants import (
    DOWNLOAD_EXCELLENT_MBPS,
    DOWNLOAD_GOOD_MBPS,
    DOWNLOAD_POOR_MBPS,
    Status,
)
from utils.helpers import retry
from utils.logger import get_logger

logger = get_logger(__name__)


class DownloadTestError(Exception):
    """Raised when a download speed test cannot be completed."""


@dataclass
class DownloadResult:
    speed_mbps: float
    status: str


def classify_download_speed(speed_mbps: float) -> str:
    """Map a raw download speed to a Status label for UI color coding."""
    if speed_mbps >= DOWNLOAD_EXCELLENT_MBPS:
        return Status.EXCELLENT.value
    if speed_mbps >= DOWNLOAD_GOOD_MBPS:
        return Status.GOOD.value
    if speed_mbps >= DOWNLOAD_POOR_MBPS:
        return Status.AVERAGE.value
    return Status.POOR.value


@retry(max_attempts=2, delay_seconds=2.0, exceptions=(speedtest.SpeedtestException,))
def run_download_test(shared_client: "speedtest.Speedtest | None" = None) -> DownloadResult:
    """
    Execute a download speed test and return the measured throughput
    in Mbps along with its classification.

    Args:
        shared_client: Optionally pass an already-initialized
            `speedtest.Speedtest` instance (with best server selected)
            to avoid repeating server discovery when download, upload,
            and ISP info are all measured back-to-back.
    """
    try:
        client = shared_client or speedtest.Speedtest()
        if shared_client is None:
            client.get_best_server()

        logger.info("Starting download speed test")
        bits_per_second = client.download()
        mbps = bits_per_second / 1_000_000
        status = classify_download_speed(mbps)
        logger.info("Download test complete: %.2f Mbps (%s)", mbps, status)
        return DownloadResult(speed_mbps=round(mbps, 2), status=status)
    except speedtest.SpeedtestException as exc:
        logger.error("Download test failed: %s", exc)
        raise DownloadTestError(str(exc)) from exc
