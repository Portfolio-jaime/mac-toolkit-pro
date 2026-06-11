from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import BROWSER_CACHE_PATHS
from mac_toolkit_pro.core.models import CleanableItem


class BrowserAnalyzer(BaseAnalyzer):
    domain = "browser"

    def analyze(self):
        items = []
        total = 0
        for browser, path in BROWSER_CACHE_PATHS.items():
            if path.exists():
                size = self._dir_size(path)
                total += size
                if size > 0:
                    items.append(CleanableItem(
                        path=path, size_bytes=size,
                        label=f"{browser} cache",
                        domain=self.domain, safe_to_delete=True,
                        reason=f"{browser} cache — safe to delete",
                    ))
        items.sort(key=lambda x: x.size_bytes, reverse=True)
        return self._make_result(items, total, f"Browser caches: {total/(1024**2):.0f}MB")
