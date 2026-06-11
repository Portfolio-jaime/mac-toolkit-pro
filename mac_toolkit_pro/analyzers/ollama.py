from pathlib import Path
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.config import OLLAMA_MODELS_DIR
from mac_toolkit_pro.core.models import AnalysisResult, CleanableItem, severity_label
from datetime import datetime


class OllamaAnalyzer(BaseAnalyzer):
    domain = "ollama"

    def analyze(self) -> AnalysisResult:
        blobs_dir = OLLAMA_MODELS_DIR / "blobs"
        if not blobs_dir.exists():
            return AnalysisResult(
                domain=self.domain, severity="low", total_size_bytes=0,
                items=[], summary="Ollama not installed",
                error="not found", timestamp=datetime.now(),
            )
        items = []
        total = 0
        try:
            for blob in blobs_dir.iterdir():
                if blob.is_file():
                    size = blob.stat().st_size
                    total += size
                    items.append(CleanableItem(
                        path=blob, size_bytes=size,
                        label=blob.name[:20], domain=self.domain,
                        safe_to_delete=False,
                        reason="Ollama model blob — verify model is unused before deleting",
                    ))
        except PermissionError as e:
            return AnalysisResult(
                domain=self.domain, severity="low", total_size_bytes=0,
                items=[], summary="Permission denied", error=str(e),
            )
        items.sort(key=lambda x: x.size_bytes, reverse=True)
        return self._make_result(
            items, total,
            f"{len(items)} blobs, {total/(1024**3):.1f}GB total"
        )
