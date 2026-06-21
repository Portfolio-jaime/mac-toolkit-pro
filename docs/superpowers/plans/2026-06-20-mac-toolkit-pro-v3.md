# Mac Toolkit Pro v3 — Monitors + Interactive Menu

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate 4 legacy monitoring scripts (battery, system, processes, network) into `mac_toolkit_pro/monitors/`, expose them as `toolkit battery|system|processes|network` CLI commands, and add an interactive menu when `toolkit` is run with no arguments.

**Architecture:** Each legacy script becomes a `BaseMonitor` subclass with a `snapshot() -> dict` method plus a `display()` method using Rich. The CLI gains 4 new sub-commands that call `display()`. `menu.py` provides a `questionary` top-level selector. `cli()` invokes `show_menu()` when no subcommand is given.

**Tech Stack:** Python 3.10+, `click`, `rich`, `questionary`, `psutil`, `subprocess` (stdlib), `urllib` (replaces `requests`)

---

## Chunk 1: Foundation

### Task 1: Add psutil to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `psutil>=5.9` to dependencies**

In `pyproject.toml`, change the `dependencies` list to:
```toml
dependencies = [
    "click>=8.1",
    "rich>=13.0",
    "questionary>=2.0",
    "psutil>=5.9",
]
```

- [ ] **Step 2: Reinstall in editable mode**

```bash
pip install -e .
python -c "import psutil; print(psutil.__version__)"
```
Expected: version string printed without error.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add psutil to pyproject.toml dependencies"
```

---

### Task 2: Create monitors package with BaseMonitor

**Files:**
- Create: `mac_toolkit_pro/monitors/__init__.py`
- Create: `mac_toolkit_pro/monitors/base.py`
- Create: `tests/test_monitors_base.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_monitors_base.py`:
```python
import pytest
from mac_toolkit_pro.monitors.base import BaseMonitor


class ConcreteMonitor(BaseMonitor):
    name = "test"

    def snapshot(self):
        return {"value": 42}

    def display(self):
        pass


def test_base_monitor_has_name():
    m = ConcreteMonitor()
    assert m.name == "test"


def test_base_monitor_snapshot_returns_dict():
    m = ConcreteMonitor()
    result = m.snapshot()
    assert isinstance(result, dict)
    assert result["value"] == 42


def test_base_monitor_cannot_instantiate_directly():
    with pytest.raises(TypeError):
        BaseMonitor()
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/test_monitors_base.py -v
```
Expected: `ModuleNotFoundError: No module named 'mac_toolkit_pro.monitors'`

- [ ] **Step 3: Create the package**

Create `mac_toolkit_pro/monitors/__init__.py` (empty):
```python
```

Create `mac_toolkit_pro/monitors/base.py`:
```python
from abc import ABC, abstractmethod


class BaseMonitor(ABC):
    name: str = ""

    @abstractmethod
    def snapshot(self) -> dict:
        ...

    @abstractmethod
    def display(self) -> None:
        ...
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/test_monitors_base.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add mac_toolkit_pro/monitors/__init__.py mac_toolkit_pro/monitors/base.py tests/test_monitors_base.py
git commit -m "feat(monitors): add BaseMonitor ABC and monitors package"
```

---

## Chunk 2: Battery + System Monitors

### Task 3: BatteryMonitor

**Files:**
- Create: `mac_toolkit_pro/monitors/battery.py`
- Create: `tests/test_monitor_battery.py`

Key data sources from `mac_battery_analyzer.py`:
- `system_profiler SPPowerDataType -json` → capacity, charging state
- `ioreg -rn AppleSmartBattery` → CycleCount, MaxCapacity, DesignCapacity, Temperature, Voltage
- `pmset -g batt` → percentage string, time remaining

- [ ] **Step 1: Write the failing test**

Create `tests/test_monitor_battery.py`:
```python
from unittest.mock import patch, MagicMock
from mac_toolkit_pro.monitors.battery import BatteryMonitor


def test_battery_monitor_name():
    assert BatteryMonitor.name == "battery"


