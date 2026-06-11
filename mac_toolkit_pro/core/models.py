from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

RiskLevel = Literal["safe", "warn", "danger"]


@dataclass
class CleanableItem:
    path: Path
    size_bytes: int
    label: str
    domain: str
    safe_to_delete: bool
    reason: str
    age_days: Optional[int] = None
    risk: RiskLevel = "safe"


@dataclass
class AnalysisResult:
    domain: str
    severity: str          # "critical" | "high" | "medium" | "low"
    total_size_bytes: int
    items: List[CleanableItem]
    summary: str
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None


def severity_label(size_bytes: int) -> str:
    gb = size_bytes / (1024 ** 3)
    mb = size_bytes / (1024 ** 2)
    if gb > 10:
        return "critical"
    if gb > 1:
        return "high"
    if mb > 100:
        return "medium"
    return "low"
