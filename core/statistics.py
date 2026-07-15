"""
statistics.py
=============
Historical analytics engine. Computes descriptive statistics (average,
max, min, median, mode, standard deviation, 95th percentile) over
stored `TestResult` records for arbitrary date ranges, powering both
dashboard analytics pages and the desktop app's Analytics tab.
"""

from __future__ import annotations

import statistics as pystats
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
import pandas as pd

from config.constants import DateRangePreset
from core.database import Database, TestResult, database
from utils.helpers import resolve_date_range
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MetricSummary:
    """Descriptive statistics for a single metric (e.g. download speed)."""

    average: float = 0.0
    maximum: float = 0.0
    minimum: float = 0.0
    median: float = 0.0
    mode: float = 0.0
    std_dev: float = 0.0
    percentile_95: float = 0.0


@dataclass
class AnalyticsSummary:
    """Full analytics summary across all tracked metrics."""

    sample_count: int = 0
    download: MetricSummary = field(default_factory=MetricSummary)
    upload: MetricSummary = field(default_factory=MetricSummary)
    ping: MetricSummary = field(default_factory=MetricSummary)
    jitter: MetricSummary = field(default_factory=MetricSummary)
    packet_loss: MetricSummary = field(default_factory=MetricSummary)
    internet_score: MetricSummary = field(default_factory=MetricSummary)


def _summarize(values: list[float]) -> MetricSummary:
    """Compute a MetricSummary from a list of numeric values."""
    if not values:
        return MetricSummary()

    arr = np.array(values, dtype=float)
    try:
        mode_value = pystats.mode(values)
    except pystats.StatisticsError:
        mode_value = values[0]

    return MetricSummary(
        average=round(float(np.mean(arr)), 2),
        maximum=round(float(np.max(arr)), 2),
        minimum=round(float(np.min(arr)), 2),
        median=round(float(np.median(arr)), 2),
        mode=round(float(mode_value), 2),
        std_dev=round(float(np.std(arr)), 2),
        percentile_95=round(float(np.percentile(arr, 95)), 2),
    )


def results_to_dataframe(results: list[TestResult]) -> pd.DataFrame:
    """Convert a list of TestResult objects into a tidy pandas DataFrame."""
    if not results:
        return pd.DataFrame(
            columns=[
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
        )

    records = [
        {
            "id": r.id,
            "datetime": pd.to_datetime(r.datetime_str),
            "download_speed": r.download_speed,
            "upload_speed": r.upload_speed,
            "ping": r.ping,
            "jitter": r.jitter,
            "packet_loss": r.packet_loss,
            "isp": r.isp,
            "server": r.server,
            "city": r.city,
            "country": r.country,
            "internet_score": r.internet_score,
        }
        for r in results
    ]
    df = pd.DataFrame(records)
    return df.sort_values("datetime")


def compute_analytics(
    preset: DateRangePreset = DateRangePreset.LAST_7_DAYS,
    custom_start: datetime | None = None,
    custom_end: datetime | None = None,
    db: Database | None = None,
) -> AnalyticsSummary:
    """
    Compute a full AnalyticsSummary for the given date range preset by
    pulling results from the database and summarizing each metric.
    """
    db = db or database
    start, end = resolve_date_range(preset, custom_start, custom_end)
    results = db.get_results_in_range(start, end)

    logger.info(
        "Computing analytics for %s -> %s (%d records)",
        start.isoformat(),
        end.isoformat(),
        len(results),
    )

    if not results:
        return AnalyticsSummary(sample_count=0)

    df = results_to_dataframe(results)

    return AnalyticsSummary(
        sample_count=len(results),
        download=_summarize(df["download_speed"].tolist()),
        upload=_summarize(df["upload_speed"].tolist()),
        ping=_summarize(df["ping"].tolist()),
        jitter=_summarize(df["jitter"].tolist()),
        packet_loss=_summarize(df["packet_loss"].tolist()),
        internet_score=_summarize(df["internet_score"].tolist()),
    )


def compute_analytics_for_range(
    start: datetime, end: datetime, db: Database | None = None
) -> AnalyticsSummary:
    """Convenience wrapper for an explicit custom date range."""
    return compute_analytics(
        preset=DateRangePreset.CUSTOM, custom_start=start, custom_end=end, db=db
    )
