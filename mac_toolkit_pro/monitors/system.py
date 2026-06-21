from __future__ import annotations
import json
import subprocess
import psutil
from mac_toolkit_pro.monitors.base import BaseMonitor
from mac_toolkit_pro.reporters.terminal import console


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout if r.returncode == 0 else ""
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


class SystemMonitor(BaseMonitor):
    name = "system"

    def _hw_info(self) -> dict:
        out = _run(["system_profiler", "SPHardwareDataType", "-json"])
        try:
            data = json.loads(out)
            hw = data.get("SPHardwareDataType", [{}])[0]
            return {
                "model": hw.get("machine_name", "Unknown"),
                "chip": hw.get("chip_type", hw.get("cpu_type", "Unknown")),
                "cores": hw.get("number_processors", "Unknown"),
                "ram": hw.get("physical_memory", "Unknown"),
            }
        except (json.JSONDecodeError, IndexError):
            return {}

    def snapshot(self) -> dict:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        thermal = _run(["pmset", "-g", "therm"]).strip()
        hw = self._hw_info()

        return {
            "cpu_percent": cpu,
            "memory_total_gb": round(mem.total / 1024**3, 1),
            "memory_used_gb": round(mem.used / 1024**3, 1),
            "memory_available_gb": round(mem.available / 1024**3, 1),
            "memory_percent": mem.percent,
            "swap_total_gb": round(swap.total / 1024**3, 1),
            "swap_used_gb": round(swap.used / 1024**3, 1),
            "swap_percent": swap.percent,
            "thermal_state": thermal or "—",
            **hw,
        }

    def display(self) -> None:
        from rich.table import Table
        from rich import box
        data = self.snapshot()
        table = Table(title="System Status", box=box.ROUNDED, show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        cpu_color = "green" if data["cpu_percent"] < 60 else "yellow" if data["cpu_percent"] < 85 else "red"
        mem_color = "green" if data["memory_percent"] < 70 else "yellow" if data["memory_percent"] < 90 else "red"

        rows = [
            ("Model", f"{data.get('model', '—')} ({data.get('chip', '—')})"),
            ("Cores / RAM", f"{data.get('cores', '—')} / {data.get('ram', '—')}"),
            ("CPU usage", f"[{cpu_color}]{data['cpu_percent']}%[/]"),
            ("Memory", f"[{mem_color}]{data['memory_used_gb']} GB / {data['memory_total_gb']} GB ({data['memory_percent']}%)[/]"),
            ("Swap", f"{data['swap_used_gb']} GB / {data['swap_total_gb']} GB ({data['swap_percent']}%)"),
            ("Thermal", data.get("thermal_state", "—")),
        ]
        for k, v in rows:
            table.add_row(k, v)
        console.print(table)
