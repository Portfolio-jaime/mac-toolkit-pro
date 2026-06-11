from abc import ABC, abstractmethod
from pathlib import Path
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

    def _make_result(self, items, total_size: int, summary: str) -> AnalysisResult:
        return AnalysisResult(
            domain=self.domain,
            severity=severity_label(total_size),
            total_size_bytes=total_size,
            items=items,
            summary=summary,
        )
