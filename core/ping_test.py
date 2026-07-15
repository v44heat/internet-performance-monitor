"""
ping_test.py
============
Measures network latency (ping) using `ping3`, sampling multiple hosts
and multiple attempts per host to produce a robust average latency
reading along with the raw sample list (consumed by `jitter.py` and
`packet_loss.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ping3 import ping

from config.constants import (
    PING_AVERAGE_MS,
    PING_EXCELLENT_MS,
    PING_GOOD_MS,
    PING_HOSTS,
    PING_SAMPLE_COUNT,
    PING_TIMEOUT_SECONDS,
    Status,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class PingTestError(Exception):
    """Raised when no host responds to any ping attempt."""


@dataclass
class PingResult:
    average_ms: float
    status: str
    samples_ms: list[float] = field(default_factory=list)
    host_used: str = ""


def classify_ping(ping_ms: float) -> str:
    """Map a raw round-trip latency (ms) to a Status label."""
    if ping_ms <= PING_EXCELLENT_MS:
        return Status.EXCELLENT.value
    if ping_ms <= PING_GOOD_MS:
        return Status.GOOD.value
    if ping_ms <= PING_AVERAGE_MS:
        return Status.AVERAGE.value
    return Status.POOR.value


def _sample_host(host: str, count: int) -> list[float]:
    """Collect `count` successful ping samples (in ms) from a single host."""
    samples: list[float] = []
    for _ in range(count):
        try:
            latency_seconds = ping(host, timeout=PING_TIMEOUT_SECONDS, unit="s")
            if latency_seconds is not None:
                samples.append(latency_seconds * 1000.0)
        except (OSError, PermissionError) as exc:
            logger.debug("Ping attempt to %s failed: %s", host, exc)
    return samples


def run_ping_test(
    hosts: list[str] | None = None, sample_count: int = PING_SAMPLE_COUNT
) -> PingResult:
    """
    Run a ping test against the first responsive host in `hosts`
    (defaulting to `PING_HOSTS`), collecting `sample_count` samples.
    """
    candidate_hosts = hosts or PING_HOSTS

    for host in candidate_hosts:
        logger.info("Pinging host %s (%d samples)", host, sample_count)
        samples = _sample_host(host, sample_count)
        if samples:
            average_ms = sum(samples) / len(samples)
            status = classify_ping(average_ms)
            logger.info(
                "Ping test complete via %s: %.2f ms avg (%s)",
                host,
                average_ms,
                status,
            )
            return PingResult(
                average_ms=round(average_ms, 2),
                status=status,
                samples_ms=[round(s, 2) for s in samples],
                host_used=host,
            )
        logger.warning("Host %s did not respond, trying next", host)

    logger.error("All ping hosts unreachable: %s", candidate_hosts)
    raise PingTestError(f"No response from any host: {candidate_hosts}")
