# Storage & Cleanup v2 — Design Spec

**Date:** 2026-06-10  
**Status:** Approved  
**Scope:** `mac_toolkit_pro` package only (legacy `mac_*.py` scripts untouched)

---

## Problem

The current toolkit covers 8 domains but misses **~6.1 GB** of cleanable data on the target Mac:
- `~/.npm/_cacache`: 3.4 GB
- `~/Library/Caches/Homebrew`: 1.9 GB
- `~/Library/Caches/pip`: 768 MB

Additionally, the UX has two friction points:
1. No way to clean a single domain without scanning all 8.
2. `--execute` mode shows no final preview — user can't confirm exactly what will be deleted.

---

## Goals

1. Add 3 new analyzers: `dev_caches`, `xcode`, `trash`.
2. Enrich `CleanableItem` with `age_days` and `risk` to enable smarter approval UX.
3. Add `--domain` flag to `analyze` and `clean` commands.
4. Add `./toolkit status` command (fast, no full scan).
5. Add pre-delete preview table when `--execute` is used without `--mode item`.

---

## Non-Goals

- No changes to legacy `mac_*.py` scripts.
- No scheduler / cron (Phase 4).
- No duplicate detection across domains (future work).
- No undo/restore (files are deleted, no recycle bin).

---

## Architecture

### 1. Model changes — `core/models.py`

Add `Literal` import and a `RiskLevel` alias:

```python
from typing import Literal, Optional
RiskLevel = Literal["safe", "warn", "danger"]

@dataclass
class CleanableItem:
    path: Path
    size_bytes: int
    label: str
    domain: str
    safe_to_delete: bool
    reason: str
    age_days: Optional[int] = None     # oldest file mtime age in days
    risk: RiskLevel = "safe"           # "safe" | "warn" | "danger"
```

**Risk semantics:**
- `safe` — auto-generated cache, always regenerable (npm, pip, brew, browser caches, logs)
- `warn` — large or old files that might matter (downloads >100 MB, appsupport data)
- `danger` — not confirmed safe to auto-delete (ollama blobs, docker image)

All existing analyzers must set `risk` explicitly; default is `"safe"` to avoid breaking changes.

**Existing analyzer `CleanableItem` instantiation sites that need `risk=` added (all 8 files):**
- `analyzers/disk.py` → `risk="warn"`
- `analyzers/ollama.py` → `risk="danger"`
- `analyzers/docker.py` → `risk="danger"`
- `analyzers/browser.py` → `risk="safe"`
- `analyzers/logs.py` → `risk="safe"`
- `analyzers/downloads.py` → `risk="warn"`
- `analyzers/appsupport.py` → `risk="warn"`
- `analyzers/repos.py` → `risk="safe"`

---

### 2. `BaseAnalyzer` helper — `analyzers/base.py`

Add `_oldest_mtime_age(path: Path) -> Optional[int]` to `BaseAnalyzer`:

```python
def _oldest_mtime_age(self, path: Path) -> Optional[int]:
    """Return age in days of the oldest file under path, or None if path missing."""
    oldest = None
    try:
        for f in path.rglob("*"):
            if f.is_file():
                mtime = f.stat().st_mtime
                if oldest is None or mtime < oldest:
                    oldest = mtime
    except (PermissionError, OSError):
        return None
    if oldest is None:
        return None
    return int((datetime.now().timestamp() - oldest) / 86400)
```

All new analyzers use this helper for `age_days`. Existing analyzers may adopt it optionally.

---

### 3. New analyzers

#### `analyzers/dev_caches.py` — `DevCachesAnalyzer`

Scans 3 sub-targets independently, returns them as separate `CleanableItem` entries:

| Sub-target | Path | Risk |
|---|---|---|
| npm cache | `~/.npm/_cacache` | safe |
| pip cache | `~/Library/Caches/pip` | safe |
| brew cache | `~/Library/Caches/Homebrew` | safe |

Each sub-target is a single directory item (not recursed into individual files). `age_days` set to oldest file mtime within the directory.

#### `analyzers/xcode.py` — `XcodeAnalyzer`

Scans (only if paths exist):
- `~/Library/Developer/Xcode/DerivedData` → risk `safe`
- `~/Library/Developer/Xcode/Archives` → risk `warn` (archives may be needed for re-signing)
- `~/Library/Developer/CoreSimulator/Devices` → risk `safe`

Returns early with `summary="Xcode not installed"` if none of the paths exist.

