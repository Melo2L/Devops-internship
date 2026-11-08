
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from backend.core.metrics import (
    SCANNER_DURATION_SECONDS,
    SCANNER_EXECUTIONS_TOTAL,
)
from backend.models.findings import Finding
from backend.scanners.checkov import scan_checkov
from backend.scanners.checkov_normalizer import normalize_checkov_findings
from backend.scanners.gitleaks import GitleaksScanner
from backend.scanners.gitleaks_normalizer import normalize_gitleaks_findings
from backend.scanners.semgrep import SemgrepScanner
from backend.scanners.semgrep_normalizer import normalize_semgrep_findings
from backend.scanners.trivy import scan_trivy
from backend.scanners.trivy_normalizer import normalize_trivy_findings
from backend.services.scan_planner import ScanPlan

logger = logging.getLogger(__name__)


@dataclass
class ScanExecutionResult:
    scanner: str
    findings: list[Finding] = field(default_factory=list)
    status: str = "completed"
    error: str | None = None


def _execute_scanner(scanner: str, project_path: Path) -> list[Finding]:
    """Execute one scanner and normalize its findings."""

    if scanner == "gitleaks":
        raw = GitleaksScanner().scan(project_path)
        return normalize_gitleaks_findings(raw)

    if scanner == "semgrep":
        raw = SemgrepScanner().scan(project_path)
        return normalize_semgrep_findings(raw)

    if scanner == "trivy":
        raw = scan_trivy(project_path)
        return normalize_trivy_findings(raw)

    if scanner == "checkov":
        raw = scan_checkov(project_path)
        return normalize_checkov_findings(raw)

    raise ValueError(f"Unsupported scanner: {scanner}")


def execute_scan_plan(
    plan: ScanPlan,
    project_path: Path,
) -> list[ScanExecutionResult]:
    """Execute enabled scanners independently in a fixed order."""

    results: list[ScanExecutionResult] = []
    enabled = set(plan.enabled_scanners)

    scanner_order = [
        "gitleaks",
        "semgrep",
        "trivy",
        "checkov",
    ]

    for scanner in scanner_order:
        if scanner not in enabled:
            continue

        start_time = time.perf_counter()

        try:
            findings = _execute_scanner(scanner, project_path)

        except Exception:
            logger.exception("Scanner '%s' execution failed.", scanner)

            SCANNER_EXECUTIONS_TOTAL.labels(
                scanner=scanner,
                status="failed",
            ).inc()

            results.append(
                ScanExecutionResult(
                    scanner=scanner,
                    status="failed",
                    error="Scanner execution failed.",
                )
            )

        else:
            SCANNER_EXECUTIONS_TOTAL.labels(
                scanner=scanner,
                status="completed",
            ).inc()

            results.append(
                ScanExecutionResult(
                    scanner=scanner,
                    findings=findings,
                    status="completed",
                )
            )

        finally:
            SCANNER_DURATION_SECONDS.labels(
                scanner=scanner,
            ).observe(time.perf_counter() - start_time)

    return results
