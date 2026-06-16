import os
from pathlib import Path
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import REPO_ROOTS
from mac_toolkit_pro.core.models import CleanableItem

CLEANABLE_DIRS = {"node_modules", ".venv", "__pycache__", ".pytest_cache"}


class ReposAnalyzer(BaseAnalyzer):
    domain = "repos"

    def analyze(self):
        items = []
        total = 0
        for root in REPO_ROOTS:
            if not root.exists():
                continue
            try:
                for dirpath, dirnames, _ in os.walk(root):
                    found = []
                    remaining = []
                    for d in dirnames:
                        if d in CLEANABLE_DIRS:
                            found.append(d)
                        else:
                            remaining.append(d)
                    # Prune: don't recurse into artifact dirs (avoids double-counting)
                    dirnames[:] = remaining
                    for d in found:
                        candidate = Path(dirpath) / d
                        size = self._dir_size(candidate)
                        total += size
                        items.append(CleanableItem(
                            path=candidate, size_bytes=size,
                            label=f"{candidate.parent.name}/{candidate.name}",
                            domain=self.domain, safe_to_delete=True,
                            reason=f"Reinstallable dependency dir ({candidate.name})",
                            risk="safe",
                        ))
            except PermissionError:
                continue
        items.sort(key=lambda x: x.size_bytes, reverse=True)
        return self._make_result(items, total, f"Repo artifacts: {total/(1024**2):.0f}MB")
