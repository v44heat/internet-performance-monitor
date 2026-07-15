"""
dashboard/analytics.py
=======================
Bridges `core.statistics` with the dashboard layer: resolves UI-level
date-range selections into `AnalyticsSummary` objects and formats them
into table-ready rows for display in Streamlit/Dash data tables.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from config.constants import DateRangePreset
from core.statistics import AnalyticsSummary, MetricSummary, compute_analytics

PRESET_LABELS: dict[DateRangePreset, str] = {
    DateRangePreset.LAST_HOUR: "Last Hour",
    DateRangePreset.TODAY: "Today",
    DateRangePreset.YESTERDAY: "Yesterday",
    DateRangePreset.LAST_7_DAYS: "Last 7 Days",
    DateRangePreset.LAST_30_DAYS: "Last 30 Days",
    DateRangePreset.CUSTOM: "Custom Range",
}


def get_analytics_summary(
    preset: DateRangePreset,
    custom_start: datetime | None = None,
    custom_end: datetime | None = None,
) -> AnalyticsSummary:
    """Thin pass-through to core.statistics.compute_analytics for UI use."""
    return compute_analytics(preset, custom_start, custom_end)


def summary_to_table(summary: AnalyticsSummary) -> pd.DataFrame:
    """
    Convert an AnalyticsSummary into a tidy DataFrame suitable for
    display as a Streamlit/Dash data table, one row per metric.
    """
    metrics: dict[str, MetricSummary] = {
        "Download (Mbps)": summary.download,
        "Upload (Mbps)": summary.upload,
        "Ping (ms)": summary.ping,
        "Jitter (ms)": summary.jitter,
        "Packet Loss (%)": summary.packet_loss,
        "Health Score": summary.internet_score,
    }

    rows = []
    for name, m in metrics.items():
        rows.append(
            {
                "Metric": name,
                "Average": m.average,
                "Median": m.median,
                "Mode": m.mode,
                "Min": m.minimum,
                "Max": m.maximum,
                "Std Dev": m.std_dev,
                "95th Percentile": m.percentile_95,
            }
        )
    return pd.DataFrame(rows)
