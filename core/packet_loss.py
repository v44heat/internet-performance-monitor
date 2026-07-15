"""
packet_loss.py
==============
Measures packet loss percentage by sending a batch of pings to a
target host and calculating the ratio of failed (timed-out / dropped)
responses to total attempts.
"""

from __future__ import annotations

from dataclasses import dataclass

from ping3 import ping

from config.constants import (
    PACKET_LOSS_EXCELLENT_PCT,
    PACKET_LOSS_GOOD_PCT,
    PACKET_LOSS_HOST,
    PACKET_LOSS_POOR_PCT,
    PACKET_LOSS_SAMPLE_COUNT,
    PING_TIMEOUT_SECONDS,
    Status,
)
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PacketLossResult:
    loss_percentage: float
    status: str
    packets_sent: int
    packets_lost: int
    host_used: str


def classify_packet_loss(loss_pct: float) -> str:
    """Map a packet loss percentage to a Status label."""
    if loss_pct <= PACKET_LOSS_EXCELLENT_PCT:
        return Status.EXCELLENT.value
    if loss_pct <= PACKET_LOSS_GOOD_PCT:
        return Status.GOOD.value
    if loss_pct <= PACKET_LOSS_POOR_PCT:
        return Status.AVERAGE.value
    return Status.POOR.value


def run_packet_loss_test(
    host: str = PACKET_LOSS_HOST, sample_count: int = PACKET_LOSS_SAMPLE_COUNT
) -> PacketLossResult:
    """
    Send `sample_count` ICMP echo requests to `host` and compute the
    percentage that did not receive a response within the timeout.
    """
    logger.info("Starting packet loss test against %s (%d packets)", host, sample_count)

    lost = 0
    for _ in range(sample_count):
        try:
            response = ping(host, timeout=PING_TIMEOUT_SECONDS, unit="s")
            if response is None:
                lost += 1
        except (OSError, PermissionError) as exc:
            logger.debug("Packet loss probe error: %s", exc)
            lost += 1

    loss_pct = (lost / sample_count) * 100.0 if sample_count else 0.0
    status = classify_packet_loss(loss_pct)

    logger.info(
        "Packet loss test complete: %.1f%% (%d/%d lost) (%s)",
        loss_pct,
        lost,
        sample_count,
        status,
    )

    return PacketLossResult(
        loss_percentage=round(loss_pct, 2),
        status=status,
        packets_sent=sample_count,
        packets_lost=lost,
        host_used=host,
    )
