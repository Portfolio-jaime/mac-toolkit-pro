import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def write_audit_log(
    output_dir: Path,
    dry_run: bool,
    approval_mode: str,
    deletions: List[Dict[str, Any]],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "session_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "executed_by": os.getenv("USER", "unknown"),
        "dry_run": dry_run,
        "approval_mode": approval_mode,
        "deletions": deletions,
    }
    path = output_dir / "audit.json"
    path.write_text(json.dumps(payload, indent=2))
    return path
