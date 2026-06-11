# Storage & Cleanup v2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `mac_toolkit_pro` with 3 new analyzers (dev_caches, xcode, trash), enrich `CleanableItem` with `risk`/`age_days`, and add `--domain`, `status`, and pre-delete preview to the CLI.

**Architecture:** All new code follows the existing `BaseAnalyzer` → `run_analyzers()` → `ApprovalEngine` → `GenericCleaner` pipeline. New fields on `CleanableItem` are backward-compatible (optional with safe defaults). CLI changes are additive flags/commands on the existing Click group.

**Tech Stack:** Python 3.10+, Click, Rich, pytest — no new dependencies.

**Spec:** `docs/superpowers/specs/2026-06-10-storage-cleanup-v2-design.md`

---

## Chunk 1: Foundation — models, base helper, config

### Task 1: Enrich `CleanableItem` with `risk` and `age_days`

**Files:**
- Modify: `mac_toolkit_pro/core/models.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_models.py`:

```python
from typing import get_args
from mac_toolkit_pro.core.models import CleanableItem, RiskLevel

def test_cleanable_item_risk_default():
    item = CleanableItem(
        path=Path("/tmp/x"), size_bytes=100, label="x",
        domain="test", safe_to_delete=True, reason="test",
    )
    assert item.risk == "safe"
    assert item.age_days is None

def test_cleanable_item_risk_values():
    for level in ("safe", "warn", "danger"):
        item = CleanableItem(
            path=Path("/tmp/x"), size_bytes=100, label="x",
            domain="test", safe_to_delete=True, reason="test",
            risk=level, age_days=30,
        )
        assert item.risk == level
        assert item.age_days == 30

def test_risk_level_literal():
    assert set(get_args(RiskLevel)) == {"safe", "warn", "danger"}
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/test_models.py::test_cleanable_item_risk_default tests/test_models.py::test_risk_level_literal -v
```
Expected: `ImportError` or `AssertionError` — `RiskLevel` and new fields don't exist yet.

- [ ] **Step 3: Implement**

Replace `mac_toolkit_pro/core/models.py` with:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

RiskLevel = Literal["safe", "warn", "danger"]


@dataclass
class CleanableItem:
    path: Path
    size_bytes: int
    label: str
    domain: str
    safe_to_delete: bool
    reason: str
    age_days: Optional[int] = None
    risk: RiskLevel = "safe"


@dataclass
class AnalysisResult:
    domain: str
    severity: str          # "critical" | "high" | "medium" | "low"
    total_size_bytes: int
    items: List[CleanableItem]
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


def severity_label(size_bytes: int) -> str:
    gb = size_bytes / (1024 ** 3)
    mb = size_bytes / (1024 ** 2)
    if gb > 10:
        return "critical"
    if gb > 1:
        return "high"
    if mb > 100:
        return "medium"
    return "low"
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_models.py -v
```
Expected: all pass (including the 4 pre-existing tests).

- [ ] **Step 5: Commit**

```bash
git add mac_toolkit_pro/core/models.py tests/test_models.py
git commit -m "feat(models): add age_days and risk fields to CleanableItem"
```

---

### Task 2: Add `_oldest_mtime_age` helper to `BaseAnalyzer`

**Files:**
- Modify: `mac_toolkit_pro/analyzers/base.py`
- Modify: `tests/test_analyzers.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_analyzers.py`:

```python
import os, time
from pathlib import Path
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.models import AnalysisResult


class _ConcreteAnalyzer(BaseAnalyzer):
    domain = "test"
    def analyze(self) -> AnalysisResult:
        return self._make_result([], 0, "ok")


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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_analyzers.py::test_oldest_mtime_age_returns_none_for_missing_path -v
```
Expected: `AttributeError: '_ConcreteAnalyzer' object has no attribute '_oldest_mtime_age'`

- [ ] **Step 3: Implement**

Replace `mac_toolkit_pro/analyzers/base.py` with:

```python
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from mac_toolkit_pro.core.models import AnalysisResult, CleanableItem, severity_label


