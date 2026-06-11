from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from mac_toolkit_pro.core.models import AnalysisResult

console = Console()

SEVERITY_STYLE = {
    "critical": "bold red",
    "high": "bold orange1",
    "medium": "bold yellow",
    "low": "bold green",
}

SEVERITY_ICON = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


def fmt_bytes(b: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def print_summary(results: List[AnalysisResult]) -> None:
    table = Table(title="🖥  Mac Disk Analysis", box=box.ROUNDED, show_lines=True)
    table.add_column("Domain", style="bold cyan", width=14)
    table.add_column("Severity", width=12)
    table.add_column("Size", justify="right", width=12)
    table.add_column("Items", justify="right", width=6)
    table.add_column("Summary")

    total_bytes = 0
    for r in sorted(results, key=lambda x: x.total_size_bytes, reverse=True):
        icon = SEVERITY_ICON.get(r.severity, "")
        style = SEVERITY_STYLE.get(r.severity, "")
        err = f" ⚠ {r.error}" if r.error else ""
        table.add_row(
            r.domain,
            f"[{style}]{icon} {r.severity}[/]",
            fmt_bytes(r.total_size_bytes),
            str(len(r.items)),
            r.summary + err,
        )
        total_bytes += r.total_size_bytes

    console.print(table)
    console.print(Panel(
        f"[bold]Total scanned:[/] {fmt_bytes(total_bytes)}",
        style="dim", expand=False,
    ))


def print_items(results: List[AnalysisResult], min_size_bytes: int = 0) -> None:
    for r in sorted(results, key=lambda x: x.total_size_bytes, reverse=True):
        if not r.items:
            continue
        table = Table(title=f"{r.domain.upper()} — {fmt_bytes(r.total_size_bytes)}", box=box.SIMPLE)
        table.add_column("Size", justify="right", width=10)
        table.add_column("Safe", width=6)
        table.add_column("Label")
        table.add_column("Reason", style="dim")
        for item in r.items:
            if item.size_bytes < min_size_bytes:
                continue
            safe = "✅" if item.safe_to_delete else "⚠️"
            table.add_row(fmt_bytes(item.size_bytes), safe, item.label, item.reason)
        console.print(table)
