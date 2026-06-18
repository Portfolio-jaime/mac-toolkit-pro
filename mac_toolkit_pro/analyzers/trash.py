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
        return self._make_result([item], size, f"Trash: {size/(1024**2):.0f}MB in {item_count} items")
