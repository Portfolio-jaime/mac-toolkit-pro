from datetime import datetime
from pathlib import Path
from typing import List
from mac_toolkit_pro.core.models import AnalysisResult
from mac_toolkit_pro.reporters.terminal import fmt_bytes

SEVERITY_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}


def save(results: List[AnalysisResult], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Mac Disk Analysis Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        "| Domain | Severity | Size | Items | Summary |",
        "|--------|----------|------|-------|---------|",
    ]
    total = 0
    for r in sorted(results, key=lambda x: x.total_size_bytes, reverse=True):
        icon = SEVERITY_ICON.get(r.severity, "")
        err = f" ⚠ {r.error}" if r.error else ""
        lines.append(
            f"| {r.domain} | {icon} {r.severity} | {fmt_bytes(r.total_size_bytes)} "
            f"| {len(r.items)} | {r.summary}{err} |"
        )
        total += r.total_size_bytes

    lines += ["", f"**Total scanned:** {fmt_bytes(total)}", ""]

    for r in sorted(results, key=lambda x: x.total_size_bytes, reverse=True):
        if not r.items:
            continue
        lines += [f"## {r.domain.upper()} — {fmt_bytes(r.total_size_bytes)}", ""]
        lines += ["| Size | Safe | Label | Reason |", "|------|------|-------|--------|"]
        for item in r.items[:20]:
            safe = "✅" if item.safe_to_delete else "⚠️"
            lines.append(f"| {fmt_bytes(item.size_bytes)} | {safe} | {item.label} | {item.reason} |")
        lines.append("")

    path = output_dir / "report.md"
    path.write_text("\n".join(lines))
    return path
