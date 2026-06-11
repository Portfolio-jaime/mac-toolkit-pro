from __future__ import annotations
from typing import List
from mac_toolkit_pro.core.models import AnalysisResult, CleanableItem
from mac_toolkit_pro.reporters.terminal import fmt_bytes, console


class ApprovalEngine:
    def __init__(self, mode: str, dry_run: bool, execute: bool):
        self.mode = mode
        self.dry_run = dry_run
        self.execute = execute and not dry_run

    def get_approved_items(self, results: List[AnalysisResult]) -> List[CleanableItem]:
        if self.mode == "deal":
            return self._mode_deal(results)
        if self.mode == "category":
            return self._mode_category(results)
        if self.mode == "item":
            return self._mode_item(results)
        if self.mode == "checklist":
            return self._mode_checklist(results)
        return []

    def _ask(self, prompt: str) -> bool:
        try:
            answer = input(f"{prompt} [s/N] ").strip().lower()
            return answer in ("s", "si", "y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    def _mode_deal(self, results: List[AnalysisResult]) -> List[CleanableItem]:
        total = sum(r.total_size_bytes for r in results)
        console.print(f"\n💡 Analysis complete. I can free up to [bold]{fmt_bytes(total)}[/].")
        if not self._ask("Ready to start?"):
            return []
        approved = []
        for r in sorted(results, key=lambda x: x.total_size_bytes, reverse=True):
            if not r.items:
                continue
            console.print(f"\n  → [bold]{r.domain}[/] {fmt_bytes(r.total_size_bytes)}")
            if self._ask("    Clean this?"):
                approved.extend(r.items)
        return approved

    def _mode_category(self, results: List[AnalysisResult]) -> List[CleanableItem]:
        approved = []
        for r in sorted(results, key=lambda x: x.total_size_bytes, reverse=True):
            if not r.items:
                continue
            console.print(f"\n  🗂  [bold]{r.domain}[/]: {fmt_bytes(r.total_size_bytes)} ({r.summary})")
            if self._ask("    Clean this category?"):
                approved.extend(r.items)
        return approved

    def _mode_item(self, results: List[AnalysisResult]) -> List[CleanableItem]:
        approved = []
        for r in results:
            for item in r.items:
                console.print(f"  🗑  {item.path}  ({fmt_bytes(item.size_bytes)})")
                if self._ask("     Delete?"):
                    approved.append(item)
        return approved

    def _mode_checklist(self, results: List[AnalysisResult]) -> List[CleanableItem]:
        try:
            import questionary
            choices = []
            item_map = {}
            for r in results:
                for item in r.items:
                    label = f"{fmt_bytes(item.size_bytes):>10}  [{r.domain}] {item.label}"
                    choices.append(questionary.Choice(title=label, value=item.path))
                    item_map[item.path] = item
            selected_paths = questionary.checkbox(
                "Select items to clean (Space=toggle, Enter=confirm):",
                choices=choices,
            ).ask()
            if not selected_paths:
                return []
            return [item_map[p] for p in selected_paths if p in item_map]
        except ImportError:
            console.print("[yellow]questionary not installed — falling back to category mode[/]")
            return self._mode_category(results)
