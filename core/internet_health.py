"""
internet_health.py
==================
Combines download speed, upload speed, ping, jitter, and packet loss
measurements into a single weighted "Internet Health Score" out of
100, along with a star rating and qualitative status label.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.constants import (
    DOWNLOAD_EXCELLENT_MBPS,
    HEALTH_WEIGHT_DOWNLOAD,
    HEALTH_WEIGHT_JITTER,
    HEALTH_WEIGHT_PACKET_LOSS,
    HEALTH_WEIGHT_PING,
    HEALTH_WEIGHT_UPLOAD,
    JITTER_POOR_MS,
    PACKET_LOSS_POOR_PCT,
    PING_AVERAGE_MS,
    Status,
    UPLOAD_EXCELLENT_MBPS,
)
# impoerts
from utils.formatter import score_to_stars
from utils.helpers import clamp
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HealthScoreResult:
    score: float
    status: str
    stars: str


def _normalize_higher_is_better(value: float, best: float) -> float:
    """Scale a metric where higher is better into a 0-1 range."""
    return clamp(value / best, 0.0, 1.0)


def _normalize_lower_is_better(value: float, worst: float) -> float:
    """Scale a metric where lower is better into a 0-1 range (1 = best)."""
    if worst <= 0:
        return 1.0
    return clamp(1.0 - (value / worst), 0.0, 1.0)


def classify_health_score(score: float) -> str:
    """Map a 0-100 health score to a qualitative Status label."""
    if score >= 85:
        return Status.EXCELLENT.value
    if score >= 65:
        return Status.GOOD.value
    if score >= 40:
        return Status.AVERAGE.value
    return Status.POOR.value


def calculate_internet_health(
    download_mbps: float,
    upload_mbps: float,
    ping_ms: float,
    jitter_ms: float,
    packet_loss_pct: float,
) -> HealthScoreResult:
    """
    Compute a weighted 0-100 Internet Health Score from the five core
    network metrics. Each metric is first normalized to a 0-1 "quality"
    value, then combined using the configured weights.
    """
    download_quality = _normalize_higher_is_better(
        download_mbps, DOWNLOAD_EXCELLENT_MBPS
    )
    upload_quality = _normalize_higher_is_better(upload_mbps, UPLOAD_EXCELLENT_MBPS)
    ping_quality = _normalize_lower_is_better(ping_ms, PING_AVERAGE_MS * 2)
    jitter_quality = _normalize_lower_is_better(jitter_ms, JITTER_POOR_MS * 2)
    packet_loss_quality = _normalize_lower_is_better(
        packet_loss_pct, PACKET_LOSS_POOR_PCT * 4
    )

    weighted_sum = (
        download_quality * HEALTH_WEIGHT_DOWNLOAD
        + upload_quality * HEALTH_WEIGHT_UPLOAD
        + ping_quality * HEALTH_WEIGHT_PING
        + jitter_quality * HEALTH_WEIGHT_JITTER
        + packet_loss_quality * HEALTH_WEIGHT_PACKET_LOSS
    )

    score = round(weighted_sum * 100, 1)
    status = classify_health_score(score)
    stars = score_to_stars(score)

    logger.info(
        "Health score computed: %.1f (%s) [dl=%.2f ul=%.2f ping=%.2f jitter=%.2f loss=%.2f]",
        score,
        status,
        download_quality,
        upload_quality,
        ping_quality,
        jitter_quality,
        packet_loss_quality,
    )

    return HealthScoreResult(score=score, status=status, stars=stars)
