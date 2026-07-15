"""Unit tests for core.statistics."""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

from config.constants import DateRangePreset
from core.database import Database, TestResult
from core.statistics import compute_analytics, results_to_dataframe


class TestStatistics(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp_dir.name) / "stats_test.db"
        self.db = Database(db_path=db_path)

        now = datetime.now()
        speeds = [50.0, 100.0, 150.0, 75.0, 125.0]
        for i, speed in enumerate(speeds):
            result = TestResult(
                download_speed=speed,
                upload_speed=speed / 5,
                ping=20.0 + i,
                jitter=2.0,
                packet_loss=0.0,
                internet_score=70.0 + i,
                datetime_str=(now - timedelta(minutes=i)).isoformat(),
            )
            self.db.insert_result(result)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def test_dataframe_conversion(self) -> None:
        results = self.db.get_all_results()
        df = results_to_dataframe(results)
        self.assertEqual(len(df), 5)
        self.assertIn("download_speed", df.columns)

    def test_compute_analytics_last_hour(self) -> None:
        summary = compute_analytics(DateRangePreset.LAST_HOUR, db=self.db)
        self.assertEqual(summary.sample_count, 5)
        self.assertEqual(summary.download.maximum, 150.0)
        self.assertEqual(summary.download.minimum, 50.0)

    def test_empty_range_returns_zeroed_summary(self) -> None:
        past_start = datetime.now() - timedelta(days=100)
        past_end = datetime.now() - timedelta(days=99)
        summary = compute_analytics(
            DateRangePreset.CUSTOM, custom_start=past_start, custom_end=past_end, db=self.db
        )
        self.assertEqual(summary.sample_count, 0)


if __name__ == "__main__":
    unittest.main()
