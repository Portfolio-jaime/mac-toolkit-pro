import pytest
from pathlib import Path
from mac_toolkit_pro.core.models import CleanableItem, AnalysisResult


def test_cleanable_item_fields():
    item = CleanableItem(
        path=Path("/tmp/test"),
        size_bytes=1024,
        label="Test file",
        domain="downloads",
        safe_to_delete=True,
        reason="Temporary file",
    )
    assert item.size_bytes == 1024
    assert item.domain == "downloads"
    assert item.safe_to_delete is True


def test_analysis_result_severity():
    result = AnalysisResult(
        domain="ollama",
        severity="critical",
        total_size_bytes=50 * 1024**3,
        items=[],
        summary="48GB of models",
    )
    assert result.severity == "critical"
    assert result.error is None


def test_analysis_result_with_error():
    result = AnalysisResult(
        domain="docker",
        severity="low",
        total_size_bytes=0,
        items=[],
        summary="Docker unreachable",
        error="Docker daemon unreachable",
    )
    assert result.error == "Docker daemon unreachable"


def test_severity_label():
    from mac_toolkit_pro.core.models import severity_label
    assert severity_label(11 * 1024**3) == "critical"
    assert severity_label(5 * 1024**3) == "high"
    assert severity_label(500 * 1024**2) == "medium"
    assert severity_label(10 * 1024**2) == "low"
