from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import DEV_CACHE_PATHS
from mac_toolkit_pro.core.models import CleanableItem


class DevCachesAnalyzer(BaseAnalyzer):
    domain = "dev_caches"

    def analyze(self):
        items = []
        total = 0
        for name, path in DEV_CACHE_PATHS.items():
            if not path.exists():
                continue
            size = self._dir_size(path)
            if size == 0:
                continue
            total += size
            items.append(CleanableItem(
                path=path, size_bytes=size,
                label=f"{name} cache",
                domain=self.domain, safe_to_delete=True,
                reason=f"{name} cache — auto-regenerated on next use",
                age_days=self._oldest_mtime_age(path),
                risk="safe",
            ))
        items.sort(key=lambda x: x.size_bytes, reverse=True)
        parts = [f"{i.label} {i.size_bytes / (1024 ** 2):.0f}MB" for i in items]
        summary = ", ".join(parts) if parts else "No dev caches found"
        return self._make_result(items, total, summary)