class BaseAnalyzer(ABC):
    domain: str = "base"

    @abstractmethod
    def analyze(self) -> AnalysisResult:
        ...

    def _dir_size(self, path: Path) -> int:
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except OSError:
                        continue
        except PermissionError:
            pass
        return total

    def _oldest_mtime_age(self, path: Path) -> Optional[int]:
        """Age in days of the oldest file under path, or None if path missing."""
        if not path.exists():
            return None
        oldest: Optional[float] = None
        try:
            for f in path.rglob("*"):
                if f.is_file():
                    try:
                        mtime = f.stat().st_mtime
                        if oldest is None or mtime < oldest:
                            oldest = mtime
                    except OSError:
                        continue
        except (PermissionError, OSError):
            return None
        if oldest is None:
            return None
        return int((datetime.now().timestamp() - oldest) / 86400)

    def _make_result(self, items, total_size: int, summary: str) -> AnalysisResult:
        return AnalysisResult(
            domain=self.domain,
            severity=severity_label(total_size),
            total_size_bytes=total_size,
            items=items,
            summary=summary,
        )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_analyzers.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add mac_toolkit_pro/analyzers/base.py tests/test_analyzers.py
git commit -m "feat(base): add _oldest_mtime_age helper to BaseAnalyzer"
```

---

### Task 3: Add config constants for new domains

**Files:**
- Modify: `mac_toolkit_pro/core/config.py`

No dedicated tests needed (pure constants — tested implicitly by analyzer tests).

- [ ] **Step 1: Add constants**

Append to the bottom of `mac_toolkit_pro/core/config.py`:

```python
DEV_CACHE_PATHS = {
    "npm":  HOME / ".npm/_cacache",
    "pip":  HOME / "Library/Caches/pip",
    "brew": HOME / "Library/Caches/Homebrew",
}

XCODE_PATHS = {
    "derived_data": HOME / "Library/Developer/Xcode/DerivedData",
    "archives":     HOME / "Library/Developer/Xcode/Archives",
    "simulators":   HOME / "Library/Developer/CoreSimulator/Devices",
}

