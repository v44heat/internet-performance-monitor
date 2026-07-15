"""
launcher.py
===========
Interactive terminal launcher menu for Internet Performance Monitor
Pro, shown when `app.py` is run with no arguments. Lets the user pick
which surface (desktop, Streamlit, Dash, single test, monitor) to
launch without needing to remember CLI flags.
"""

from __future__ import annotations

import sys

MENU = """
╔══════════════════════════════════════════════════╗
║      🌐  Internet Performance Monitor Pro         ║
╠══════════════════════════════════════════════════╣
║  1) Launch Desktop Application (PySide6)          ║
║  2) Launch Streamlit Web Dashboard                ║
║  3) Launch Dash Web Dashboard                      ║
║  4) Run a Single Speed Test (CLI)                 ║
║  5) Start Continuous Monitoring (CLI)             ║
║  0) Exit                                          ║
╚══════════════════════════════════════════════════╝
"""


def main() -> None:
    print(MENU)
    choice = input("Select an option: ").strip()

    import app as app_module

    dispatch = {
        "1": app_module.run_desktop,
        "2": app_module.run_streamlit,
        "3": app_module.run_dash,
        "4": app_module.run_single_test,
        "5": app_module.run_monitor,
    }

    if choice == "0":
        print("Goodbye!")
        sys.exit(0)

    handler = dispatch.get(choice)
    if handler is None:
        print("Invalid choice.")
        sys.exit(1)

    handler()


if __name__ == "__main__":
    main()
