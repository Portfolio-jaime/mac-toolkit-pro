import os
import time
from pathlib import Path
from unittest.mock import patch

from mac_toolkit_pro.analyzers.dev_caches import DevCachesAnalyzer


def test_dev_caches_all_missing():
    with patch("mac_toolkit_pro.analyzers.dev_caches.DEV_CACHE_PATHS",
               {"npm": Path("/nonexistent/npm"), "pip": Path("/nonexistent/pip"),
                "brew": Path("/nonexistent/brew")}):
        result = DevCachesAnalyzer().analyze()
    assert result.domain == "dev_caches"
    assert result.total_size_bytes == 0
    assert result.items == []


def test_dev_caches_found_dir(tmp_path):
    cache = tmp_path / "npm"
    cache.mkdir()
    (cache / "file.bin").write_bytes(b"x" * 1024 * 1024)  # 1 MB

    with patch("mac_toolkit_pro.analyzers.dev_caches.DEV_CACHE_PATHS",
               {"npm": cache, "pip": Path("/no/pip"), "brew": Path("/no/brew")}):
        result = DevCachesAnalyzer().analyze()

    assert result.total_size_bytes >= 1024 * 1024
    assert len(result.items) == 1
    assert result.items[0].risk == "safe"
    assert result.items[0].safe_to_delete is True
    assert result.items[0].domain == "dev_caches"


def test_dev_caches_age_days_set(tmp_path):
    cache = tmp_path / "pip"
    cache.mkdir()
    f = cache / "pkg.whl"
    f.write_bytes(b"x" * 100)
    old = time.time() - 5 * 86400
    os.utime(f, (old, old))

    with patch("mac_toolkit_pro.analyzers.dev_caches.DEV_CACHE_PATHS",
               {"npm": Path("/no"), "pip": cache, "brew": Path("/no")}):
        result = DevCachesAnalyzer().analyze()

    assert result.items[0].age_days >= 5
