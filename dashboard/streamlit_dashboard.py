"""
streamlit_dashboard.py
======================
Professional Streamlit dashboard for Internet Performance Monitor Pro.
Provides a sidebar-driven multi-page experience: Dashboard, History,
Analytics, Reports, Export, and Settings — all sharing the same dark
glassmorphism theme.

Run with:
    streamlit run dashboard/streamlit_dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when launched via `streamlit run`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from config.constants import APP_NAME, APP_VERSION, DateRangePreset, ExportFormat
from config.settings import settings_manager
from core.database import database
from core.exporter import export_by_preset
from core.internet_health import calculate_internet_health
from core.scheduler import monitor_scheduler, test_runner
from core.statistics import results_to_dataframe
from dashboard.analytics import PRESET_LABELS, get_analytics_summary, summary_to_table
from dashboard.cards import (
    render_info_card_html,
    render_metric_card_html,
    render_stars_card_html,
    render_status_bar_html,
)
from dashboard.charts import (
    build_gauge,
    build_health_score_gauge,
    build_history_line_chart,
    build_multi_metric_chart,
    build_score_distribution_chart,
)
from dashboard.theme import get_streamlit_css
from utils.formatter import format_percentage, format_ping, format_score, format_speed

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_session_state() -> None:
    if "theme" not in st.session_state:
        st.session_state.theme = settings_manager.settings.theme
    if "connection_status" not in st.session_state:
        st.session_state.connection_status = "Connected"


def _sidebar_navigation() -> str:
    with st.sidebar:
        st.markdown(f'<div class="app-title">🌐 {APP_NAME}</div>', unsafe_allow_html=True)
        st.caption(f"v{APP_VERSION}")
        st.markdown("---")
        page = st.radio(
            "Navigation",
            ["Dashboard", "History", "Analytics", "Reports", "Export", "Settings"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown(
            render_status_bar_html(st.session_state.connection_status, st.session_state.theme),
            unsafe_allow_html=True,
        )
        return page


def _run_test_button() -> None:
    if st.button("🚀 Run Speed Test Now", use_container_width=True, type="primary"):
        st.session_state.connection_status = "Testing"
        with st.spinner("Running full network performance test..."):
            result = test_runner.run_full_test()
        if result.success:
            st.success("Test completed successfully!")
            st.session_state.connection_status = "Connected"
        else:
            st.error(f"Test failed: {result.error_message}")
            st.session_state.connection_status = "Disconnected"
        st.rerun()


def _page_dashboard() -> None:
    theme_name = st.session_state.theme
    st.title("📊 Live Dashboard")
    _run_test_button()

    latest = database.get_latest_result()

    if latest is None:
        st.info("No test results yet. Click **Run Speed Test Now** to get started.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(
            build_gauge(latest.download_speed, "Download", 300, "Mbps", "Excellent", theme_name),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            build_gauge(latest.upload_speed, "Upload", 100, "Mbps", "Excellent", theme_name),
            use_container_width=True,
        )
    with col3:
        st.plotly_chart(
            build_health_score_gauge(latest.internet_score, theme_name),
            use_container_width=True,
        )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric_card_html("Ping", format_ping(latest.ping), icon="📶"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric_card_html("Jitter", f"{latest.jitter:.1f} ms", icon="📡"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric_card_html("Packet Loss", format_percentage(latest.packet_loss), icon="📉"), unsafe_allow_html=True)
    with c4:
        st.markdown(
            render_info_card_html(
                "Network",
                {"ISP": latest.isp or "—", "Server": latest.server or "—", "Location": f"{latest.city}, {latest.country}"},
            ),
            unsafe_allow_html=True,
        )

    st.markdown("### Recent Trend")
    df = results_to_dataframe(database.get_all_results(limit=50))
    st.plotly_chart(build_multi_metric_chart(df, theme_name), use_container_width=True)


def _page_history() -> None:
    st.title("🕓 Test History")

    with st.expander("🔎 Search & Filter", expanded=True):
        col1, col2, col3 = st.columns(3)
        isp_filter = col1.text_input("ISP contains")
        server_filter = col2.text_input("Server contains")
        max_ping = col3.number_input("Max ping (ms)", min_value=0, value=0, step=10)

    results = database.search_results(
        isp=isp_filter or None,
        server=server_filter or None,
        max_ping=max_ping or None,
    )
    df = results_to_dataframe(results)

    st.caption(f"{len(df)} results")
    st.dataframe(df, use_container_width=True, height=500)


def _page_analytics() -> None:
    st.title("📈 Analytics")

    preset_name = st.selectbox("Date Range", list(PRESET_LABELS.values()))
    preset = next(k for k, v in PRESET_LABELS.items() if v == preset_name)

    custom_start, custom_end = None, None
    if preset == DateRangePreset.CUSTOM:
        col1, col2 = st.columns(2)
        custom_start = datetime.combine(col1.date_input("Start date"), datetime.min.time())
        custom_end = datetime.combine(col2.date_input("End date"), datetime.max.time())

    summary = get_analytics_summary(preset, custom_start, custom_end)

    if summary.sample_count == 0:
        st.info("No data available for the selected range.")
        return

    st.caption(f"{summary.sample_count} samples analyzed")
    st.dataframe(summary_to_table(summary), use_container_width=True)

    start = custom_start or (datetime.now() - timedelta(days=7))
    end = custom_end or datetime.now()
    results = database.get_results_in_range(start, end)
    df = results_to_dataframe(results)

    theme_name = st.session_state.theme
    tab1, tab2, tab3 = st.tabs(["Speed History", "Quality History", "Score Distribution"])
    with tab1:
        st.plotly_chart(build_multi_metric_chart(df, theme_name), use_container_width=True)
    with tab2:
        st.plotly_chart(build_history_line_chart(df, "ping", "Ping History", "ms", theme_name), use_container_width=True)
        st.plotly_chart(build_history_line_chart(df, "packet_loss", "Packet Loss History", "%", theme_name), use_container_width=True)
    with tab3:
        st.plotly_chart(build_score_distribution_chart(df, theme_name), use_container_width=True)


def _page_reports() -> None:
    st.title("📄 Reports")
    latest = database.get_latest_result()
    if latest is None:
        st.info("No data to report on yet.")
        return

    health = calculate_internet_health(
        latest.download_speed, latest.upload_speed, latest.ping, latest.jitter, latest.packet_loss
    )
    st.markdown(
        render_stars_card_html("Overall Internet Health", health.stars, format_score(health.score)),
        unsafe_allow_html=True,
    )

    summary_7d = get_analytics_summary(DateRangePreset.LAST_7_DAYS)
    st.markdown("### 7-Day Summary")
    st.table(summary_to_table(summary_7d))


def _page_export() -> None:
    st.title("⬇️ Export Data")

    col1, col2 = st.columns(2)
    preset_name = col1.selectbox("Range", list(PRESET_LABELS.values()))
    preset = next(k for k, v in PRESET_LABELS.items() if v == preset_name)
    fmt_name = col2.selectbox("Format", ["CSV", "JSON"])
    fmt = ExportFormat.CSV if fmt_name == "CSV" else ExportFormat.JSON

    if st.button("Generate Export File", type="primary"):
        try:
            path = export_by_preset(preset, fmt)
            st.success(f"Exported to: {path}")
            with open(path, "rb") as fh:
                st.download_button("Download File", fh, file_name=Path(path).name)
        except Exception as exc:
            st.error(f"Export failed: {exc}")


def _page_settings() -> None:
    st.title("⚙️ Settings")
    s = settings_manager.settings

    theme_choice = st.selectbox("Theme", ["dark", "light"], index=0 if s.theme == "dark" else 1)
    interval_choice = st.select_slider(
        "Monitoring Interval (seconds)",
        options=[30, 60, 300, 900, 1800, 3600],
        value=s.monitoring_interval_seconds,
    )
    notifications_enabled = st.checkbox("Enable Notifications", value=s.notifications_enabled)

    st.markdown("#### Notification Thresholds")
    t = s.notification_thresholds
    max_ping = st.slider("Max acceptable ping (ms)", 20, 300, int(t.max_ping_ms))
    max_loss = st.slider("Max acceptable packet loss (%)", 0, 20, int(t.max_packet_loss_pct))
    min_download = st.slider("Min acceptable download (Mbps)", 1, 100, int(t.min_download_mbps))

    if st.button("💾 Save Settings", type="primary"):
        settings_manager.update(
            theme=theme_choice,
            monitoring_interval_seconds=interval_choice,
            notifications_enabled=notifications_enabled,
        )
        settings_manager.update_thresholds(
            max_ping_ms=max_ping, max_packet_loss_pct=max_loss, min_download_mbps=min_download
        )
        st.session_state.theme = theme_choice
        st.success("Settings saved.")
        st.rerun()

    st.markdown("---")
    st.markdown("#### Continuous Monitoring")
    if monitor_scheduler.is_running:
        st.info("Monitoring is currently **active**.")
        if st.button("⏹ Stop Monitoring"):
            monitor_scheduler.stop()
            st.rerun()
    else:
        st.warning("Monitoring is currently **stopped**.")
        if st.button("▶️ Start Monitoring"):
            monitor_scheduler.start(interval_choice)
            st.rerun()


def main() -> None:
    _init_session_state()
    st.markdown(get_streamlit_css(st.session_state.theme), unsafe_allow_html=True)

    page = _sidebar_navigation()

    pages = {
        "Dashboard": _page_dashboard,
        "History": _page_history,
        "Analytics": _page_analytics,
        "Reports": _page_reports,
        "Export": _page_export,
        "Settings": _page_settings,
    }
    pages[page]()


if __name__ == "__main__":
    main()
