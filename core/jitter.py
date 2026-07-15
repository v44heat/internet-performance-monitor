"""
jitter.py
=========
Computes network jitter — the variation in latency between
consecutive ping samples — from a list of raw ping samples produced
by `ping_test.py`. Reports average, minimum, maximum, and "current"
(most recent) jitter values.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.constants import JITTER_EXCELLENT_MS, JITTER_GOOD_MS, JITTER_POOR_MS, Status
from utils.logger import get_logger

logger = get_logger(__name__)


class JitterCalculationError(Exception):
    """Raised when jitter cannot be computed from the given samples."""


@dataclass
class JitterResult:
    average_ms: float
    minimum_ms: float
    maximum_ms: float
    current_ms: float
    status: str


def classify_jitter(jitter_ms: float) -> str:
    """Map an average jitter value (ms) to a Status label."""
    if jitter_ms <= JITTER_EXCELLENT_MS:
        return Status.EXCELLENT.value
    if jitter_ms <= JITTER_GOOD_MS:
        return Status.GOOD.value
    if jitter_ms <= JITTER_POOR_MS:
        return Status.AVERAGE.value
    return Status.POOR.value


def calculate_jitter(samples_ms: list[float]) -> JitterResult:
    """
    Calculate jitter statistics from a sequence of ping round-trip
    times (ms). Jitter for each pair of consecutive samples is the
    absolute difference between them; the deltas are then aggregated.
    """
    if len(samples_ms) < 2:
        logger.error("Insufficient ping samples for jitter calculation: %d", len(samples_ms))
        raise JitterCalculationError(
            "At least 2 ping samples are required to compute jitter"
        )

    deltas = [
        abs(samples_ms[i] - samples_ms[i - 1]) for i in range(1, len(samples_ms))
    ]

    average = sum(deltas) / len(deltas)
    minimum = min(deltas)
    maximum = max(deltas)
    current = deltas[-1]
    status = classify_jitter(average)

    logger.info(
        "Jitter computed: avg=%.2f min=%.2f max=%.2f current=%.2f (%s)",
        average,
        minimum,
        maximum,
        current,
        status,
    )

    return JitterResult(
        average_ms=round(average, 2),
        minimum_ms=round(minimum, 2),
        maximum_ms=round(maximum, 2),
        current_ms=round(current, 2),
        status=status,
    )
