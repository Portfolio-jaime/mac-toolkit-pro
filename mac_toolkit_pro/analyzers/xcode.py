from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import XCODE_PATHS
from mac_toolkit_pro.core.models import CleanableItem

_RISK = {
    "derived_data": "safe",
    "simulators": "safe",
    "archives": "warn",
}

_LABELS = {
    "derived_data": "Xcode DerivedData",
    "simulators": "iOS Simulators",
    "archives": "Xcode Archives",
}


class XcodeAnalyzer(BaseAnalyzer):
    domain = "xcode"

    def analyze(self):
        items = []
        total = 0
        for key, path in XCODE_PATHS.items():
            if not path.exists():
                continue
            size = self._dir_size(path)
            if size == 0:
                continue
            total += size
            items.append(CleanableItem(
                path=path, size_bytes=size,
                label=_LABELS[key],
                domain=self.domain,
                safe_to_delete=(key != "archives"),
                reason=(
                    f"{_LABELS[key]} — safe to delete, Xcode regenerates"
                    if key != "archives"
                    else "Xcode Archives — verify archives are no longer needed"
                ),
                age_days=self._oldest_mtime_age(path),
                risk=_RISK[key],
            ))

        if not items:
            return self._make_result([], 0, "Xcode not installed")

        items.sort(key=lambda x: x.size_bytes, reverse=True)
        return self._make_result(
            items, total,
            f"Xcode: {total / (1024 ** 3):.1f}GB across {len(items)} targets",
        )
