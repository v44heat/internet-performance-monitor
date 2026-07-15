"""
exporter.py
===========
Exports stored test results to CSV or JSON files for a given date
range (today, weekly, monthly, or a fully custom range), writing into
the configured exports folder.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.constants import EXPORTS_DIR, RESULT_COLUMNS, DateRangePreset, ExportFormat
from core.database import Database, TestResult, database
from utils.helpers import resolve_date_range
from utils.logger import get_logger
from utils.validators import is_writable_directory

logger = get_logger(__name__)


class ExportError(Exception):
    """Raised when an export operation fails."""


def _result_to_flat_dict(result: TestResult) -> dict:
    data = asdict(result)
    data["datetime"] = data.pop("datetime_str")
    return {col: data.get(col, "") for col in RESULT_COLUMNS}


def _build_filename(preset: DateRangePreset, fmt: ExportFormat) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"internet_report_{preset.value}_{timestamp}.{fmt.value}"


def export_to_csv(
    results: list[TestResult], destination_folder: Path | str = EXPORTS_DIR, filename: Optional[str] = None
) -> Path:
    """Write a list of TestResult records to a CSV file and return its path."""
    folder = Path(destination_folder)
    if not is_writable_directory(folder):
        raise ExportError(f"Export folder is not writable: {folder}")

    filename = filename or f"internet_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = folder / filename

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=RESULT_COLUMNS)
            writer.writeheader()
            for result in results:
                writer.writerow(_result_to_flat_dict(result))
        logger.info("Exported %d results to CSV: %s", len(results), filepath)
        return filepath
    except OSError as exc:
        logger.error("CSV export failed: %s", exc)
        raise ExportError(str(exc)) from exc


def export_to_json(
    results: list[TestResult], destination_folder: Path | str = EXPORTS_DIR, filename: Optional[str] = None
) -> Path:
    """Write a list of TestResult records to a JSON file and return its path."""
    folder = Path(destination_folder)
    if not is_writable_directory(folder):
        raise ExportError(f"Export folder is not writable: {folder}")

    filename = filename or f"internet_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = folder / filename

    try:
        payload = [_result_to_flat_dict(r) for r in results]
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        logger.info("Exported %d results to JSON: %s", len(results), filepath)
        return filepath
    except OSError as exc:
        logger.error("JSON export failed: %s", exc)
        raise ExportError(str(exc)) from exc


def export_by_preset(
    preset: DateRangePreset,
    fmt: ExportFormat,
    custom_start: datetime | None = None,
    custom_end: datetime | None = None,
    destination_folder: Path | str = EXPORTS_DIR,
    db: Database | None = None,
) -> Path:
    """
    High-level export entry point: resolve the date range, pull
    matching results, and write them in the requested format.
    """
    db = db or database
    start, end = resolve_date_range(preset, custom_start, custom_end)
    results = db.get_results_in_range(start, end)
    filename = _build_filename(preset, fmt)

    if fmt == ExportFormat.CSV:
        return export_to_csv(results, destination_folder, filename)
    if fmt == ExportFormat.JSON:
        return export_to_json(results, destination_folder, filename)

    raise ExportError(f"Unsupported export format: {fmt}")
