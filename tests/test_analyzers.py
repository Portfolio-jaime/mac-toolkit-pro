import os
import time
import pytest
from pathlib import Path
from mac_toolkit_pro.analyzers.disk import DiskAnalyzer
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.models import AnalysisResult


class _ConcreteAnalyzer(BaseAnalyzer):
    domain = "test"

    def analyze(self) -> AnalysisResult:
        return self._make_result([], 0, "ok")


def test_disk_analyzer_returns_result():
    result = DiskAnalyzer().analyze()
    assert result.domain == "disk"
    assert isinstance(result.total_size_bytes, int)
    assert result.summary != ""
    # On macOS: size > 0; on non-APFS environments: graceful error allowed
    assert result.total_size_bytes >= 0


def test_oldest_mtime_age_returns_none_for_missing_path(tmp_path):
    a = _ConcreteAnalyzer()
    assert a._oldest_mtime_age(tmp_path / "nonexistent") is None


def test_oldest_mtime_age_returns_int_for_existing_dir(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x")
    # Set mtime to 10 days ago
    old_time = time.time() - 10 * 86400
    os.utime(f, (old_time, old_time))
    a = _ConcreteAnalyzer()
    age = a._oldest_mtime_age(tmp_path)
    assert isinstance(age, int)
    assert age >= 10
