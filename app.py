"""
app.py
======
Primary CLI entry point for Internet Performance Monitor Pro.

Usage:
    python app.py desktop      # Launch the PySide6 desktop application
    python app.py streamlit    # Launch the Streamlit web dashboard
    python app.py dash         # Launch the Dash web dashboard
    python app.py test         # Run a single test cycle from the CLI
    python app.py monitor      # Start continuous background monitoring (CLI)

If no argument is given, the interactive launcher menu is shown
instead (see `launcher.py`).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def run_desktop() -> None:
    from desktop.main_window import main as desktop_main

    desktop_main()


def run_streamlit() -> None:
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(PROJECT_ROOT / "dashboard" / "streamlit_dashboard.py")],
        check=False,
    )


def run_dash() -> None:
    from dashboard.dash_dashboard import app as dash_app

    dash_app.run(debug=False, port=8050)


def run_single_test() -> None:
    from core.scheduler import test_runner

    print("Running full network performance test...")
    result = test_runner.run_full_test()
    if result.success:
        r = result.test_result
        print(f"✅ Test complete — Score: {r.internet_score:.0f}/100")
        print(f"   Download: {r.download_speed:.1f} Mbps")
        print(f"   Upload:   {r.upload_speed:.1f} Mbps")
        print(f"   Ping:     {r.ping:.1f} ms")
        print(f"   Jitter:   {r.jitter:.1f} ms")
        print(f"   Loss:     {r.packet_loss:.1f}%")
        print(f"   ISP:      {r.isp}")
    else:
        print(f"❌ Test failed: {result.error_message}")


def run_monitor() -> None:
    import time

    from core.scheduler import monitor_scheduler

    print("Starting continuous monitoring (Ctrl+C to stop)...")
    monitor_scheduler.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor_scheduler.shutdown()


COMMANDS = {
    "desktop": run_desktop,
    "streamlit": run_streamlit,
    "dash": run_dash,
    "test": run_single_test,
    "monitor": run_monitor,
}


def main() -> None:
    if len(sys.argv) < 2:
        from launcher import main as launcher_main

        launcher_main()
        return

    command = sys.argv[1].lower()
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(COMMANDS)}")
        sys.exit(1)

    handler()


if __name__ == "__main__":
    main()