def test_battery_snapshot_returns_required_keys():
    monitor = BatteryMonitor()
    mock_ioreg = """
  "CycleCount" = 120
  "MaxCapacity" = 8500
  "DesignCapacity" = 9000
  "CurrentCapacity" = 6000
  "Temperature" = 2950
  "Voltage" = 12100
  "IsCharging" = No
"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_ioreg)
        result = monitor.snapshot()

    assert "cycle_count" in result
    assert "health_percent" in result
    assert "temperature_c" in result
    assert "is_charging" in result


def test_battery_health_calculation():
    monitor = BatteryMonitor()
    health = monitor._calc_health(max_cap=8500, design_cap=9000)
    assert round(health, 1) == round(8500 / 9000 * 100, 1)
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/test_monitor_battery.py -v
```
Expected: `ModuleNotFoundError: mac_toolkit_pro.monitors.battery`

- [ ] **Step 3: Implement BatteryMonitor**

Create `mac_toolkit_pro/monitors/battery.py`:
```python
from __future__ import annotations
import re
import subprocess
from typing import Optional
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
            "is_charging": "yes" in raw.get("is_charging_raw", "").lower() or
                           "true" in raw.get("is_charging_raw", "").lower(),
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
            ("Cycles", str(data.get("cycle_count", "—"))),
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
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/test_monitor_battery.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add mac_toolkit_pro/monitors/battery.py tests/test_monitor_battery.py
git commit -m "feat(monitors): add BatteryMonitor with ioreg + pmset snapshot"
```

---

### Task 4: SystemMonitor

**Files:**
- Create: `mac_toolkit_pro/monitors/system.py`
- Create: `tests/test_monitor_system.py`

Key data: `psutil` for CPU%, memory, swap; `pmset -g therm` for thermal state; `system_profiler SPHardwareDataType -json` for chip/model.

- [ ] **Step 1: Write the failing test**

Create `tests/test_monitor_system.py`:
```python
from unittest.mock import patch, MagicMock
from mac_toolkit_pro.monitors.system import SystemMonitor


def test_system_monitor_name():
    assert SystemMonitor.name == "system"


def test_system_snapshot_returns_required_keys():
    monitor = SystemMonitor()
    with patch("psutil.cpu_percent", return_value=23.5), \
         patch("psutil.virtual_memory") as mock_vm, \
         patch("psutil.swap_memory") as mock_swap, \
         patch("subprocess.run") as mock_run:
        mock_vm.return_value = MagicMock(
            total=16 * 1024**3, used=8 * 1024**3,
            available=8 * 1024**3, percent=50.0
        )
        mock_swap.return_value = MagicMock(
            total=2 * 1024**3, used=512 * 1024**2, percent=25.0
        )
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        result = monitor.snapshot()

    assert "cpu_percent" in result
    assert "memory_used_gb" in result
    assert "memory_percent" in result
    assert "swap_used_gb" in result
    assert result["cpu_percent"] == 23.5
    assert result["memory_percent"] == 50.0


def test_system_snapshot_formats_gb():
    monitor = SystemMonitor()
    with patch("psutil.cpu_percent", return_value=0.0), \
         patch("psutil.virtual_memory") as mock_vm, \
         patch("psutil.swap_memory") as mock_swap, \
         patch("subprocess.run") as mock_run:
        mock_vm.return_value = MagicMock(
            total=16 * 1024**3, used=4 * 1024**3,
            available=12 * 1024**3, percent=25.0
        )
        mock_swap.return_value = MagicMock(
            total=0, used=0, percent=0.0
        )
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        result = monitor.snapshot()

    assert result["memory_used_gb"] == round(4 * 1024**3 / 1024**3, 1)
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/test_monitor_system.py -v
```
Expected: `ModuleNotFoundError: mac_toolkit_pro.monitors.system`

- [ ] **Step 3: Implement SystemMonitor**

Create `mac_toolkit_pro/monitors/system.py`:
```python
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
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/test_monitor_system.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Wire battery + system CLI commands (failing test first)**

Add to `tests/test_cli_monitors.py`:
```python
from click.testing import CliRunner
from mac_toolkit_pro.cli import cli
from unittest.mock import patch, MagicMock


def test_battery_command_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["battery", "--help"])
    assert result.exit_code == 0
    assert "battery" in result.output.lower()


def test_system_command_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["system", "--help"])
    assert result.exit_code == 0
    assert "system" in result.output.lower()
```

Run to verify FAIL:
```bash
pytest tests/test_cli_monitors.py -v
```
Expected: `No such command 'battery'` / `No such command 'system'`

- [ ] **Step 6: Add battery and system commands to cli.py**

In `mac_toolkit_pro/cli.py`, add after the `full` command:

```python
@cli.command()
def battery():
    """Show battery health, cycles and charge status."""
    from mac_toolkit_pro.monitors.battery import BatteryMonitor
    BatteryMonitor().display()


@cli.command()
def system():
    """Show CPU, memory and thermal state."""
    from mac_toolkit_pro.monitors.system import SystemMonitor
    SystemMonitor().display()
```

- [ ] **Step 7: Run to verify PASS**

```bash
pytest tests/test_cli_monitors.py -v
```
Expected: 2 passed.

- [ ] **Step 8: Commit**

```bash
git add mac_toolkit_pro/monitors/system.py tests/test_monitor_system.py \
        tests/test_cli_monitors.py mac_toolkit_pro/cli.py
git commit -m "feat(monitors): add SystemMonitor + battery/system CLI commands"
```

---

## Chunk 3: Process + Network Monitors

### Task 5: ProcessMonitor

**Files:**
- Create: `mac_toolkit_pro/monitors/processes.py`
- Create: `tests/test_monitor_processes.py`

Key data from `mac_process_manager.py`: `psutil.process_iter` for top-CPU / top-memory; `psutil.virtual_memory()` for pressure; `memory_pressure` command.

- [ ] **Step 1: Write the failing test**

Create `tests/test_monitor_processes.py`:
```python
from unittest.mock import patch, MagicMock
from mac_toolkit_pro.monitors.processes import ProcessMonitor


def test_process_monitor_name():
    assert ProcessMonitor.name == "processes"


def test_top_cpu_returns_list():
    monitor = ProcessMonitor()
    mock_proc = MagicMock()
    mock_proc.info = {
        "pid": 123, "name": "python", "cpu_percent": 45.0,
        "memory_percent": 2.5, "create_time": 1700000000.0, "username": "user"
    }
    with patch("psutil.process_iter", return_value=[mock_proc]):
        result = monitor.top_by_cpu(limit=5)
    assert isinstance(result, list)
    assert result[0]["name"] == "python"
    assert result[0]["cpu_percent"] == 45.0


def test_top_memory_returns_list():
    monitor = ProcessMonitor()
    mock_proc = MagicMock()
    mock_proc.info = {
        "pid": 456, "name": "chrome", "cpu_percent": 5.0,
        "memory_percent": 15.0,
        "memory_info": MagicMock(rss=500 * 1024**2),
        "create_time": 1700000000.0, "username": "user"
    }
    with patch("psutil.process_iter", return_value=[mock_proc]):
        result = monitor.top_by_memory(limit=5)
    assert isinstance(result, list)
    assert result[0]["name"] == "chrome"


def test_snapshot_has_required_keys():
    monitor = ProcessMonitor()
    mock_proc = MagicMock()
    mock_proc.info = {
        "pid": 1, "name": "idle", "cpu_percent": 0.0,
        "memory_percent": 0.1, "create_time": 1700000000.0, "username": "root"
    }
    with patch("psutil.process_iter", return_value=[mock_proc]), \
         patch("psutil.virtual_memory") as mock_vm, \
         patch("subprocess.run") as mock_run:
        mock_vm.return_value = MagicMock(percent=40.0)
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        result = monitor.snapshot()
    assert "top_cpu" in result
    assert "top_memory" in result
    assert "memory_percent" in result
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/test_monitor_processes.py -v
```

- [ ] **Step 3: Implement ProcessMonitor**

Create `mac_toolkit_pro/monitors/processes.py`:
```python
from __future__ import annotations
import time
import subprocess
import psutil
from typing import Optional
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

        def _proc_table(procs: list[dict], title: str, sort_key: str) -> None:
            table = Table(title=title, box=box.ROUNDED)
            table.add_column("PID", width=7)
            table.add_column("Name")
            table.add_column("CPU%", justify="right", width=7)
            table.add_column("Mem%", justify="right", width=7)
            table.add_column("User", style="dim")
            for p in procs[:10]:
                cpu = p.get("cpu_percent", 0)
                mem = p.get("memory_percent", 0)
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
        console.print(f"\n[bold]Memory pressure:[/] [{mem_c}]{mem_pct}%[/]")
        _proc_table(data["top_cpu"], "Top CPU Consumers", "cpu_percent")
        _proc_table(data["top_memory"], "Top Memory Consumers", "memory_percent")
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/test_monitor_processes.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add mac_toolkit_pro/monitors/processes.py tests/test_monitor_processes.py
git commit -m "feat(monitors): add ProcessMonitor with top CPU/memory tables"
```

---

### Task 6: NetworkMonitor (no `requests`)

**Files:**
- Create: `mac_toolkit_pro/monitors/network.py`
- Create: `tests/test_monitor_network.py`

Replace `requests` with `urllib.request`. Key data: `psutil.net_io_counters()`, `psutil.net_connections()`, `ifconfig` output, `airport -I` for WiFi.

- [ ] **Step 1: Write the failing test**

Create `tests/test_monitor_network.py`:
```python
from unittest.mock import patch, MagicMock
from mac_toolkit_pro.monitors.network import NetworkMonitor


def test_network_monitor_name():
    assert NetworkMonitor.name == "network"


def test_snapshot_returns_required_keys():
    monitor = NetworkMonitor()
    mock_counters = MagicMock()
    mock_counters.bytes_sent = 1_000_000
    mock_counters.bytes_recv = 5_000_000
    mock_counters.packets_sent = 1000
    mock_counters.packets_recv = 5000

    with patch("psutil.net_io_counters", return_value=mock_counters), \
         patch("psutil.net_connections", return_value=[]), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = monitor.snapshot()

    assert "bytes_sent_mb" in result
    assert "bytes_recv_mb" in result
    assert "active_connections" in result
    assert "wifi" in result


def test_snapshot_converts_bytes_to_mb():
    monitor = NetworkMonitor()
    mock_counters = MagicMock()
    mock_counters.bytes_sent = 10 * 1024 * 1024   # 10 MB
    mock_counters.bytes_recv = 50 * 1024 * 1024   # 50 MB
    mock_counters.packets_sent = 100
    mock_counters.packets_recv = 500

    with patch("psutil.net_io_counters", return_value=mock_counters), \
         patch("psutil.net_connections", return_value=[]), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = monitor.snapshot()

    assert result["bytes_sent_mb"] == round(10.0, 2)
    assert result["bytes_recv_mb"] == round(50.0, 2)


def test_no_requests_import():
    import mac_toolkit_pro.monitors.network as net_mod
    import sys
    assert "requests" not in sys.modules or \
           "requests" not in open(net_mod.__file__).read(), \
           "network.py must not import 'requests'"
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/test_monitor_network.py -v
```

- [ ] **Step 3: Implement NetworkMonitor**

Create `mac_toolkit_pro/monitors/network.py`:
```python
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


_AIRPORT = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"


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
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/test_monitor_network.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Wire processes + network CLI commands**

Add to `tests/test_cli_monitors.py` (existing file):
```python
def test_processes_command_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["processes", "--help"])
    assert result.exit_code == 0


def test_network_command_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["network", "--help"])
    assert result.exit_code == 0
```

Run to verify FAIL:
```bash
pytest tests/test_cli_monitors.py::test_processes_command_exists tests/test_cli_monitors.py::test_network_command_exists -v
```

- [ ] **Step 6: Add processes and network commands to cli.py**

In `mac_toolkit_pro/cli.py`, append after `system` command:

```python
@cli.command()
def processes():
    """Show top CPU and memory consuming processes."""
    from mac_toolkit_pro.monitors.processes import ProcessMonitor
    ProcessMonitor().display()


@cli.command()
def network():
    """Show network stats, WiFi info and connectivity."""
    from mac_toolkit_pro.monitors.network import NetworkMonitor
    NetworkMonitor().display()
```

- [ ] **Step 7: Run all monitor tests**

```bash
pytest tests/test_monitor_battery.py tests/test_monitor_system.py \
       tests/test_monitor_processes.py tests/test_monitor_network.py \
       tests/test_cli_monitors.py -v
```
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add mac_toolkit_pro/monitors/network.py tests/test_monitor_network.py \
        tests/test_cli_monitors.py mac_toolkit_pro/cli.py
git commit -m "feat(monitors): add NetworkMonitor + processes/network CLI commands"
```

---

## Chunk 4: Interactive Menu

### Task 7: menu.py with questionary

**Files:**
- Create: `mac_toolkit_pro/menu.py`
- Create: `tests/test_menu.py`
- Modify: `mac_toolkit_pro/cli.py` — `cli()` calls `show_menu()` when no subcommand

- [ ] **Step 1: Write the failing test**

Create `tests/test_menu.py`:
```python
from unittest.mock import patch
from mac_toolkit_pro.menu import MENU_CHOICES, show_menu


def test_menu_choices_not_empty():
    assert len(MENU_CHOICES) > 0


def test_menu_choices_have_required_keys():
    for choice in MENU_CHOICES:
        assert "name" in choice
        assert "value" in choice


def test_menu_includes_monitors():
    values = [c["value"] for c in MENU_CHOICES]
    assert "battery" in values
    assert "system" in values
    assert "processes" in values
    assert "network" in values


def test_menu_includes_toolkit_actions():
    values = [c["value"] for c in MENU_CHOICES]
    assert "analyze" in values
    assert "clean" in values


def test_show_menu_exits_on_quit(capsys):
    with patch("questionary.select") as mock_select:
        mock_select.return_value.ask.return_value = "quit"
        show_menu()
    # No exception = success
```

- [ ] **Step 2: Run to verify FAIL**

```bash
pytest tests/test_menu.py -v
```
Expected: `ModuleNotFoundError: mac_toolkit_pro.menu`

- [ ] **Step 3: Implement menu.py**

Create `mac_toolkit_pro/menu.py`:
```python
from __future__ import annotations
import questionary
from mac_toolkit_pro.reporters.terminal import console

MENU_CHOICES = [
    {"name": "🔍 Analyze disk (all domains)", "value": "analyze"},
    {"name": "🧹 Clean disk (interactive)", "value": "clean"},
    {"name": "📊 Full flow (analyze + clean)", "value": "full"},
    {"name": "📋 Domain status", "value": "status"},
    {"name": "─── Monitors ───────────────", "value": "sep", "disabled": True},
    {"name": "🔋 Battery health", "value": "battery"},
    {"name": "💻 System (CPU / memory)", "value": "system"},
    {"name": "⚙️  Processes (top CPU / mem)", "value": "processes"},
    {"name": "🌐 Network", "value": "network"},
    {"name": "─── ────────────────────────", "value": "sep2", "disabled": True},
    {"name": "❌ Quit", "value": "quit"},
]

_CLEAN_CHOICES = [c for c in MENU_CHOICES if not c.get("disabled")]


def show_menu() -> None:
    console.print("\n[bold cyan]Mac DevOps Toolkit Pro[/] — choose an action\n")

    choice = questionary.select(
        "What would you like to do?",
        choices=[c["name"] for c in _CLEAN_CHOICES],
    ).ask()

    if choice is None or "Quit" in (choice or ""):
        return

    # resolve value from label
    value = next((c["value"] for c in _CLEAN_CHOICES if c["name"] == choice), None)
    if not value or value == "quit":
        return

    _dispatch(value)


def _dispatch(action: str) -> None:
    if action == "analyze":
        from mac_toolkit_pro.core.runner import run_analyzers
        from mac_toolkit_pro.cli import ALL_ANALYZERS
        from mac_toolkit_pro.reporters import terminal
        with console.status("[dim]Scanning...[/]"):
            results = run_analyzers(ALL_ANALYZERS)
        terminal.print_summary(results)

    elif action == "clean":
        from mac_toolkit_pro.core.runner import run_analyzers
        from mac_toolkit_pro.core.approval import ApprovalEngine
        from mac_toolkit_pro.cleaners.generic import GenericCleaner
        from mac_toolkit_pro.reporters import terminal, audit
        from mac_toolkit_pro.cli import ALL_ANALYZERS
        from mac_toolkit_pro.core.config import REPORTS_DIR
        from datetime import datetime
        with console.status("[dim]Scanning...[/]"):
            results = run_analyzers(ALL_ANALYZERS)
        terminal.print_summary(results)
        engine = ApprovalEngine(mode="checklist", dry_run=True, execute=False)
        approved = engine.get_approved_items(results)
        if approved:
            terminal.print_preview_table(approved)
            confirm = questionary.confirm(
                f"Delete {len(approved)} items? (runs in DRY-RUN — add --execute to cli for real deletions)"
            ).ask()
            if confirm:
                cleaner = GenericCleaner(dry_run=True, execute=False)
                cleaner.clean(approved)

    elif action == "full":
        from mac_toolkit_pro.core.runner import run_analyzers
        from mac_toolkit_pro.reporters import terminal
        from mac_toolkit_pro.cli import ALL_ANALYZERS
        with console.status("[dim]Running full analysis...[/]"):
            results = run_analyzers(ALL_ANALYZERS)
        terminal.print_summary(results)

    elif action == "status":
        from mac_toolkit_pro.cli import cli
        from click.testing import CliRunner
        CliRunner().invoke(cli, ["status"], catch_exceptions=False)

    elif action == "battery":
        from mac_toolkit_pro.monitors.battery import BatteryMonitor
        BatteryMonitor().display()

    elif action == "system":
        from mac_toolkit_pro.monitors.system import SystemMonitor
        SystemMonitor().display()

    elif action == "processes":
        from mac_toolkit_pro.monitors.processes import ProcessMonitor
        ProcessMonitor().display()

    elif action == "network":
        from mac_toolkit_pro.monitors.network import NetworkMonitor
        NetworkMonitor().display()
```

- [ ] **Step 4: Run to verify PASS**

```bash
pytest tests/test_menu.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Wire `toolkit` (no args) → show_menu**

The goal: `toolkit` with no subcommand launches the interactive menu. The cleanest way is to override `cli.invoke()` with `invoke_without_command=True`.

In `mac_toolkit_pro/cli.py`, change the `cli` group definition from:
```python
@click.group()
def cli():
    """🖥  Mac DevOps Toolkit Pro — Disk analysis and safe cleanup."""
    pass
```

to:
```python
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """🖥  Mac DevOps Toolkit Pro — Disk analysis and safe cleanup."""
    if ctx.invoked_subcommand is None:
        from mac_toolkit_pro.menu import show_menu
        show_menu()
```

- [ ] **Step 6: Write test for no-args behavior**

Add to `tests/test_menu.py`:
```python
from click.testing import CliRunner
from mac_toolkit_pro.cli import cli
from unittest.mock import patch


def test_toolkit_no_args_calls_show_menu():
    runner = CliRunner()
    with patch("mac_toolkit_pro.menu.show_menu") as mock_menu:
        mock_menu.return_value = None
        result = runner.invoke(cli, [])
    mock_menu.assert_called_once()
```

Run to verify:
```bash
pytest tests/test_menu.py -v
```
Expected: all 6 pass.

- [ ] **Step 7: Commit**

```bash
git add mac_toolkit_pro/menu.py tests/test_menu.py mac_toolkit_pro/cli.py
git commit -m "feat(menu): add interactive menu, launch on toolkit with no args"
```

---

### Task 8: Final integration check + push

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -20
```
Expected: all tests pass (target: 40+ tests).

- [ ] **Step 2: Smoke test the CLI**

```bash
toolkit --help
toolkit status
toolkit battery
toolkit system
```
Verify each command shows its Rich table output without errors.

- [ ] **Step 3: Update README monitors section**

In `README.md`, add a "Monitors" section after "Comandos":

```markdown
## Monitors

| Comando | Descripción |
|---------|-------------|
| `toolkit battery` | Salud, ciclos, temperatura y estado de carga |
| `toolkit system` | CPU, memoria, swap y estado térmico |
| `toolkit processes` | Top procesos por CPU y memoria |
| `toolkit network` | WiFi, estadísticas de red y conectividad |

Ejecutar `toolkit` sin argumentos abre el menú interactivo.
```

- [ ] **Step 4: Commit and push**

```bash
git add README.md
git commit -m "docs: add v3 monitors section to README"
git push origin main
```

---

## Summary

| Chunk | Tasks | New Files | Tests |
|-------|-------|-----------|-------|
| 1 — Foundation | 1-2 | `monitors/__init__.py`, `monitors/base.py` | 3 |
| 2 — Battery + System | 3-4 | `monitors/battery.py`, `monitors/system.py` | 6 + 2 CLI |
| 3 — Processes + Network | 5-6 | `monitors/processes.py`, `monitors/network.py` | 8 + 2 CLI |
| 4 — Menu | 7-8 | `menu.py` | 6 |

**Total new tests: ~27. Total suite after v3: ~60.**
