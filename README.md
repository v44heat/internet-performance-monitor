# 🌐 Internet Performance Monitor Pro

A production-quality, full-stack internet performance monitoring suite built in Python. Continuously measures download/upload speed, ping, jitter, and packet loss; stores every result in SQLite; and presents the data through **three** independent interfaces — a PySide6 desktop app, a Streamlit web dashboard, and a Dash web dashboard — all sharing the same modular core engine.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- **Download / Upload speed testing** via `speedtest-cli`, with animated color-coded gauges
- **Ping, jitter & packet loss** measurement via `ping3`
- **ISP / network detection** — IP, ISP, server, country, city, connection type
- **Internet Health Score** (0–100, weighted composite metric) with star ratings
- **Continuous background monitoring** on configurable intervals (30s → 1h) via APScheduler, never blocking the UI
- **SQLite persistence** of every test with a clean, indexed schema
- **Historical analytics** — average, median, mode, std dev, 95th percentile over custom date ranges
- **Interactive Plotly charts** — zoomable, hoverable, exportable, dark-mode aware
- **CSV & JSON export** for any date range
- **Desktop notifications** (via Plyer) for poor internet, high ping, high loss, disconnects, and restores
- **Three UIs**: PySide6 desktop app, Streamlit dashboard, Dash dashboard — all sharing one core engine and design system
- **Full test suite** (`unittest`), type hints, docstrings, and structured logging throughout

---


---

## 🚀 Installation

```bash
git clone <your-repo-url>
cd internet-performance-monitor
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** `ping3` requires elevated/raw-socket permissions on some platforms (Linux may need `sudo` or `setcap`; Windows generally works out of the box).

---

## ▶️ Usage

Launch the interactive menu:
```bash
python app.py
```

Or launch a specific surface directly:
```bash
python app.py desktop      # PySide6 desktop application
python app.py streamlit    # Streamlit web dashboard  → http://localhost:8501
python app.py dash         # Dash web dashboard        → http://localhost:8050
python app.py test         # Run one test cycle from the CLI
python app.py monitor      # Start continuous background monitoring (CLI)
```

Or run each dashboard directly with its native tooling:
```bash
streamlit run dashboard/streamlit_dashboard.py
python dashboard/dash_dashboard.py
python desktop/main_window.py
```

---

## 🧪 Running Tests

```bash
python -m unittest discover -s tests -v
```

---

## 🏗️ Architecture

The application follows a clean, layered architecture:

1. **`core/`** — pure business logic (network testing, scoring, persistence, scheduling). No UI dependencies; fully unit-testable.
2. **`config/`** — shared constants, theming, and user settings consumed by every layer.
3. **`utils/`** — cross-cutting helpers (logging, formatting, validation).
4. **`dashboard/` & `desktop/`** — three independent presentation layers built entirely on top of `core/`, so any UI can be added/removed without touching business logic.

All network tests execute on background threads (QThread in the desktop app, APScheduler worker threads for continuous monitoring), so no UI ever freezes during a multi-second speed test.

---

## 🛠️ Tech Stack

Python 3.12+ · speedtest-cli · ping3 · Plotly · Streamlit · Dash · dash-bootstrap-components · PySide6 · SQLite3 · pandas · numpy · APScheduler · psutil · plyer

---

## 📄 License

MIT — see [LICENSE](LICENSE).
