import subprocess, json
from mac_toolkit_pro.analyzers.base import BaseAnalyzer
from mac_toolkit_pro.core.models import AnalysisResult, severity_label
from datetime import datetime


class DiskAnalyzer(BaseAnalyzer):
    domain = "disk"

    def analyze(self) -> AnalysisResult:
        try:
            result = subprocess.run(
                ["df", "-k", "/System/Volumes/Data"],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) >= 2:
                parts = lines[1].split()
                used_bytes = int(parts[2]) * 1024
                avail_bytes = int(parts[3]) * 1024
                total_bytes = used_bytes + avail_bytes
                pct = int(parts[4].rstrip("%"))
                summary = f"Used {used_bytes/(1024**3):.1f}GB / {total_bytes/(1024**3):.1f}GB ({pct}%)"
                severity = "critical" if pct >= 85 else "high" if pct >= 70 else "low"
                return AnalysisResult(
                    domain=self.domain, severity=severity,
                    total_size_bytes=used_bytes, items=[],
                    summary=summary, timestamp=datetime.now(),
                )
            # df returned fewer than 2 lines — volume not found or unusual state
            return AnalysisResult(
                domain=self.domain, severity="low", total_size_bytes=0,
                items=[], summary="Could not parse df output",
                error="df output had fewer than 2 lines",
            )
        except Exception as e:
            return AnalysisResult(
                domain=self.domain, severity="low", total_size_bytes=0,
                items=[], summary="Could not read disk", error=str(e),
            )
