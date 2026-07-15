"""
network_info.py
===============
Detects ISP, public IP address, nearest speedtest server, and
geographic (country/region/city) information, as well as basic local
network-type detection (Wi-Fi vs Ethernet) via `psutil`.
"""

from __future__ import annotations

from dataclasses import dataclass

import psutil
import speedtest

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NetworkInfo:
    isp: str = "Unknown"
    ip_address: str = "Unknown"
    server_name: str = "Unknown"
    server_location: str = "Unknown"
    country: str = "Unknown"
    region: str = "Unknown"
    city: str = "Unknown"
    network_type: str = "Unknown"


def detect_network_type() -> str:
    """
    Best-effort classification of the active network interface as
    'Wi-Fi', 'Ethernet', or 'Unknown', based on interface naming
    conventions reported by psutil (works cross-platform reasonably
    well, though naming varies by OS).
    """
    try:
        stats = psutil.net_if_stats()
        active_interfaces = [
            name for name, s in stats.items() if s.isup and name != "lo"
        ]
        for name in active_interfaces:
            lowered = name.lower()
            if any(tag in lowered for tag in ("wl", "wifi", "wlan", "airport")):
                return "Wi-Fi"
            if any(tag in lowered for tag in ("eth", "en0", "enp", "local area")):
                return "Ethernet"
        return "Unknown" if not active_interfaces else active_interfaces[0]
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to detect network type: %s", exc)
        return "Unknown"


def get_network_info(shared_client: "speedtest.Speedtest | None" = None) -> NetworkInfo:
    """
    Gather ISP/server/location metadata using speedtest-cli's server
    discovery and configuration results, plus local network-type
    detection via psutil.
    """
    try:
        client = shared_client or speedtest.Speedtest()
        if shared_client is None:
            client.get_best_server()

        config = client.config
        best = client.results.server or client.get_best_server()

        info = NetworkInfo(
            isp=config.get("client", {}).get("isp", "Unknown"),
            ip_address=config.get("client", {}).get("ip", "Unknown"),
            server_name=best.get("sponsor", "Unknown"),
            server_location=f"{best.get('name', '')}, {best.get('country', '')}".strip(", "),
            country=config.get("client", {}).get("country", "Unknown"),
            region=best.get("region", "Unknown") if isinstance(best, dict) else "Unknown",
            city=best.get("name", "Unknown"),
            network_type=detect_network_type(),
        )
        logger.info(
            "Network info detected: ISP=%s IP=%s Server=%s",
            info.isp,
            info.ip_address,
            info.server_name,
        )
        return info
    except Exception as exc:
        logger.error("Failed to retrieve network info: %s", exc)
        return NetworkInfo(network_type=detect_network_type())
