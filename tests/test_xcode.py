from pathlib import Path
from unittest.mock import patch

from mac_toolkit_pro.analyzers.xcode import XcodeAnalyzer


def test_xcode_not_installed():
    with patch("mac_toolkit_pro.analyzers.xcode.XCODE_PATHS",
               {k: Path("/nonexistent") for k in ("derived_data", "archives", "simulators")}):
        result = XcodeAnalyzer().analyze()
    assert result.domain == "xcode"
    assert result.total_size_bytes == 0
    assert result.items == []
    assert "not installed" in result.summary


def test_xcode_derived_data_found(tmp_path):
    dd = tmp_path / "DerivedData"
    dd.mkdir()
    (dd / "MyApp").mkdir()
    (dd / "MyApp" / "Build").write_bytes(b"x" * 1024 * 1024 * 50)  # 50 MB

    with patch("mac_toolkit_pro.analyzers.xcode.XCODE_PATHS", {
        "derived_data": dd,
        "archives": Path("/no"),
        "simulators": Path("/no"),
    }):
        result = XcodeAnalyzer().analyze()

    assert result.total_size_bytes > 0
    assert any(i.risk == "safe" for i in result.items)


def test_xcode_archives_risk_warn(tmp_path):
    arch = tmp_path / "Archives"
    arch.mkdir()
    (arch / "MyApp.xcarchive").mkdir()
    (arch / "MyApp.xcarchive" / "data").write_bytes(b"x" * 1024 * 1024 * 10)

    with patch("mac_toolkit_pro.analyzers.xcode.XCODE_PATHS", {
        "derived_data": Path("/no"),
        "archives": arch,
        "simulators": Path("/no"),
    }):
        result = XcodeAnalyzer().analyze()

    assert any(i.risk == "warn" for i in result.items)
