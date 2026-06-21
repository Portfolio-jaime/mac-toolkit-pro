from __future__ import annotations
import questionary
from mac_toolkit_pro.reporters.terminal import console

MENU_CHOICES = [
    {"name": "🔍 Analyze disk (all domains)", "value": "analyze"},
    {"name": "🧹 Clean disk (interactive)", "value": "clean"},
    {"name": "📊 Full flow (analyze + clean)", "value": "full"},
    {"name": "📋 Domain status", "value": "status"},
    {"name": "🔋 Battery health", "value": "battery"},
    {"name": "💻 System (CPU / memory)", "value": "system"},
    {"name": "⚙️  Processes (top CPU / mem)", "value": "processes"},
    {"name": "🌐 Network", "value": "network"},
    {"name": "❌ Quit", "value": "quit"},
]


def show_menu() -> None:
    console.print("\n[bold cyan]Mac DevOps Toolkit Pro[/] — choose an action\n")

    choice = questionary.select(
        "What would you like to do?",
        choices=[c["name"] for c in MENU_CHOICES],
    ).ask()

    if choice is None:
        return

    value = next((c["value"] for c in MENU_CHOICES if c["name"] == choice), None)
    if not value or value == "quit":
        return

    _dispatch(value)


def _dispatch(action: str) -> None:
    if action == "analyze":
        from mac_toolkit_pro.core.runner import run_analyzers
        from mac_toolkit_pro.cli import ALL_ANALYZERS
        from mac_toolkit_pro.reporters import terminal
        with console.status("[dim]Scanning...[/]"):
            results = run_analyzers(ALL_ANALYZERS)
        terminal.print_summary(results)

    elif action == "clean":
        from mac_toolkit_pro.core.runner import run_analyzers
        from mac_toolkit_pro.core.approval import ApprovalEngine
        from mac_toolkit_pro.cleaners.generic import GenericCleaner
        from mac_toolkit_pro.reporters import terminal
        from mac_toolkit_pro.cli import ALL_ANALYZERS
        with console.status("[dim]Scanning...[/]"):
            results = run_analyzers(ALL_ANALYZERS)
        terminal.print_summary(results)
        engine = ApprovalEngine(mode="checklist", dry_run=True, execute=False)
        approved = engine.get_approved_items(results)
        if approved:
            terminal.print_preview_table(approved)
            confirm = questionary.confirm(
                f"Delete {len(approved)} items? (DRY-RUN — use toolkit clean --execute for real)"
            ).ask()
            if confirm:
                GenericCleaner(dry_run=True, execute=False).clean(approved)

    elif action == "full":
        from mac_toolkit_pro.core.runner import run_analyzers
        from mac_toolkit_pro.reporters import terminal
        from mac_toolkit_pro.cli import ALL_ANALYZERS
        with console.status("[dim]Running full analysis...[/]"):
            results = run_analyzers(ALL_ANALYZERS)
        terminal.print_summary(results)

    elif action == "status":
        from click.testing import CliRunner
        from mac_toolkit_pro.cli import cli
        CliRunner().invoke(cli, ["status"], catch_exceptions=False)

    elif action == "battery":
        from mac_toolkit_pro.monitors.battery import BatteryMonitor
        BatteryMonitor().display()

    elif action == "system":
        from mac_toolkit_pro.monitors.system import SystemMonitor
        SystemMonitor().display()

    elif action == "processes":
        from mac_toolkit_pro.monitors.processes import ProcessMonitor
        ProcessMonitor().display()

    elif action == "network":
        from mac_toolkit_pro.monitors.network import NetworkMonitor
        NetworkMonitor().display()