TRASH_DIR = HOME / ".Trash"
```

- [ ] **Step 2: Verify import**

```bash
python3 -c "from mac_toolkit_pro.core.config import DEV_CACHE_PATHS, XCODE_PATHS, TRASH_DIR; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add mac_toolkit_pro/core/config.py
git commit -m "feat(config): add DEV_CACHE_PATHS, XCODE_PATHS, TRASH_DIR constants"
```

---

## Chunk 2: Update existing analyzers with `risk=`

### Task 4: Add `risk=` to all 7 CleanableItem-creating analyzers

**Files (all Modify):**
- `mac_toolkit_pro/analyzers/ollama.py`
- `mac_toolkit_pro/analyzers/docker.py`
- `mac_toolkit_pro/analyzers/browser.py`
- `mac_toolkit_pro/analyzers/logs.py`
- `mac_toolkit_pro/analyzers/downloads.py`
- `mac_toolkit_pro/analyzers/appsupport.py`
- `mac_toolkit_pro/analyzers/repos.py`

Note: `disk.py` produces no `CleanableItem` objects — no change needed.

- [ ] **Step 1: Update `ollama.py`**

In `CleanableItem(...)` inside `analyze()`, add `risk="danger"` after `reason=`:

```python
items.append(CleanableItem(
    path=blob, size_bytes=size,
    label=blob.name[:20], domain=self.domain,
    safe_to_delete=False,
    reason="Ollama model blob — verify model is unused before deleting",
    risk="danger",
))
```

- [ ] **Step 2: Update `docker.py`**

In `_build_items()`, add `risk="danger"` after `reason=`:

```python
return [CleanableItem(
    path=_DOCKER_RAW, size_bytes=_DOCKER_RAW.stat().st_size,
    label="Docker.raw virtual disk",
    domain=self.domain, safe_to_delete=False,
    reason="Run 'docker system prune -a' to reclaim space inside Docker",
    risk="danger",
)]
```

- [ ] **Step 3: Update `browser.py`**

In `CleanableItem(...)` inside `analyze()`, add `risk="safe"` after `reason=`:

```python
items.append(CleanableItem(
    path=path, size_bytes=size,
    label=f"{browser} cache",
    domain=self.domain, safe_to_delete=True,
    reason=f"{browser} cache — safe to delete",
    risk="safe",
))
```

- [ ] **Step 4: Update `logs.py`**

`logs.py` already computes `age_days` locally (as an `int`). Add both `risk="safe"` and `age_days=age_days` so the value propagates to the preview table:

```python
items.append(CleanableItem(
    path=log_file, size_bytes=size,
    label=f"{log_file.name} ({age_days}d old)",
    domain=self.domain, safe_to_delete=True,
    reason=f"Log file {age_days} days old",
    risk="safe",
    age_days=age_days,
))
```

- [ ] **Step 5: Update `downloads.py`**

In `CleanableItem(...)` inside `analyze()`, add `risk="warn"` after `reason=`:

```python
items.append(CleanableItem(
    path=f, size_bytes=size,
    label=f.name, domain=self.domain,
    safe_to_delete=is_dup,
    reason=reason,
    risk="warn",
))
```

- [ ] **Step 6: Update `appsupport.py`**

In `CleanableItem(...)` inside `analyze()`, add `risk="warn"` after `reason=`:

```python
items.append(CleanableItem(
    path=app_dir, size_bytes=size,
    label=app_dir.name, domain=self.domain,
    safe_to_delete=False,
    reason="Application data — verify app is uninstalled before deleting",
    risk="warn",
))
```

- [ ] **Step 7: Update `repos.py`**

In `CleanableItem(...)` inside `analyze()`, add `risk="safe"` after `reason=`:

```python
items.append(CleanableItem(
    path=candidate, size_bytes=size,
    label=f"{candidate.parent.name}/{candidate.name}",
    domain=self.domain, safe_to_delete=True,
    reason=f"Reinstallable dependency dir ({candidate.name})",
    risk="safe",
))
```

- [ ] **Step 8: Run full test suite**

```bash
pytest tests/ -v
```
Expected: all existing tests pass. The `risk` default `"safe"` means nothing broke.

- [ ] **Step 9: Commit**

```bash
git add mac_toolkit_pro/analyzers/
git commit -m "feat(analyzers): add risk= to all existing CleanableItem instantiations"
```

---

## Chunk 3: New analyzers

### Task 5: `DevCachesAnalyzer`

**Files:**
- Create: `mac_toolkit_pro/analyzers/dev_caches.py`
- Create: `tests/test_dev_caches.py`

- [ ] **Step 1: Write tests**

Create `tests/test_dev_caches.py`:

```python
from pathlib import Path
from unittest.mock import patch, MagicMock
from mac_toolkit_pro.analyzers.dev_caches import DevCachesAnalyzer


def test_dev_caches_all_missing():
    """When no cache dirs exist, returns zero-size result with no items."""
    with patch("mac_toolkit_pro.analyzers.dev_caches.DEV_CACHE_PATHS",
               {"npm": Path("/nonexistent/npm"), "pip": Path("/nonexistent/pip"),
                "brew": Path("/nonexistent/brew")}):
        result = DevCachesAnalyzer().analyze()
    assert result.domain == "dev_caches"
    assert result.total_size_bytes == 0
    assert result.items == []


