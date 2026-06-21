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
