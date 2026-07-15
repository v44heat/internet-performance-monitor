"""
upload_test.py
==============
Wraps `speedtest-cli` to measure upload bandwidth in Mbps with the
same reliability and classification conventions as `download_test.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

import speedtest

from config.constants import (
    Status,
    UPLOAD_EXCELLENT_MBPS,
    UPLOAD_GOOD_MBPS,
    UPLOAD_POOR_MBPS,
)
from utils.helpers import retry
from utils.logger import get_logger

logger = get_logger(__name__)


class UploadTestError(Exception):
    """Raised when an upload speed test cannot be completed."""


@dataclass
class UploadResult:
    speed_mbps: float
    status: str


def classify_upload_speed(speed_mbps: float) -> str:
    """Map a raw upload speed to a Status label for UI color coding."""
    if speed_mbps >= UPLOAD_EXCELLENT_MBPS:
        return Status.EXCELLENT.value
    if speed_mbps >= UPLOAD_GOOD_MBPS:
        return Status.GOOD.value
    if speed_mbps >= UPLOAD_POOR_MBPS:
        return Status.AVERAGE.value
    return Status.POOR.value


@retry(max_attempts=2, delay_seconds=2.0, exceptions=(speedtest.SpeedtestException,))
def run_upload_test(shared_client: "speedtest.Speedtest | None" = None) -> UploadResult:
    """
    Execute an upload speed test and return the measured throughput
    in Mbps along with its classification.

    Args:
        shared_client: Optionally pass an already-initialized
            `speedtest.Speedtest` instance to share server selection
            with a preceding download test.
    """
    try:
        client = shared_client or speedtest.Speedtest()
        if shared_client is None:
            client.get_best_server()

        logger.info("Starting upload speed test")
        bits_per_second = client.upload()
        mbps = bits_per_second / 1_000_000
        status = classify_upload_speed(mbps)
        logger.info("Upload test complete: %.2f Mbps (%s)", mbps, status)
        return UploadResult(speed_mbps=round(mbps, 2), status=status)
    except speedtest.SpeedtestException as exc:
        logger.error("Upload test failed: %s", exc)
        raise UploadTestError(str(exc)) from exc