def test_dev_caches_found_dir(tmp_path):
    """When a cache dir exists with files, returns correct size and risk=safe."""
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
    """age_days is populated for existing dirs."""
    import os, time
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_dev_caches.py -v
```
Expected: `ModuleNotFoundError` — file doesn't exist yet.

- [ ] **Step 3: Implement**

Create `mac_toolkit_pro/analyzers/dev_caches.py`:

```python
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import DEV_CACHE_PATHS
from mac_toolkit_pro.core.models import CleanableItem


class DevCachesAnalyzer(BaseAnalyzer):
    domain = "dev_caches"

    def analyze(self):
        items = []
        total = 0
        for name, path in DEV_CACHE_PATHS.items():
            if not path.exists():
                continue
            size = self._dir_size(path)
            if size == 0:
                continue
            total += size
            items.append(CleanableItem(
                path=path, size_bytes=size,
                label=f"{name} cache",
                domain=self.domain, safe_to_delete=True,
                reason=f"{name} cache — auto-regenerated on next use",
                age_days=self._oldest_mtime_age(path),
                risk="safe",
            ))
        items.sort(key=lambda x: x.size_bytes, reverse=True)
        parts = [f"{i.label} {i.size_bytes/(1024**2):.0f}MB" for i in items]
        summary = ", ".join(parts) if parts else "No dev caches found"
        return self._make_result(items, total, summary)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_dev_caches.py -v
```
Expected: all 3 pass.

- [ ] **Step 5: Commit**

```bash
git add mac_toolkit_pro/analyzers/dev_caches.py tests/test_dev_caches.py
git commit -m "feat(analyzers): add DevCachesAnalyzer (npm, pip, brew)"
```

---

### Task 6: `XcodeAnalyzer`

**Files:**
- Create: `mac_toolkit_pro/analyzers/xcode.py`
- Create: `tests/test_xcode.py`

- [ ] **Step 1: Write tests**

Create `tests/test_xcode.py`:

```python
from pathlib import Path
from unittest.mock import patch
from mac_toolkit_pro.analyzers.xcode import XcodeAnalyzer


def test_xcode_not_installed():
    """When no Xcode paths exist, returns summary 'Xcode not installed'."""
    with patch("mac_toolkit_pro.analyzers.xcode.XCODE_PATHS",
               {k: Path("/nonexistent") for k in ("derived_data", "archives", "simulators")}):
        result = XcodeAnalyzer().analyze()
    assert result.domain == "xcode"
    assert result.total_size_bytes == 0
    assert result.items == []
    assert "not installed" in result.summary


def test_xcode_derived_data_found(tmp_path):
    """DerivedData items get risk=safe."""
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
    dd_items = [i for i in result.items if "derived" in i.label.lower() or "DerivedData" in str(i.path)]
    assert any(i.risk == "safe" for i in result.items)


def test_xcode_archives_risk_warn(tmp_path):
    """Archive items get risk=warn."""
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
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_xcode.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement**

Create `mac_toolkit_pro/analyzers/xcode.py`:

```python
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import XCODE_PATHS
from mac_toolkit_pro.core.models import CleanableItem

_RISK = {
    "derived_data": "safe",
    "simulators":   "safe",
    "archives":     "warn",
}

_LABELS = {
    "derived_data": "Xcode DerivedData",
    "simulators":   "iOS Simulators",
    "archives":     "Xcode Archives",
}


class XcodeAnalyzer(BaseAnalyzer):
    domain = "xcode"

    def analyze(self):
        items = []
        total = 0
        for key, path in XCODE_PATHS.items():
            if not path.exists():
                continue
            size = self._dir_size(path)
            if size == 0:
                continue
            total += size
            items.append(CleanableItem(
                path=path, size_bytes=size,
                label=_LABELS[key],
                domain=self.domain,
                safe_to_delete=(key != "archives"),
                reason=f"{_LABELS[key]} — {'safe to delete, Xcode regenerates' if key != 'archives' else 'verify archives are no longer needed'}",
                age_days=self._oldest_mtime_age(path),
                risk=_RISK[key],
            ))

        if not items:
            return self._make_result([], 0, "Xcode not installed")

        items.sort(key=lambda x: x.size_bytes, reverse=True)
        return self._make_result(items, total, f"Xcode: {total/(1024**3):.1f}GB across {len(items)} targets")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_xcode.py -v
```
Expected: all 3 pass.

