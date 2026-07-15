"""
database.py
===========
SQLite persistence layer for Internet Performance Monitor Pro.

Provides a thread-safe `Database` class encapsulating all reads and
writes to the `test_results` and `app_events` tables. Uses parameterized
queries throughout to avoid SQL injection and a per-call connection
strategy (via a context manager) to keep the class safe to use from
scheduler threads, Streamlit reruns, and the Qt event loop alike.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

from config.constants import DATABASE_PATH, SCHEMA_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TestResult:
    """A single, fully-populated network performance test result."""

    download_speed: float
    upload_speed: float
    ping: float
    jitter: float
    packet_loss: float
    isp: str = ""
    server: str = ""
    city: str = ""
    country: str = ""
    ip_address: str = ""
    network_type: str = ""
    internet_score: float = 0.0
    datetime_str: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None

    def to_row(self) -> dict[str, Any]:
        return {
            "datetime": self.datetime_str,
            "download_speed": self.download_speed,
            "upload_speed": self.upload_speed,
            "ping": self.ping,
            "jitter": self.jitter,
            "packet_loss": self.packet_loss,
            "isp": self.isp,
            "server": self.server,
            "city": self.city,
            "country": self.country,
            "ip_address": self.ip_address,
            "network_type": self.network_type,
            "internet_score": self.internet_score,
        }

    @staticmethod
    def from_row(row: sqlite3.Row) -> "TestResult":
        return TestResult(
            id=row["id"],
            datetime_str=row["datetime"],
            download_speed=row["download_speed"],
            upload_speed=row["upload_speed"],
            ping=row["ping"],
            jitter=row["jitter"],
            packet_loss=row["packet_loss"],
            isp=row["isp"] or "",
            server=row["server"] or "",
            city=row["city"] or "",
            country=row["country"] or "",
            ip_address=row["ip_address"] if "ip_address" in row.keys() else "",
            network_type=row["network_type"] if "network_type" in row.keys() else "",
            internet_score=row["internet_score"],
        )


class Database:
    """Thread-safe SQLite wrapper for storing and querying test results."""

    def __init__(self, db_path: Path | str = DATABASE_PATH) -> None:
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._initialize_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize_schema(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self._connect() as conn:
            if SCHEMA_PATH.exists():
                script = SCHEMA_PATH.read_text(encoding="utf-8")
                conn.executescript(script)
                logger.info("Database schema initialized at %s", self._db_path)
            else:
                logger.warning(
                    "Schema file not found at %s; skipping init", SCHEMA_PATH
                )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    def insert_result(self, result: TestResult) -> int:
        """Insert a TestResult and return its new row id."""
        row = result.to_row()
        columns = ", ".join(row.keys())
        placeholders = ", ".join(["?"] * len(row))
        sql = (
            f"INSERT INTO test_results ({columns}) VALUES ({placeholders})"
        )
        with self._lock, self._connect() as conn:
            cursor = conn.execute(sql, list(row.values()))
            new_id = cursor.lastrowid
            logger.info("Inserted test result id=%s", new_id)
            return int(new_id)

    def log_event(self, level: str, category: str, message: str) -> None:
        """Persist an application event (for the in-app event log view)."""
        sql = (
            "INSERT INTO app_events (datetime, level, category, message) "
            "VALUES (?, ?, ?, ?)"
        )
        with self._lock, self._connect() as conn:
            conn.execute(sql, (datetime.now().isoformat(), level, category, message))

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------
    def get_all_results(self, limit: Optional[int] = None) -> list[TestResult]:
        sql = "SELECT * FROM test_results ORDER BY datetime DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        with self._lock, self._connect() as conn:
            rows = conn.execute(sql).fetchall()
            return [TestResult.from_row(r) for r in rows]

    def get_results_in_range(
        self, start: datetime, end: datetime
    ) -> list[TestResult]:
        sql = (
            "SELECT * FROM test_results WHERE datetime BETWEEN ? AND ? "
            "ORDER BY datetime ASC"
        )
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                sql, (start.isoformat(), end.isoformat())
            ).fetchall()
            return [TestResult.from_row(r) for r in rows]

    def get_latest_result(self) -> Optional[TestResult]:
        sql = "SELECT * FROM test_results ORDER BY datetime DESC LIMIT 1"
        with self._lock, self._connect() as conn:
            row = conn.execute(sql).fetchone()
            return TestResult.from_row(row) if row else None

    def search_results(
        self,
        isp: Optional[str] = None,
        server: Optional[str] = None,
        min_download: Optional[float] = None,
        max_ping: Optional[float] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[TestResult]:
        """Flexible search over stored results by any combination of filters."""
        clauses: list[str] = []
        params: list[Any] = []

        if isp:
            clauses.append("isp LIKE ?")
            params.append(f"%{isp}%")
        if server:
            clauses.append("server LIKE ?")
            params.append(f"%{server}%")
        if min_download is not None:
            clauses.append("download_speed >= ?")
            params.append(min_download)
        if max_ping is not None:
            clauses.append("ping <= ?")
            params.append(max_ping)
        if start is not None:
            clauses.append("datetime >= ?")
            params.append(start.isoformat())
        if end is not None:
            clauses.append("datetime <= ?")
            params.append(end.isoformat())

        sql = "SELECT * FROM test_results"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY datetime DESC"

        with self._lock, self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [TestResult.from_row(r) for r in rows]

    def count_results(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM test_results").fetchone()
            return int(row["c"])

    def delete_result(self, result_id: int) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM test_results WHERE id = ?", (result_id,))
            logger.info("Deleted test result id=%s", result_id)

    def clear_all(self) -> None:
        """Danger zone: wipe all stored results (used by Settings > Reset)."""
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM test_results")
            logger.warning("All test results cleared from database")


# Module-level singleton used by dashboards/desktop app for convenience.
database = Database()
