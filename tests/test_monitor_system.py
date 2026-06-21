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