- [ ] **Step 5: Commit**

```bash
git add mac_toolkit_pro/analyzers/xcode.py tests/test_xcode.py
git commit -m "feat(analyzers): add XcodeAnalyzer (DerivedData, Simulators, Archives)"
```

---

### Task 7: `TrashAnalyzer`

**Files:**
- Create: `mac_toolkit_pro/analyzers/trash.py`
- Create: `tests/test_trash.py`

- [ ] **Step 1: Write tests**

Create `tests/test_trash.py`:

```python
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
    (trash / "oldfile.dmg").write_bytes(b"x" * 1024 * 1024 * 200)  # 200 MB

    with patch("mac_toolkit_pro.analyzers.trash.TRASH_DIR", trash):
        result = TrashAnalyzer().analyze()

    assert result.total_size_bytes >= 200 * 1024 * 1024
    assert len(result.items) == 1
    assert result.items[0].risk == "warn"
    assert result.items[0].safe_to_delete is False
    assert result.items[0].path == trash
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_trash.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement**

Create `mac_toolkit_pro/analyzers/trash.py`:

```python
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import TRASH_DIR
from mac_toolkit_pro.core.models import CleanableItem


class TrashAnalyzer(BaseAnalyzer):
    domain = "trash"

    def analyze(self):
        if not TRASH_DIR.exists():
            return self._make_result([], 0, "Trash is empty")

        size = self._dir_size(TRASH_DIR)
        if size == 0:
            return self._make_result([], 0, "Trash is empty")

        item_count = sum(1 for _ in TRASH_DIR.iterdir())
        item = CleanableItem(
            path=TRASH_DIR, size_bytes=size,
            label=f"Trash ({item_count} items)",
            domain=self.domain, safe_to_delete=False,
            reason="Contents of ~/.Trash — equivalent to 'Empty Trash'",
            age_days=self._oldest_mtime_age(TRASH_DIR),
            risk="warn",
        )
        return self._make_result(
            [item], size,
            f"Trash: {size/(1024**2):.0f}MB in {item_count} items",
        )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_trash.py -v
```
Expected: both pass.

- [ ] **Step 5: Run full suite**

```bash
pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add mac_toolkit_pro/analyzers/trash.py tests/test_trash.py
git commit -m "feat(analyzers): add TrashAnalyzer"
```

---

## Chunk 4: CLI + reporter

### Task 8: Fix console singleton + wire new analyzers into `ALL_ANALYZERS`

**Files:**
- Modify: `mac_toolkit_pro/cli.py`

- [ ] **Step 1: Update imports and ALL_ANALYZERS**

In `mac_toolkit_pro/cli.py`:

1. Remove line 22: `console = Console()` — and remove `from rich.console import Console` import.
2. Add to imports block (after existing analyzer imports):

```python
from mac_toolkit_pro.analyzers.dev_caches import DevCachesAnalyzer
from mac_toolkit_pro.analyzers.xcode import XcodeAnalyzer
from mac_toolkit_pro.analyzers.trash import TrashAnalyzer
from mac_toolkit_pro.reporters.terminal import console
```

3. Add 3 entries to `ALL_ANALYZERS`:

```python
ALL_ANALYZERS = [
    DiskAnalyzer().analyze,
    OllamaAnalyzer().analyze,
    DockerAnalyzer().analyze,
    BrowserAnalyzer().analyze,
    LogsAnalyzer().analyze,
    DownloadsAnalyzer().analyze,
    AppSupportAnalyzer().analyze,
    ReposAnalyzer().analyze,
    DevCachesAnalyzer().analyze,   # new
    XcodeAnalyzer().analyze,       # new
    TrashAnalyzer().analyze,       # new
]
```

- [ ] **Step 2: Smoke test**

```bash
./toolkit --help
```
Expected: help text prints without error.

```bash
./toolkit analyze 2>&1 | head -20
```
Expected: runs and shows table (new domains appear even if `0B`).

- [ ] **Step 3: Commit**

```bash
git add mac_toolkit_pro/cli.py
git commit -m "feat(cli): wire DevCachesAnalyzer, XcodeAnalyzer, TrashAnalyzer into ALL_ANALYZERS; fix console singleton"
```

---

### Task 9: `--domain` flag on `analyze` and `clean`

**Files:**
- Modify: `mac_toolkit_pro/cli.py`
- Create: `tests/test_cli_domain.py`

- [ ] **Step 1: Write tests**

Create `tests/test_cli_domain.py`:

```python
from click.testing import CliRunner
from mac_toolkit_pro.cli import cli, ALL_ANALYZERS, _filter_analyzers


