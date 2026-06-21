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
         patch("subprocess.run") as mock_run, \
         patch.object(monitor, "_test_connectivity", return_value=True):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = monitor.snapshot()

    assert "bytes_sent_mb" in result
    assert "bytes_recv_mb" in result
    assert "active_connections" in result
    assert "wifi" in result


def test_snapshot_converts_bytes_to_mb():
    monitor = NetworkMonitor()
    mock_counters = MagicMock()
    mock_counters.bytes_sent = 10 * 1024 * 1024
    mock_counters.bytes_recv = 50 * 1024 * 1024
    mock_counters.packets_sent = 100
    mock_counters.packets_recv = 500

    with patch("psutil.net_io_counters", return_value=mock_counters), \
         patch("psutil.net_connections", return_value=[]), \
         patch("subprocess.run") as mock_run, \
         patch.object(monitor, "_test_connectivity", return_value=False):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = monitor.snapshot()

    assert result["bytes_sent_mb"] == round(10.0, 2)
    assert result["bytes_recv_mb"] == round(50.0, 2)


def test_no_requests_import():
    import mac_toolkit_pro.monitors.network as net_mod
    source = open(net_mod.__file__).read()
    assert "import requests" not in source
    assert "from requests" not in source
