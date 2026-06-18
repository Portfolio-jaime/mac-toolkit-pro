from pathlib import Path
from unittest.mock import patch
from mac_toolkit_pro.analyzers.trash import TrashAnalyzer

def test_trash_empty_or_missing():
    with patch("mac_toolkit_pro.analyzers.trash.TRASH_DIR", Path("/nonexistent/.Trash")):
        result = TrashAnalyzer().analyze()
    assert result.domain == "trash"
    assert result.total_size_bytes == 0
    assert result.items == []

def test_trash_with_files(tmp_path):
    trash = tmp_path / ".Trash"
    trash.mkdir()
    (trash / "oldfile.dmg").write_bytes(b"x" * 1024 * 1024 * 200)
    with patch("mac_toolkit_pro.analyzers.trash.TRASH_DIR", trash):
        result = TrashAnalyzer().analyze()
    assert result.total_size_bytes >= 200 * 1024 * 1024
    assert len(result.items) == 1
    assert result.items[0].risk == "warn"
    assert result.items[0].safe_to_delete is False
    assert result.items[0].path == trash