def test_filter_analyzers_none_returns_all():
    result = _filter_analyzers(None)
    assert result == ALL_ANALYZERS


def test_filter_analyzers_valid_domain():
    result = _filter_analyzers("disk")
    assert len(result) == 1
    assert result[0].__self__.domain == "disk"


def test_filter_analyzers_invalid_domain_raises():
    import click
    try:
        _filter_analyzers("nonexistent_domain")
        assert False, "Should have raised"
    except click.BadParameter:
        pass


def test_analyze_domain_flag_runs():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--domain", "disk"])
    assert result.exit_code == 0


def test_analyze_invalid_domain_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--domain", "fakefakefake"])
    assert result.exit_code != 0
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_cli_domain.py -v
```
Expected: `ImportError` — `_filter_analyzers` not defined yet.

- [ ] **Step 3: Implement**

Add `_filter_analyzers` function to `cli.py` (before the Click commands):

```python
import click as _click

def _filter_analyzers(domain):
    """Return analyzers filtered to a single domain, or all if domain is None."""
    if domain is None:
        return ALL_ANALYZERS
    valid = {fn.__self__.domain for fn in ALL_ANALYZERS}
    if domain not in valid:
        raise _click.BadParameter(
            f"Unknown domain '{domain}'. Valid: {', '.join(sorted(valid))}",
            param_hint="--domain",
        )
    return [fn for fn in ALL_ANALYZERS if fn.__self__.domain == domain]
```

Add `--domain` option to `analyze` command:

```python
@cli.command()
@click.option("--save", is_flag=True)
@click.option("--verbose", is_flag=True)
@click.option("--min-size", default=DEFAULT_MIN_SIZE_MB, show_default=True)
@click.option("--domain", default=None, help="Run only this domain (e.g. dev_caches)")
def analyze(save, verbose, min_size, domain):
    """Run full disk analysis across all domains in parallel."""
    analyzers = _filter_analyzers(domain)
    ...  # rest unchanged, replace ALL_ANALYZERS with analyzers
```

Add `--domain` option to `clean` command identically — replace `ALL_ANALYZERS` with `_filter_analyzers(domain)`.

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_cli_domain.py -v
```
Expected: all 5 pass.

- [ ] **Step 5: Manual smoke test**

```bash
./toolkit analyze --domain dev_caches
./toolkit clean --domain dev_caches
```
Expected: only `dev_caches` domain runs.

- [ ] **Step 6: Commit**

```bash
git add mac_toolkit_pro/cli.py tests/test_cli_domain.py
git commit -m "feat(cli): add --domain flag to analyze and clean commands"
```

---

### Task 10: `./toolkit status` command

**Files:**
- Modify: `mac_toolkit_pro/cli.py`

- [ ] **Step 1: Write test**

Add to `tests/test_cli_domain.py`:

