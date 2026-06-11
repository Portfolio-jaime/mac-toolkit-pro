import time
import pytest
from mac_toolkit_pro.core.models import AnalysisResult
from mac_toolkit_pro.core.runner import run_analyzers


def make_fast_analyzer(domain: str, size: int):
    def analyze():
        return AnalysisResult(
            domain=domain, severity="low",
            total_size_bytes=size, items=[], summary=f"{domain} ok"
        )
    return analyze


def make_slow_analyzer(domain: str):
    def analyze():
        time.sleep(35)  # Exceeds 30s timeout
        return AnalysisResult(domain=domain, severity="low", total_size_bytes=0, items=[], summary="slow")
    return analyze


def make_crashing_analyzer(domain: str):
    def analyze():
        raise RuntimeError("Disk read error")
    return analyze


def test_run_multiple_analyzers():
    analyzers = [make_fast_analyzer("disk", 1000), make_fast_analyzer("ollama", 2000)]
    results = run_analyzers(analyzers)
    assert len(results) == 2
    domains = {r.domain for r in results}
    assert "disk" in domains
    assert "ollama" in domains


def test_crashing_analyzer_returns_degraded_result():
    analyzers = [make_crashing_analyzer("docker")]
    results = run_analyzers(analyzers)
    assert len(results) == 1
    assert results[0].error is not None
    assert "Disk read error" in results[0].error


def test_slow_analyzer_returns_timeout_result():
    analyzers = [make_slow_analyzer("browser")]
    results = run_analyzers(analyzers, timeout=2)
    assert len(results) == 1
    assert results[0].error == "timeout"
