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
