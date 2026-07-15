"""Unit tests for core.jitter."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

from core.jitter import JitterCalculationError, calculate_jitter, classify_jitter


class TestJitter(unittest.TestCase):
    def test_calculates_average_min_max_current(self) -> None:
        samples = [10.0, 15.0, 12.0, 20.0]
        result = calculate_jitter(samples)
        # deltas: |15-10|=5, |12-15|=3, |20-12|=8
        self.assertAlmostEqual(result.average_ms, (5 + 3 + 8) / 3, places=2)
        self.assertAlmostEqual(result.minimum_ms, 3.0, places=2)
        self.assertAlmostEqual(result.maximum_ms, 8.0, places=2)
        self.assertAlmostEqual(result.current_ms, 8.0, places=2)

    def test_stable_latency_gives_zero_jitter(self) -> None:
        samples = [20.0, 20.0, 20.0, 20.0]
        result = calculate_jitter(samples)
        self.assertEqual(result.average_ms, 0.0)
        self.assertEqual(result.status, "Excellent")

    def test_insufficient_samples_raises(self) -> None:
        with self.assertRaises(JitterCalculationError):
            calculate_jitter([10.0])

    def test_classify_jitter_thresholds(self) -> None:
        self.assertEqual(classify_jitter(2), "Excellent")
        self.assertEqual(classify_jitter(10), "Good")
        self.assertEqual(classify_jitter(25), "Average")
        self.assertEqual(classify_jitter(50), "Poor")


if __name__ == "__main__":
    unittest.main()
