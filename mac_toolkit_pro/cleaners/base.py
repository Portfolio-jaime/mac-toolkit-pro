import shutil
from abc import ABC
from pathlib import Path
from typing import Any, Dict, List
from mac_toolkit_pro.core.config import BLACKLISTED_PREFIXES, BLACKLISTED_PATHS
from mac_toolkit_pro.core.models import CleanableItem


class BaseCleaner(ABC):
    def __init__(self, dry_run: bool, execute: bool):
        self.dry_run = dry_run
        self.execute = execute and not dry_run

    def _is_blacklisted(self, path: Path) -> bool:
        if path.name in BLACKLISTED_PATHS:
            return True
        return any(str(path).startswith(str(p)) for p in BLACKLISTED_PREFIXES)

    def _delete(self, path: Path) -> Dict[str, Any]:
        if self._is_blacklisted(path):
            return {"path": str(path), "result": "skipped-blacklisted", "error": None}
        if self.dry_run or not self.execute:
            return {"path": str(path), "result": "skipped-dry-run", "error": None}
        try:
            if path.is_file():
                size = path.stat().st_size
                path.unlink()
            elif path.is_dir():
                size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                shutil.rmtree(path)
            else:
                return {"path": str(path), "result": "skipped-not-found", "error": None}
            return {"path": str(path), "size_bytes": size, "result": "success", "error": None}
        except Exception as e:
            return {"path": str(path), "result": "failure", "error": str(e)}
