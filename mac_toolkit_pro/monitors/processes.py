from __future__ import annotations
import time
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


class ProcessMonitor(BaseMonitor):
    name = "processes"

    def top_by_cpu(self, limit: int = 10) -> list[dict]:
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "create_time", "username"]):
            try:
                info = dict(p.info)
                info["age_s"] = time.time() - info.get("create_time", time.time())
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(procs, key=lambda x: x.get("cpu_percent", 0), reverse=True)[:limit]

    def top_by_memory(self, limit: int = 10) -> list[dict]:
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "memory_info", "create_time", "username"]):
            try:
                info = dict(p.info)
                info["age_s"] = time.time() - info.get("create_time", time.time())
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(procs, key=lambda x: x.get("memory_percent", 0), reverse=True)[:limit]

    def snapshot(self) -> dict:
        mem = psutil.virtual_memory()
        pressure = _run(["memory_pressure"]).strip()
        return {
            "top_cpu": self.top_by_cpu(),
            "top_memory": self.top_by_memory(),
            "memory_percent": mem.percent,
            "memory_pressure": pressure or "—",
        }

    def display(self) -> None:
        from rich.table import Table
        from rich import box
        data = self.snapshot()

        def _proc_table(procs: list[dict], title: str) -> None:
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("PID", width=7)
            table.add_column("Name")
            table.add_column("CPU%", justify="right", width=7)
            table.add_column("Mem%", justify="right", width=7)
            table.add_column("User", style="dim")
            for p in procs[:10]:
                cpu = p.get("cpu_percent", 0) or 0
                mem = p.get("memory_percent", 0) or 0
                cpu_c = "red" if cpu > 80 else "yellow" if cpu > 40 else "green"
                mem_c = "red" if mem > 10 else "yellow" if mem > 5 else "green"
                table.add_row(
                    str(p.get("pid", "?")),
                    str(p.get("name", "?")),
                    f"[{cpu_c}]{cpu:.1f}[/]",
                    f"[{mem_c}]{mem:.1f}[/]",
                    str(p.get("username", "?"))[:15],
                )
            console.print(table)

        mem_pct = data["memory_percent"]
        mem_c = "green" if mem_pct < 70 else "yellow" if mem_pct < 90 else "red"
        console.print(f"\n[bold]Memory:[/] [{mem_c}]{mem_pct}%[/]")
        _proc_table(data["top_cpu"], "Top CPU Consumers")
        _proc_table(data["top_memory"], "Top Memory Consumers")
