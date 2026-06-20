#!/usr/bin/env python3
"""Mac DevOps Toolkit Pro — Professional disk analysis and safe cleanup."""
from __future__ import annotations
import click
from datetime import datetime
from mac_toolkit_pro.core.config import REPORTS_DIR, DEFAULT_MIN_SIZE_MB
from mac_toolkit_pro.core.runner import run_analyzers
from mac_toolkit_pro.core.approval import ApprovalEngine
from mac_toolkit_pro.cleaners.generic import GenericCleaner
from mac_toolkit_pro.reporters import terminal, markdown, json_reporter, audit
from mac_toolkit_pro.reporters.terminal import console
from mac_toolkit_pro.analyzers.disk import DiskAnalyzer
from mac_toolkit_pro.analyzers.ollama import OllamaAnalyzer
from mac_toolkit_pro.analyzers.docker import DockerAnalyzer
from mac_toolkit_pro.analyzers.browser import BrowserAnalyzer
from mac_toolkit_pro.analyzers.logs import LogsAnalyzer
from mac_toolkit_pro.analyzers.downloads import DownloadsAnalyzer
from mac_toolkit_pro.analyzers.appsupport import AppSupportAnalyzer
from mac_toolkit_pro.analyzers.repos import ReposAnalyzer
from mac_toolkit_pro.analyzers.dev_caches import DevCachesAnalyzer
from mac_toolkit_pro.analyzers.xcode import XcodeAnalyzer
from mac_toolkit_pro.analyzers.trash import TrashAnalyzer

ALL_ANALYZERS = [
    DiskAnalyzer().analyze,
    OllamaAnalyzer().analyze,
    DockerAnalyzer().analyze,
    BrowserAnalyzer().analyze,
    LogsAnalyzer().analyze,
    DownloadsAnalyzer().analyze,
    AppSupportAnalyzer().analyze,
    ReposAnalyzer().analyze,
    DevCachesAnalyzer().analyze,
    XcodeAnalyzer().analyze,
    TrashAnalyzer().analyze,
]


def _filter_analyzers(domain):
    if domain is None:
        return ALL_ANALYZERS
    valid = {fn.__self__.domain for fn in ALL_ANALYZERS}
    if domain not in valid:
        raise click.BadParameter(
            f"Unknown domain '{domain}'. Valid: {', '.join(sorted(valid))}",
            param_hint="--domain",
        )
    return [fn for fn in ALL_ANALYZERS if fn.__self__.domain == domain]


@click.group()
def cli():
    """🖥  Mac DevOps Toolkit Pro — Disk analysis and safe cleanup."""
    pass


@cli.command()
@click.option("--save", is_flag=True, help="Save MD + JSON reports to reports/")
@click.option("--verbose", is_flag=True, help="Show all items")
@click.option("--min-size", default=DEFAULT_MIN_SIZE_MB, show_default=True, help="Min MB to display")
@click.option("--domain", default=None, help="Run only this domain (e.g. dev_caches)")
def analyze(save, verbose, min_size, domain):
    """Run full disk analysis across all 8 domains in parallel."""
    analyzers = _filter_analyzers(domain)
    console.print("\n[bold cyan]🔍 Running analysis across all domains...[/]\n")
    with console.status("[dim]Scanning in parallel (up to 30s per domain)...[/]"):
        results = run_analyzers(analyzers)

    terminal.print_summary(results)
    if verbose:
        terminal.print_items(results, min_size_bytes=min_size * 1024 * 1024)

    if save:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = REPORTS_DIR / f"analysis_{ts}"
        md_path = markdown.save(results, out_dir)
        json_path = json_reporter.save(results, out_dir)
        console.print(f"\n[dim]📄 {md_path}[/]")
        console.print(f"[dim]📄 {json_path}[/]")


@cli.command()
@click.option("--mode", default="deal",
              type=click.Choice(["deal", "category", "item", "checklist"]),
              show_default=True, help="Approval mode")
@click.option("--execute", is_flag=True, default=False, help="Perform real deletions (default: dry-run)")
@click.option("--min-size", default=DEFAULT_MIN_SIZE_MB, show_default=True)
@click.option("--domain", default=None, help="Clean only this domain (e.g. dev_caches)")
def clean(mode, execute, min_size, domain):
    """Analyze, then clean with interactive approval."""
    analyzers = _filter_analyzers(domain)
    if not execute:
        console.print("\n[dim]🔍 SIMULATION MODE — no files deleted. Use --execute to delete for real.[/]\n")

    with console.status("[dim]Scanning...[/]"):
        results = run_analyzers(analyzers)

    terminal.print_summary(results)
    terminal.print_items(results, min_size_bytes=min_size * 1024 * 1024)

    engine = ApprovalEngine(mode=mode, dry_run=not execute, execute=execute)
    approved = engine.get_approved_items(results)

    if not approved:
        console.print("\n[dim]Nothing selected for cleanup.[/]")
        return

    cleaner = GenericCleaner(dry_run=not execute, execute=execute)
    deletions = cleaner.clean(approved)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = REPORTS_DIR / f"cleanup_{ts}"
    audit_path = audit.write_audit_log(out_dir, dry_run=not execute, approval_mode=mode, deletions=deletions)

    successes = [d for d in deletions if d["result"] == "success"]
    console.print(f"\n[bold green]✓ Cleaned {len(successes)}/{len(deletions)} items[/]")
    console.print(f"[dim]📋 Audit: {audit_path}[/]")


@cli.command()
@click.option("--last", is_flag=True, help="Show last saved report")
def report(last):
    """View saved analysis reports."""
    if not REPORTS_DIR.exists():
        console.print("[yellow]No reports found. Run: ./toolkit analyze --save[/]")
        return
    reports = sorted(REPORTS_DIR.iterdir(), key=lambda p: p.name, reverse=True)
    if not reports:
        console.print("[yellow]No reports found.[/]")
        return
    md = reports[0] / "report.md"
    if md.exists():
        console.print(md.read_text())
    else:
        console.print(f"[yellow]No report.md in {reports[0]}[/]")


@cli.command()
@click.option("--mode", default="deal",
              type=click.Choice(["deal", "category", "item", "checklist"]),
              show_default=True)
@click.option("--execute", is_flag=True, default=False)
def full(mode, execute):
    """Full flow: analyze → save reports → clean with approval."""
    if not execute:
        console.print("\n[dim]🔍 SIMULATION MODE — use --execute to delete for real.[/]\n")

    with console.status("[dim]Running full analysis...[/]"):
        results = run_analyzers(ALL_ANALYZERS)

    terminal.print_summary(results)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = REPORTS_DIR / f"analysis_{ts}"
    markdown.save(results, out_dir)
    json_reporter.save(results, out_dir)
    console.print(f"[dim]📄 Reports → {out_dir}[/]\n")

    engine = ApprovalEngine(mode=mode, dry_run=not execute, execute=execute)
    approved = engine.get_approved_items(results)

    if not approved:
        console.print("[dim]Nothing selected.[/]")
        return

    cleaner = GenericCleaner(dry_run=not execute, execute=execute)
    deletions = cleaner.clean(approved)
    audit.write_audit_log(out_dir, dry_run=not execute, approval_mode=mode, deletions=deletions)
    successes = [d for d in deletions if d["result"] == "success"]
    console.print(f"\n[bold green]✓ Cleaned {len(successes)}/{len(deletions)} items[/]")


if __name__ == "__main__":
    cli()
