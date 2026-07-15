"""Unit tests for status-classification helpers across core modules."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

from core.download_test import classify_download_speed
from core.upload_test import classify_upload_speed
from core.ping_test import classify_ping
from core.packet_loss import classify_packet_loss


class TestClassifiers(unittest.TestCase):
    def test_download_classification(self) -> None:
        self.assertEqual(classify_download_speed(150), "Excellent")
        self.assertEqual(classify_download_speed(50), "Good")
        self.assertEqual(classify_download_speed(15), "Average")
        self.assertEqual(classify_download_speed(2), "Poor")

    def test_upload_classification(self) -> None:
        self.assertEqual(classify_upload_speed(50), "Excellent")
        self.assertEqual(classify_upload_speed(20), "Good")
        self.assertEqual(classify_upload_speed(7), "Average")
        self.assertEqual(classify_upload_speed(1), "Poor")

    def test_ping_classification(self) -> None:
        self.assertEqual(classify_ping(10), "Excellent")
        self.assertEqual(classify_ping(40), "Good")
        self.assertEqual(classify_ping(80), "Average")
        self.assertEqual(classify_ping(150), "Poor")

    def test_packet_loss_classification(self) -> None:
        self.assertEqual(classify_packet_loss(0), "Excellent")
        self.assertEqual(classify_packet_loss(0.5), "Good")
        self.assertEqual(classify_packet_loss(3), "Average")
        self.assertEqual(classify_packet_loss(10), "Poor")


if __name__ == "__main__":
    unittest.main()
