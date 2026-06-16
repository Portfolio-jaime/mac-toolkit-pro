from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import APP_SUPPORT_DIR
from mac_toolkit_pro.core.models import CleanableItem


class AppSupportAnalyzer(BaseAnalyzer):
    domain = "appsupport"

    def analyze(self):
        items = []
        total = 0
        if not APP_SUPPORT_DIR.exists():
            return self._make_result([], 0, "Application Support not found")
        try:
            for app_dir in APP_SUPPORT_DIR.iterdir():
                if not app_dir.is_dir():
                    continue
                size = self._dir_size(app_dir)
                if size > 50 * 1024 * 1024:
                    total += size
                    items.append(CleanableItem(
                        path=app_dir, size_bytes=size,
                        label=app_dir.name, domain=self.domain,
                        safe_to_delete=False,
                        reason="Application data — verify app is uninstalled before deleting",
                        risk="warn",
                    ))
        except PermissionError:
            pass
        items.sort(key=lambda x: x.size_bytes, reverse=True)
        return self._make_result(items, total, f"App Support: {total/(1024**3):.1f}GB across {len(items)} apps")
