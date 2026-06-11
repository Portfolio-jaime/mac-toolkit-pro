# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip3 install click rich questionary pytest

# Run the toolkit
./toolkit --help
./toolkit analyze
./toolkit clean
./toolkit full

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_runner.py

# Run a single test
pytest tests/test_models.py::test_severity_label
```

## Architecture

This repo has two generations of code:

1. **Legacy standalone scripts** (`mac_*.py` at root) — self-contained scripts using only stdlib + psutil. Each script is independent.

2. **`mac_toolkit_pro/` package** — the current production codebase. Entry point: `./toolkit` (shell wrapper → `mac_toolkit_pro.cli`).

### Package structure

```
mac_toolkit_pro/
  cli.py              # Click CLI: analyze | clean | full | report commands
  core/
    config.py         # All path constants, thresholds, blacklist (edit here for new targets)
    models.py         # CleanableItem, AnalysisResult dataclasses + severity_label()
    runner.py         # run_analyzers() — runs all analyzers in parallel via ThreadPoolExecutor
    approval.py       # ApprovalEngine — deal/category/item/checklist modes
  analyzers/
    base.py           # BaseAnalyzer ABC with _dir_size() helper
    disk/ollama/docker/browser/logs/downloads/appsupport/repos.py  — one per domain
  cleaners/
    base.py           # BaseCleaner — _is_blacklisted() + _delete() with blacklist enforcement
    generic.py        # GenericCleaner — iterates CleanableItem list
  reporters/
    terminal.py       # Rich-formatted console output (console singleton lives here)
    markdown.py       # Save report.md to reports/
    json_reporter.py  # Save report.json
    audit.py          # Write audit.json after cleanup
```

### Data flow

`run_analyzers()` → `List[AnalysisResult]` → `ApprovalEngine.get_approved_items()` → `List[CleanableItem]` → `GenericCleaner.clean()` → deletion log

### Key design constraints

- **`--execute` flag is required for real deletions.** All commands default to dry-run. `BaseCleaner._delete()` checks `self.execute` before touching the filesystem.
- **Blacklist is enforced in `BaseCleaner._is_blacklisted()`** — `/System`, `/usr`, `/bin`, `/sbin`, and specific app prefs are never deleted regardless of approval.
- **Analyzer timeout is 120s** (configured in `config.py` as `ANALYZER_TIMEOUT_SECONDS`). `run_analyzers()` returns a degraded `AnalysisResult` with `error="timeout"` if exceeded.
- **`console` singleton** is defined in `reporters/terminal.py` and imported by other modules — don't create new `Console()` instances.
- **`ALL_ANALYZERS`** is defined in `cli.py` — add new analyzers there and create the corresponding file in `analyzers/`.
- Repo roots scanned by `ReposAnalyzer` are hardcoded in `config.py` as `REPO_ROOTS`.