```python
def test_status_command_runs():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "disk" in result.output.lower()
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_cli_domain.py::test_status_command_runs -v
```
Expected: `UsageError: No such command 'status'`

- [ ] **Step 3: Implement**

Add `import subprocess` and `import shutil` to top of `cli.py`.

Add this command to `cli.py`:

```python
@cli.command()
def status():
    """Quick storage snapshot — no full scan, results in under 3 seconds."""
    from rich.table import Table
    from rich import box as rbox

    usage = shutil.disk_usage("/")
    pct = int(usage.used / usage.total * 100)

    table = Table(title="🖥  Mac Storage Status", box=rbox.ROUNDED)
    table.add_column("Domain", style="bold cyan", width=14)
    table.add_column("Est. Size", justify="right", width=16)

    table.add_row("disk", f"{usage.used/(1024**3):.1f}GB / {usage.total/(1024**3):.1f}GB ({pct}%)")

    from mac_toolkit_pro.core.config import (
        OLLAMA_MODELS_DIR, DEV_CACHE_PATHS, XCODE_PATHS, TRASH_DIR
    )
    from pathlib import Path

    _DOCKER_RAW = Path.home() / "Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"

    quick_paths = [
        ("ollama",  OLLAMA_MODELS_DIR),
        ("docker",  _DOCKER_RAW),
        ("npm",     DEV_CACHE_PATHS["npm"]),
        ("pip",     DEV_CACHE_PATHS["pip"]),
        ("brew",    DEV_CACHE_PATHS["brew"]),
        ("xcode",   XCODE_PATHS["derived_data"]),
        ("trash",   TRASH_DIR),
    ]

    for name, path in quick_paths:
        if not path.exists():
            table.add_row(name, "[dim]not found[/]")
            continue
        try:
            if path.is_file():
                kb = path.stat().st_size // 1024
            else:
                r = subprocess.run(["du", "-sk", str(path)],
                                   capture_output=True, text=True, timeout=5)
                kb = int(r.stdout.split()[0])
            from mac_toolkit_pro.reporters.terminal import fmt_bytes
            table.add_row(name, fmt_bytes(kb * 1024))
        except Exception:
            table.add_row(name, "[dim]error[/]")

    console.print(table)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_cli_domain.py -v
```
Expected: all pass.

- [ ] **Step 5: Manual smoke test**

```bash
./toolkit status
```
Expected: table prints in <3 seconds.

- [ ] **Step 6: Commit**

```bash
git add mac_toolkit_pro/cli.py
git commit -m "feat(cli): add status command for fast storage snapshot"
```

---

### Task 11: Pre-delete preview table in reporter + `clean`/`full` commands

**Files:**
- Modify: `mac_toolkit_pro/reporters/terminal.py`
- Modify: `mac_toolkit_pro/cli.py`

- [ ] **Step 1: Write test for `print_preview_table`**

Add to `tests/test_models.py` (or create `tests/test_terminal.py`):

```python
from pathlib import Path
from io import StringIO
from rich.console import Console
from mac_toolkit_pro.core.models import CleanableItem
from mac_toolkit_pro.reporters.terminal import print_preview_table


def test_print_preview_table_renders(capsys):
    items = [
        CleanableItem(
            path=Path("/tmp/a.zip"), size_bytes=50 * 1024 * 1024,
            label="a.zip", domain="downloads", safe_to_delete=True,
            reason="archive", risk="warn", age_days=30,
        ),
        CleanableItem(
            path=Path("/tmp/b"), size_bytes=200 * 1024 * 1024,
            label="b", domain="dev_caches", safe_to_delete=True,
            reason="cache", risk="safe", age_days=None,
        ),
    ]
    buf = StringIO()
    c = Console(file=buf, force_terminal=False)
    print_preview_table(items, _console=c)   # note: _console, not console
    out = buf.getvalue()
    assert "a.zip" in out
    assert "warn" in out
    assert "safe" in out
    assert "30" in out   # age_days
    assert "—" in out    # None age_days
```

