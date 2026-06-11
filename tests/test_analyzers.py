import pytest
from mac_toolkit_pro.analyzers.disk import DiskAnalyzer


def test_disk_analyzer_returns_result():
    result = DiskAnalyzer().analyze()
    assert result.domain == "disk"
    assert isinstance(result.total_size_bytes, int)
    assert result.summary != ""
    # On macOS: size > 0; on non-APFS environments: graceful error allowed
    assert result.total_size_bytes >= 0