#### `analyzers/trash.py` — `TrashAnalyzer`

Scans `~/.Trash`. Reports total size and item count. All items have `risk="warn"` (user put them there intentionally, so we confirm before vacuuming). Does **not** recurse deep — reports `~/.Trash` as a single item.

**Blacklist note:** `~/.Trash` is not in `BLACKLISTED_PREFIXES`, so `BaseCleaner._delete()` will proceed normally. The analyzer represents the Trash directory as a **single `CleanableItem` pointing to `~/.Trash`** with `safe_to_delete=False` to force the user through the approval step. `GenericCleaner` will call `shutil.rmtree("~/.Trash")` which empties it. This is intentional — equivalent to "Empty Trash" in Finder.

---

### 3. Config changes — `core/config.py`

Add constants:
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

---

### 4. CLI changes — `cli.py`

#### `ALL_ANALYZERS` list
Add `DevCachesAnalyzer`, `XcodeAnalyzer`, `TrashAnalyzer`.

#### `--domain` flag on `analyze` and `clean`

```
./toolkit analyze --domain dev_caches
./toolkit clean --execute --domain dev_caches
```

Implementation: filter `ALL_ANALYZERS` by `fn.__self__.domain == domain` before passing to `run_analyzers()`. Invalid domain → `click.BadParameter` with list of valid domains.

#### `./toolkit status` command

Fast overview using `shutil.disk_usage` + direct `du` calls on the most expensive known paths (no `run_analyzers`). Target: <3 seconds.

Output: Rich table with columns `Domain | Est. Size` (no "Last Checked" — no persistence layer). Shows live `du` sizes for: disk, ollama models dir, docker raw file, npm cache, pip cache, brew cache, trash. Other domains show `—`.

#### Pre-delete preview table

In `clean` and `full` commands, when `execute=True` and `mode != "item"`:
- In `clean`: after `ApprovalEngine.get_approved_items()`, render preview table → `[s/N]` → `GenericCleaner.clean()`.
- In `full`: after `markdown.save()` / `json_reporter.save()`, after approval, same preview → `[s/N]` → `GenericCleaner.clean()`.

The table shows columns: `Path | Size | Risk | Age (days)`. `age_days=None` displays as `—`.

#### `cli.py` Console cleanup

`cli.py` currently creates its own `Console()` instance at line 22. This must be removed. Import and reuse `console` from `reporters/terminal.py` instead, consistent with the project's singleton constraint.

---

### 5. Approval engine — `core/approval.py`

No structural changes. The new `risk` field is used only for display (color coding in terminal output) and in the preview table. The engine does not auto-reject `danger` items — that's the user's call.

---

### 6. Terminal reporter — `reporters/terminal.py`

- `print_summary()`: add `risk` color coding (green=safe, yellow=warn, red=danger) to item rows.
- New `print_preview_table(items)`: renders the pre-delete confirmation table.

---

### 7. Existing analyzer updates

Set `risk` on existing analyzers to avoid defaulting:

| Analyzer | risk |
|---|---|
| disk | `warn` (just disk info, no items to delete) |
| ollama | `danger` |
| docker | `danger` |
| browser | `safe` |
| logs | `safe` |
| downloads | `warn` |
| appsupport | `warn` |
| repos | `safe` (node_modules, .venv, __pycache__) |

---

## Data Flow (updated)

```
run_analyzers(filtered_by_domain?)
  → List[AnalysisResult]  (each item has age_days + risk)
  → terminal.print_summary()
  → ApprovalEngine.get_approved_items()
  → [if execute] terminal.print_preview_table()  ← new
  → [s/N confirm]
  → GenericCleaner.clean()
  → audit.write_audit_log()
```

---

## Testing

- Unit tests for each new analyzer (no filesystem side effects — mock paths that don't exist).
- Unit test for `--domain` filter logic in CLI.
- Unit test for `risk` field propagation.
- Existing tests must stay green (backward compat: `risk` defaults to `"safe"`).

---

## Roadmap (out of scope for this spec)

| Phase | Feature | Notes |
|---|---|---|
| 2 | System Monitor | Migrate `mac_system_monitor.py` + `mac_process_manager.py` to `monitor/` module |
| 3 | Network + Battery | Migrate `mac_network_monitor.py` + `mac_battery_analyzer.py` |
| 4 | Scheduler | `./toolkit schedule` — launchd weekly cron + macOS notifications |
