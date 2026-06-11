import json
from datetime import datetime
from pathlib import Path
from typing import List
from mac_toolkit_pro.core.models import AnalysisResult


def save(results: List[AnalysisResult], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "domains": [
            {
                "domain": r.domain,
                "severity": r.severity,
                "total_size_bytes": r.total_size_bytes,
                "summary": r.summary,
                "error": r.error,
                "items": [
                    {
                        "path": str(i.path),
                        "size_bytes": i.size_bytes,
                        "label": i.label,
                        "safe_to_delete": i.safe_to_delete,
                        "reason": i.reason,
                    }
                    for i in r.items
                ],
            }
            for r in results
        ],
    }
    path = output_dir / "report.json"
    path.write_text(json.dumps(payload, indent=2))
    return path
