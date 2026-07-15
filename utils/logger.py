"""
logger.py
=========
Centralized logging configuration for Internet Performance Monitor Pro.
All modules should call `get_logger(__name__)` rather than configuring
their own handlers, ensuring consistent formatting and a single set of
rotating log files under /logs.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.constants import LOGS_DIR

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root_logger() -> None:
    """Attach rotating file + console handlers to the root logger once."""
    global _configured
    if _configured:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path: Path = LOGS_DIR / "app.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    error_path: Path = LOGS_DIR / "errors.log"
    error_handler = RotatingFileHandler(
        error_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.addHandler(error_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    _configure_root_logger()
    return logging.getLogger(name)
