from datetime import datetime
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import LOG_DIRS
from mac_toolkit_pro.core.models import CleanableItem


class LogsAnalyzer(BaseAnalyzer):
    domain = "logs"

    def analyze(self):
        items = []
        total = 0
        now = datetime.now()
        for log_dir in LOG_DIRS:
            if not log_dir.exists():
                continue
            try:
                for log_file in log_dir.rglob("*.log*"):
                    if not log_file.is_file():
                        continue
                    try:
                        st = log_file.stat()
                        size = st.st_size
                        age_days = (now - datetime.fromtimestamp(st.st_mtime)).days
                        if age_days >= 7:
                            total += size
                            items.append(CleanableItem(
                                path=log_file, size_bytes=size,
                                label=f"{log_file.name} ({age_days}d old)",
                                domain=self.domain, safe_to_delete=True,
                                reason=f"Log file {age_days} days old",
                                risk="safe",
                                age_days=age_days,
                            ))
                    except OSError:
                        continue
            except PermissionError:
                continue
        items.sort(key=lambda x: x.size_bytes, reverse=True)
        return self._make_result(items, total, f"{len(items)} old logs, {total/(1024**2):.0f}MB")
