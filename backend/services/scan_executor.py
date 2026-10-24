from dataclasses import dataclass, field
from pathlib import Path

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


@dataclass
class ScanExecutionResult:
    scanner: str
    findings: list[Finding] = field(default_factory=list)


def execute_scan_plan(
    plan: ScanPlan,
    project_path: Path,
) -> list[ScanExecutionResult]:
    results: list[ScanExecutionResult] = []
    enabled = set(plan.enabled_scanners)

    if "gitleaks" in enabled:
        raw = GitleaksScanner().scan(project_path)
        results.append(ScanExecutionResult(
            scanner="gitleaks",
            findings=normalize_gitleaks_findings(raw),
        ))

    if "semgrep" in enabled:
        raw = SemgrepScanner().scan(project_path)
        results.append(ScanExecutionResult(
            scanner="semgrep",
            findings=normalize_semgrep_findings(raw),
        ))

    if "trivy" in enabled:
        raw = scan_trivy(project_path)
        results.append(ScanExecutionResult(
            scanner="trivy",
            findings=normalize_trivy_findings(raw),
        ))

    if "checkov" in enabled:
        raw = scan_checkov(project_path)
        results.append(ScanExecutionResult(
            scanner="checkov",
            findings=normalize_checkov_findings(raw),
        ))

    return results
