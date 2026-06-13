from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from mac_toolkit_pro.core.models import AnalysisResult, CleanableItem, severity_label


class BaseAnalyzer(ABC):
    domain: str = "base"

    @abstractmethod
    def analyze(self) -> AnalysisResult:
        ...

    def _dir_size(self, path: Path) -> int:
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except OSError:
                        continue
        except PermissionError:
            pass
        return total

    def _oldest_mtime_age(self, path: Path) -> Optional[int]:
        """Age in days of the oldest file under path, or None if path missing."""
        if not path.exists():
            return None
        oldest: Optional[float] = None
        try:
            for f in path.rglob("*"):
                if f.is_file():
                    try:
                        mtime = f.stat().st_mtime
                        if oldest is None or mtime < oldest:
                            oldest = mtime
                    except OSError:
                        continue
        except (PermissionError, OSError):
            return None
        if oldest is None:
            return None
        return int((datetime.now().timestamp() - oldest) / 86400)

    def _make_result(self, items, total_size: int, summary: str) -> AnalysisResult:
        return AnalysisResult(
            domain=self.domain,
            severity=severity_label(total_size),
            total_size_bytes=total_size,
            items=items,
            summary=summary,
        )
