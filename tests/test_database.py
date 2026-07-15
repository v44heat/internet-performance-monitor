"""Unit tests for core.database, using a temporary SQLite file per test."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

from core.database import Database, TestResult


class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self._tmp_dir.name) / "test_internet.db"
        self.db = Database(db_path=db_path)

    def tearDown(self) -> None:
        self._tmp_dir.cleanup()

    def _make_result(self, **overrides) -> TestResult:
        defaults = dict(
            download_speed=100.0,
            upload_speed=20.0,
            ping=15.0,
            jitter=3.0,
            packet_loss=0.0,
            isp="TestISP",
            server="TestServer",
            city="TestCity",
            country="TestCountry",
            internet_score=85.0,
        )
        defaults.update(overrides)
        return TestResult(**defaults)

    def test_insert_and_retrieve(self) -> None:
        result = self._make_result()
        new_id = self.db.insert_result(result)
        self.assertIsInstance(new_id, int)
        self.assertEqual(self.db.count_results(), 1)

        latest = self.db.get_latest_result()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.isp, "TestISP")
        self.assertEqual(latest.download_speed, 100.0)

    def test_search_by_isp(self) -> None:
        self.db.insert_result(self._make_result(isp="Comcast"))
        self.db.insert_result(self._make_result(isp="Verizon"))

        results = self.db.search_results(isp="Comcast")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].isp, "Comcast")

    def test_search_by_max_ping(self) -> None:
        self.db.insert_result(self._make_result(ping=10.0))
        self.db.insert_result(self._make_result(ping=200.0))

        results = self.db.search_results(max_ping=50.0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].ping, 10.0)

    def test_delete_result(self) -> None:
        new_id = self.db.insert_result(self._make_result())
        self.assertEqual(self.db.count_results(), 1)
        self.db.delete_result(new_id)
        self.assertEqual(self.db.count_results(), 0)

    def test_clear_all(self) -> None:
        for _ in range(3):
            self.db.insert_result(self._make_result())
        self.assertEqual(self.db.count_results(), 3)
        self.db.clear_all()
        self.assertEqual(self.db.count_results(), 0)


if __name__ == "__main__":
    unittest.main()
