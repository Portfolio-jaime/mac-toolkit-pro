from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime
from typing import Callable, List

from mac_toolkit_pro.core.config import ANALYZER_TIMEOUT_SECONDS
from mac_toolkit_pro.core.models import AnalysisResult


def _get_domain(fn: Callable) -> str:
    """Extract domain name from a bound analyzer method or bare callable."""
    # Bound method of BaseAnalyzer subclass: fn.__self__.domain is authoritative
    instance = getattr(fn, "__self__", None)
    if instance is not None and hasattr(instance, "domain"):
        return instance.domain
    return getattr(fn, "__name__", "unknown")


def run_analyzers(
    analyzers: List[Callable[[], AnalysisResult]],
    timeout: int = ANALYZER_TIMEOUT_SECONDS,
) -> List[AnalysisResult]:
    results: List[AnalysisResult] = []
    with ThreadPoolExecutor(max_workers=len(analyzers) or 1) as pool:
        futures = {pool.submit(fn): fn for fn in analyzers}
        for future, fn in futures.items():
            domain = _get_domain(fn)
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except FuturesTimeout:
                results.append(AnalysisResult(
                    domain=domain, severity="low", total_size_bytes=0,
                    items=[], summary="Analyzer timed out",
                    timestamp=datetime.now(), error="timeout",
                ))
            except Exception as exc:
                results.append(AnalysisResult(
                    domain=domain, severity="low", total_size_bytes=0,
                    items=[], summary="Analyzer failed",
                    timestamp=datetime.now(), error=str(exc),
                ))
    return results
