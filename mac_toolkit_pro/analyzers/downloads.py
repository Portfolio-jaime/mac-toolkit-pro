from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import DOWNLOAD_DIRS
from mac_toolkit_pro.core.models import CleanableItem

DUPLICATE_PATTERNS = [" (1)", " (2)", " (3)", " copy", " Copy", "-1", "-2"]
LARGE_FILE_MB = 100


class DownloadsAnalyzer(BaseAnalyzer):
    domain = "downloads"

    def analyze(self):
        items = []
        total = 0
        for search_dir in DOWNLOAD_DIRS:
            if not search_dir.exists():
                continue
            try:
                for f in search_dir.rglob("*"):
                    if not f.is_file():
                        continue
                    try:
                        size = f.stat().st_size
                        is_large = size >= LARGE_FILE_MB * 1024 * 1024
                        is_dup = any(p in f.name for p in DUPLICATE_PATTERNS)
                        is_zip = f.suffix.lower() in (".zip", ".tar", ".gz", ".dmg", ".pkg")
                        if is_large or is_dup or is_zip:
                            total += size
                            reason = "duplicate" if is_dup else ("archive" if is_zip else f"large file ({size/(1024**2):.0f}MB)")
                            items.append(CleanableItem(
                                path=f, size_bytes=size,
                                label=f.name, domain=self.domain,
                                safe_to_delete=is_dup,
                                reason=reason,
                            ))
                    except OSError:
                        continue
            except PermissionError:
                continue
        items.sort(key=lambda x: x.size_bytes, reverse=True)
        return self._make_result(items, total, f"{len(items)} candidates, {total/(1024**2):.0f}MB")
