import subprocess
from pathlib import Path
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.models import AnalysisResult, CleanableItem
from datetime import datetime

_DOCKER_RAW = Path.home() / "Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"


class DockerAnalyzer(BaseAnalyzer):
    domain = "docker"

    def analyze(self) -> AnalysisResult:
        try:
            result = subprocess.run(
                ["docker", "system", "df"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                return self._degraded("Docker daemon unreachable")
            total_bytes = self._raw_file_size()
            items = self._build_items()
            return self._make_result(items, total_bytes, f"Docker using {total_bytes/(1024**3):.1f}GB")
        except FileNotFoundError:
            return self._degraded("Docker not installed")
        except subprocess.TimeoutExpired:
            return self._degraded("Docker daemon timed out")
        except Exception as e:
            return self._degraded(str(e))

    def _degraded(self, reason: str) -> AnalysisResult:
        return AnalysisResult(
            domain=self.domain, severity="low", total_size_bytes=0,
            items=[], summary="Docker unavailable", error=reason, timestamp=datetime.now(),
        )

    def _raw_file_size(self) -> int:
        return _DOCKER_RAW.stat().st_size if _DOCKER_RAW.exists() else 0

    def _build_items(self) -> list:
        if not _DOCKER_RAW.exists():
            return []
        return [CleanableItem(
            path=_DOCKER_RAW, size_bytes=_DOCKER_RAW.stat().st_size,
            label="Docker.raw virtual disk",
            domain=self.domain, safe_to_delete=False,
            reason="Run 'docker system prune -a' to reclaim space inside Docker",
        )]
