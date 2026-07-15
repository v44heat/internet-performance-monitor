"""Unit tests for core.internet_health."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

from core.internet_health import calculate_internet_health, classify_health_score


class TestInternetHealth(unittest.TestCase):
    def test_excellent_connection_scores_high(self) -> None:
        result = calculate_internet_health(
            download_mbps=200, upload_mbps=50, ping_ms=10, jitter_ms=2, packet_loss_pct=0
        )
        self.assertGreaterEqual(result.score, 85)
        self.assertEqual(result.status, "Excellent")

    def test_poor_connection_scores_low(self) -> None:
        result = calculate_internet_health(
            download_mbps=1, upload_mbps=0.5, ping_ms=400, jitter_ms=100, packet_loss_pct=20
        )
        self.assertLess(result.score, 40)
        self.assertEqual(result.status, "Poor")

    def test_score_bounds(self) -> None:
        result = calculate_internet_health(0, 0, 1000, 1000, 100)
        self.assertGreaterEqual(result.score, 0)
        self.assertLessEqual(result.score, 100)

    def test_classify_health_score_boundaries(self) -> None:
        self.assertEqual(classify_health_score(90), "Excellent")
        self.assertEqual(classify_health_score(70), "Good")
        self.assertEqual(classify_health_score(50), "Average")
        self.assertEqual(classify_health_score(10), "Poor")


if __name__ == "__main__":
    unittest.main()
