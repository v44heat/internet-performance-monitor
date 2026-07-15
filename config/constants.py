"""
constants.py
============
Central repository of static constants used throughout the Internet
Performance Monitor Pro application. Keeping these values in one place
avoids "magic numbers" scattered across the codebase and makes tuning
thresholds trivial.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATABASE_DIR: Path = BASE_DIR / "database"
DATABASE_PATH: Path = DATABASE_DIR / "internet.db"
SCHEMA_PATH: Path = DATABASE_DIR / "schema.sql"
EXPORTS_DIR: Path = BASE_DIR / "exports"
LOGS_DIR: Path = BASE_DIR / "logs"
ASSETS_DIR: Path = BASE_DIR / "assets"

for _directory in (DATABASE_DIR, EXPORTS_DIR, LOGS_DIR, ASSETS_DIR):
    _directory.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Application metadata
# --------------------------------------------------------------------------
APP_NAME: str = "Internet Performance Monitor Pro"
APP_VERSION: str = "1.0.0"
APP_AUTHOR: str = "Internet Performance Monitor Team"

# --------------------------------------------------------------------------
# Speed thresholds (Mbps) used for color coding & health scoring
# --------------------------------------------------------------------------
DOWNLOAD_EXCELLENT_MBPS: float = 100.0
DOWNLOAD_GOOD_MBPS: float = 40.0
DOWNLOAD_POOR_MBPS: float = 10.0

UPLOAD_EXCELLENT_MBPS: float = 40.0
UPLOAD_GOOD_MBPS: float = 15.0
UPLOAD_POOR_MBPS: float = 5.0

# --------------------------------------------------------------------------
# Ping thresholds (milliseconds)
# --------------------------------------------------------------------------
PING_EXCELLENT_MS: float = 20.0
PING_GOOD_MS: float = 60.0
PING_AVERAGE_MS: float = 100.0
# Anything above PING_AVERAGE_MS is considered "Poor"

# --------------------------------------------------------------------------
# Jitter thresholds (milliseconds)
# --------------------------------------------------------------------------
JITTER_EXCELLENT_MS: float = 5.0
JITTER_GOOD_MS: float = 15.0
JITTER_POOR_MS: float = 30.0

# --------------------------------------------------------------------------
# Packet loss thresholds (percentage)
# --------------------------------------------------------------------------
PACKET_LOSS_EXCELLENT_PCT: float = 0.0
PACKET_LOSS_GOOD_PCT: float = 1.0
PACKET_LOSS_POOR_PCT: float = 5.0

# --------------------------------------------------------------------------
# Monitoring intervals (seconds) exposed to the UI
# --------------------------------------------------------------------------
class MonitorInterval(Enum):
    """Enumeration of selectable continuous-monitoring intervals."""

    THIRTY_SECONDS = 30
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    FIFTEEN_MINUTES = 900
    THIRTY_MINUTES = 1800
    ONE_HOUR = 3600

    @property
    def label(self) -> str:
        """Human readable label for display in UI dropdowns."""
        mapping = {
            MonitorInterval.THIRTY_SECONDS: "30 seconds",
            MonitorInterval.ONE_MINUTE: "1 minute",
            MonitorInterval.FIVE_MINUTES: "5 minutes",
            MonitorInterval.FIFTEEN_MINUTES: "15 minutes",
            MonitorInterval.THIRTY_MINUTES: "30 minutes",
            MonitorInterval.ONE_HOUR: "1 hour",
        }
        return mapping[self]


# --------------------------------------------------------------------------
# Health score weighting (must sum to 1.0)
# --------------------------------------------------------------------------
HEALTH_WEIGHT_DOWNLOAD: float = 0.30
HEALTH_WEIGHT_UPLOAD: float = 0.20
HEALTH_WEIGHT_PING: float = 0.20
HEALTH_WEIGHT_JITTER: float = 0.15
HEALTH_WEIGHT_PACKET_LOSS: float = 0.15

# --------------------------------------------------------------------------
# Status / color labels
# --------------------------------------------------------------------------
class Status(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    POOR = "Poor"


STATUS_COLORS: dict[str, str] = {
    Status.EXCELLENT.value: "#22C55E",  # green
    Status.GOOD.value: "#84CC16",       # lime
    Status.AVERAGE.value: "#F59E0B",    # amber
    Status.POOR.value: "#EF4444",       # red
}

# --------------------------------------------------------------------------
# Notification categories
# --------------------------------------------------------------------------
class NotificationType(str, Enum):
    POOR_INTERNET = "poor_internet"
    HIGH_PING = "high_ping"
    HIGH_PACKET_LOSS = "high_packet_loss"
    DISCONNECTED = "disconnected"
    CONNECTION_RESTORED = "connection_restored"


# --------------------------------------------------------------------------
# Ping test configuration
# --------------------------------------------------------------------------
PING_HOSTS: list[str] = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
PING_SAMPLE_COUNT: int = 10
PING_TIMEOUT_SECONDS: float = 2.0

# --------------------------------------------------------------------------
# Packet loss test configuration
# --------------------------------------------------------------------------
PACKET_LOSS_SAMPLE_COUNT: int = 20
PACKET_LOSS_HOST: str = "8.8.8.8"

# --------------------------------------------------------------------------
# Database field / table names
# --------------------------------------------------------------------------
TABLE_RESULTS: str = "test_results"

RESULT_COLUMNS: list[str] = [
    "id",
    "datetime",
    "download_speed",
    "upload_speed",
    "ping",
    "jitter",
    "packet_loss",
    "isp",
    "server",
    "city",
    "country",
    "internet_score",
]

# --------------------------------------------------------------------------
# Export formats
# --------------------------------------------------------------------------
class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"


# --------------------------------------------------------------------------
# Date range presets for analytics/filters
# --------------------------------------------------------------------------
class DateRangePreset(str, Enum):
    LAST_HOUR = "last_hour"
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    CUSTOM = "custom"
