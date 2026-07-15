"""
formatter.py
============
Formatting helpers for turning raw numeric measurements into
display-friendly strings used across all three UI surfaces
(Streamlit, Dash, PySide6).
"""

from __future__ import annotations

from datetime import datetime


def format_speed(mbps: float) -> str:
    """Format a speed value in Mbps, e.g. '123.4 Mbps'."""
    return f"{mbps:,.1f} Mbps"


def format_ping(ms: float) -> str:
    """Format a latency value in milliseconds, e.g. '23.5 ms'."""
    return f"{ms:,.1f} ms"


def format_percentage(pct: float) -> str:
    """Format a percentage value, e.g. '1.2%'."""
    return f"{pct:,.1f}%"


def format_score(score: float) -> str:
    """Format an internet health score out of 100, e.g. '87/100'."""
    return f"{score:.0f}/100"


def score_to_stars(score: float, max_stars: int = 5) -> str:
    """Convert a 0-100 score into a star rating string, e.g. '★★★★☆'."""
    filled = round((score / 100.0) * max_stars)
    filled = max(0, min(max_stars, filled))
    return "★" * filled + "☆" * (max_stars - filled)


def format_datetime(dt: datetime | str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime object or ISO string for display."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime(fmt)


def format_bytes(num_bytes: float) -> str:
    """Format a byte count into a human readable string (KB/MB/GB)."""
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0:
            return f"{value:,.1f} {unit}"
        value /= 1024.0
    return f"{value:,.1f} PB"


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as a human readable string."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m"


def truncate(text: str, max_length: int = 40) -> str:
    """Truncate long strings (e.g. server names) with an ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"
