"""
helpers.py
==========
Miscellaneous general-purpose helper functions that don't belong in a
more specific utility module: date range resolution, retry decorator,
and connectivity probing.
"""

from __future__ import annotations

import socket
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, TypeVar

from config.constants import DateRangePreset
from utils.logger import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def resolve_date_range(
    preset: DateRangePreset,
    custom_start: datetime | None = None,
    custom_end: datetime | None = None,
) -> tuple[datetime, datetime]:
    """
    Resolve a DateRangePreset into concrete (start, end) datetime
    boundaries relative to "now". Custom presets require explicit
    start/end values.
    """
    now = datetime.now()

    if preset == DateRangePreset.LAST_HOUR:
        return now - timedelta(hours=1), now
    if preset == DateRangePreset.TODAY:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    if preset == DateRangePreset.YESTERDAY:
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        return yesterday_start, today_start
    if preset == DateRangePreset.LAST_7_DAYS:
        return now - timedelta(days=7), now
    if preset == DateRangePreset.LAST_30_DAYS:
        return now - timedelta(days=30), now
    if preset == DateRangePreset.CUSTOM:
        if custom_start is None or custom_end is None:
            raise ValueError("Custom date range requires start and end")
        return custom_start, custom_end

    raise ValueError(f"Unknown date range preset: {preset}")


def is_connected(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """
    Lightweight connectivity probe using a raw TCP socket connection
    to a well-known DNS server, avoiding the overhead of a full speed
    test just to check basic connectivity.
    """
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
        return True
    except OSError:
        return False


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator that retries a function call up to `max_attempts` times,
    waiting `delay_seconds` between attempts, on the given exception
    types. Used for flaky network operations like speed tests.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # type: ignore[misc]
                    last_exc = exc
                    logger.warning(
                        "Attempt %d/%d for %s failed: %s",
                        attempt,
                        max_attempts,
                        func.__name__,
                        exc,
                    )
                    if attempt < max_attempts:
                        time.sleep(delay_seconds)
            assert last_exc is not None
            raise last_exc

        return wrapper  # type: ignore[return-value]

    return decorator


def safe_round(value: float | None, digits: int = 2) -> float:
    """Round a numeric value, gracefully handling None/NaN input."""
    if value is None:
        return 0.0
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a value into the [low, high] range."""
    return max(low, min(high, value))
