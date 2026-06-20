from pathlib import Path
from io import StringIO
from rich.console import Console
from mac_toolkit_pro.core.models import CleanableItem, AnalysisResult
from mac_toolkit_pro.reporters.terminal import print_preview_table


def _make_items():
    return [
        CleanableItem(
            path=Path("/tmp/npm"), size_bytes=50 * 1024 * 1024,
            label="npm cache", domain="dev_caches", safe_to_delete=True,
            reason="auto-regenerated", risk="safe", age_days=10,
        ),
        CleanableItem(
            path=Path("/tmp/arch"), size_bytes=200 * 1024 * 1024,
            label="Xcode Archives", domain="xcode", safe_to_delete=False,
            reason="verify before deleting", risk="warn", age_days=90,
        ),
    ]


def test_print_preview_table_renders_without_error():
    buf = StringIO()
    con = Console(file=buf, width=120)
    items = _make_items()
    print_preview_table(items, console=con)
    output = buf.getvalue()
    assert "npm cache" in output
    assert "Xcode Archives" in output


def test_print_preview_table_shows_risk():
    buf = StringIO()
    con = Console(file=buf, width=120)
    items = _make_items()
    print_preview_table(items, console=con)
    output = buf.getvalue()
    assert "safe" in output.lower() or "warn" in output.lower()


def test_print_preview_table_shows_size():
    buf = StringIO()
    con = Console(file=buf, width=120)
    items = _make_items()
    print_preview_table(items, console=con)
    output = buf.getvalue()
    assert "MB" in output


def test_print_preview_table_empty_items():
    buf = StringIO()
    con = Console(file=buf, width=120)
    print_preview_table([], console=con)
    output = buf.getvalue()
    assert "nothing" in output.lower() or output.strip() == "" or "0" in output
