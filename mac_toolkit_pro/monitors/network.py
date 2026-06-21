from __future__ import annotations
import subprocess
import urllib.request
import psutil
from mac_toolkit_pro.monitors.base import BaseMonitor
from mac_toolkit_pro.reporters.terminal import console


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout if r.returncode == 0 else ""
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


_AIRPORT = (
    "/System/Library/PrivateFrameworks/Apple80211.framework"
    "/Versions/Current/Resources/airport"
)


class NetworkMonitor(BaseMonitor):
    name = "network"

    def _wifi_info(self) -> dict:
        out = _run([_AIRPORT, "-I"])
        if not out:
            return {}
        info: dict = {}
        for line in out.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                info[k.strip()] = v.strip()
        return info

    def _test_connectivity(self) -> bool:
        try:
            urllib.request.urlopen("https://www.apple.com", timeout=5)
            return True
        except Exception:
            return False

    def snapshot(self) -> dict:
        counters = psutil.net_io_counters()
        conns = psutil.net_connections()
        wifi = self._wifi_info()
        online = self._test_connectivity()

        established = [c for c in conns if c.status == "ESTABLISHED"]

        return {
            "bytes_sent_mb": round(counters.bytes_sent / 1024**2, 2),
            "bytes_recv_mb": round(counters.bytes_recv / 1024**2, 2),
            "packets_sent": counters.packets_sent,
            "packets_recv": counters.packets_recv,
            "active_connections": len(established),
            "total_connections": len(conns),
            "wifi": {
                "ssid": wifi.get("SSID", "—"),
                "rssi": wifi.get("agrCtlRSSI", "—"),
                "channel": wifi.get("channel", "—"),
            },
            "online": online,
        }

    def display(self) -> None:
        from rich.table import Table
        from rich import box
        data = self.snapshot()

        table = Table(title="Network Status", box=box.ROUNDED, show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        online_str = "[green]Online[/]" if data["online"] else "[red]Offline[/]"
        wifi = data.get("wifi", {})

        rows = [
            ("Connectivity", online_str),
            ("WiFi SSID", wifi.get("ssid", "—")),
            ("WiFi RSSI", wifi.get("rssi", "—")),
            ("WiFi Channel", wifi.get("channel", "—")),
            ("Sent (total)", f"{data['bytes_sent_mb']} MB"),
            ("Received (total)", f"{data['bytes_recv_mb']} MB"),
            ("Packets sent", str(data["packets_sent"])),
            ("Packets recv", str(data["packets_recv"])),
            ("Active connections", str(data["active_connections"])),
            ("Total connections", str(data["total_connections"])),
        ]
        for k, v in rows:
            table.add_row(k, v)
        console.print(table)