- [ ] **Step 2: Run to verify failure**

```bash
pytest tests/test_models.py::test_print_preview_table_renders -v
```
Expected: `ImportError` or `TypeError`.

- [ ] **Step 3: Add `print_preview_table` to `reporters/terminal.py`**

First, update the existing import line at the top of `terminal.py`:

```python
# Change:
from typing import List
# To:
from typing import List, Optional
```

Then add the following at the module level (after `print_items()`) and the `RISK_STYLE` dict (before the function):

```python
from mac_toolkit_pro.core.models import CleanableItem as _CI  # add to existing imports block

RISK_STYLE = {
    "safe":   "green",
    "warn":   "yellow",
    "danger": "bold red",
}


def print_preview_table(items: List[_CI], _console: Optional[Console] = None) -> None:
    """Render a pre-delete confirmation table. Pass _console for testing."""
    _con = _console if _console is not None else console  # console = module-level singleton
    total = sum(i.size_bytes for i in items)
    table = Table(
        title=f"⚠️  About to delete {len(items)} items ({fmt_bytes(total)})",
        box=box.ROUNDED, show_lines=True,
    )
    table.add_column("Path", overflow="fold", max_width=60)
    table.add_column("Size", justify="right", width=10)
    table.add_column("Risk", width=8)
    table.add_column("Age (days)", justify="right", width=10)

    for item in sorted(items, key=lambda x: x.size_bytes, reverse=True):
        style = RISK_STYLE.get(item.risk, "")
        age = str(item.age_days) if item.age_days is not None else "—"
        table.add_row(
            str(item.path),
            fmt_bytes(item.size_bytes),
            f"[{style}]{item.risk}[/]",
            age,
        )
    _con.print(table)
```

Note: The parameter is `_console` (not `console`) to avoid shadowing the module-level `console` singleton inside the function body.

- [ ] **Step 4: Run test**

```bash
pytest tests/test_models.py::test_print_preview_table_renders -v
```
Expected: PASS.

- [ ] **Step 5: Wire preview into `clean` and `full` commands in `cli.py`**

In the `clean` command, after `approved = engine.get_approved_items(results)` and before `cleaner = GenericCleaner(...)`, add:

```python
if execute and approved and mode != "item":
    from mac_toolkit_pro.reporters.terminal import print_preview_table
    print_preview_table(approved)
    try:
        confirm = input("\nProceed with deletion? [s/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        confirm = "n"
    if confirm not in ("s", "si", "y", "yes"):
        console.print("[dim]Cancelled.[/]")
        return
```

Apply the same block in the `full` command — after `approved = engine.get_approved_items(results)` and before `cleaner = GenericCleaner(...)`.

- [ ] **Step 6: Run full suite**

```bash
pytest tests/ -v
```
Expected: all tests pass.

- [ ] **Step 7: Manual end-to-end test**

```bash
./toolkit clean --execute --domain dev_caches --mode deal
```
Expected: after approval flow, the preview table appears before final deletion confirmation.

- [ ] **Step 8: Final commit**

```bash
git add mac_toolkit_pro/reporters/terminal.py mac_toolkit_pro/cli.py tests/
git commit -m "feat(cli,reporter): add pre-delete preview table and print_preview_table"
```

---

## Final validation

- [ ] **Run complete test suite**

```bash
pytest tests/ -v --tb=short
```
Expected: all tests pass, no regressions.

- [ ] **End-to-end smoke**

```bash
./toolkit status
./toolkit analyze --domain dev_caches --verbose
./toolkit clean --domain dev_caches   # dry-run, no --execute
```

- [ ] **Verify new domains appear in full analyze**

```bash
./toolkit analyze
```
Expected: `dev_caches`, `xcode`, `trash` rows in summary table.
