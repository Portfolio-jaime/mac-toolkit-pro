from __future__ import annotations
import re
import subprocess
from mac_toolkit_pro.monitors.base import BaseMonitor
from mac_toolkit_pro.reporters.terminal import console


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout if r.returncode == 0 else ""
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


class BatteryMonitor(BaseMonitor):
    name = "battery"

    def _parse_ioreg(self, output: str) -> dict:
        info: dict = {}
        patterns = {
            "cycle_count": (r'"CycleCount"\s*=\s*(\d+)', int),
            "max_capacity": (r'"MaxCapacity"\s*=\s*(\d+)', int),
            "design_capacity": (r'"DesignCapacity"\s*=\s*(\d+)', int),
            "current_capacity": (r'"CurrentCapacity"\s*=\s*(\d+)', int),
            "temperature_raw": (r'"Temperature"\s*=\s*(\d+)', int),
            "voltage_mv": (r'"Voltage"\s*=\s*(\d+)', int),
            "is_charging_raw": (r'"IsCharging"\s*=\s*(\w+)', str),
        }
        for key, (pat, cast) in patterns.items():
            m = re.search(pat, output)
            if m:
                info[key] = cast(m.group(1))
        return info

    def _calc_health(self, max_cap: int, design_cap: int) -> float:
        if design_cap == 0:
            return 0.0
        return max_cap / design_cap * 100

    def snapshot(self) -> dict:
        ioreg_out = _run(["ioreg", "-rn", "AppleSmartBattery"])
        raw = self._parse_ioreg(ioreg_out)

        max_cap = raw.get("max_capacity", 0)
        design_cap = raw.get("design_capacity", 0)
        temp_raw = raw.get("temperature_raw", 0)

        pmset_out = _run(["pmset", "-g", "batt"])
        percent_match = re.search(r"(\d+)%", pmset_out)
        time_match = re.search(r"(\d+:\d+) remaining", pmset_out)

        return {
            "cycle_count": raw.get("cycle_count"),
            "max_capacity_mah": max_cap,
            "design_capacity_mah": design_cap,
            "health_percent": round(self._calc_health(max_cap, design_cap), 1),
            "current_percent": int(percent_match.group(1)) if percent_match else None,
            "time_remaining": time_match.group(1) if time_match else None,
            "temperature_c": round(temp_raw / 100.0, 1) if temp_raw else None,
            "voltage_v": round(raw.get("voltage_mv", 0) / 1000.0, 2),
            "is_charging": "yes" in raw.get("is_charging_raw", "").lower()
                           or "true" in raw.get("is_charging_raw", "").lower(),
        }

    def display(self) -> None:
        from rich.table import Table
        from rich import box
        data = self.snapshot()
        table = Table(title="Battery Status", box=box.ROUNDED, show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        health = data.get("health_percent", 0)
        health_color = "green" if health >= 80 else "yellow" if health >= 60 else "red"

        rows = [
            ("Health", f"[{health_color}]{health}%[/]"),
            ("Cycles", str(data.get("cycle_count") or "—")),
            ("Charge", f"{data.get('current_percent', '—')}%"),
            ("Charging", "Yes" if data.get("is_charging") else "No"),
            ("Time remaining", data.get("time_remaining") or "—"),
            ("Temperature", f"{data.get('temperature_c', '—')} °C"),
            ("Voltage", f"{data.get('voltage_v', '—')} V"),
            ("Max / Design", f"{data.get('max_capacity_mah')} / {data.get('design_capacity_mah')} mAh"),
        ]
        for k, v in rows:
            table.add_row(k, v)
        console.print(table)
