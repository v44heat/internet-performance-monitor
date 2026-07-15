"""
validators.py
==============
Small, focused validation helpers used across the settings UI, export
routines, and database layer to guard against invalid user input.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def is_valid_date_range(start: datetime, end: datetime) -> bool:
    """Return True if start is strictly before end."""
    return start < end


def is_writable_directory(path: str | Path) -> bool:
    """
    Return True if the given path exists (or can be created) and is
    writable. Used before performing exports or changing the database
    path in Settings.
    """
    p = Path(path)
    try:
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".write_test"
        probe.touch()
        probe.unlink()
        return True
    except OSError:
        return False


def is_valid_theme(name: str) -> bool:
    return name in ("dark", "light", "auto")


def is_valid_interval(seconds: int) -> bool:
    valid = {30, 60, 300, 900, 1800, 3600}
    return seconds in valid


def is_positive_number(value: float) -> bool:
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def is_valid_percentage(value: float) -> bool:
    try:
        v = float(value)
        return 0.0 <= v <= 100.0
    except (TypeError, ValueError):
        return False


def is_non_empty_string(value: str | None) -> bool:
    return bool(value and value.strip())
