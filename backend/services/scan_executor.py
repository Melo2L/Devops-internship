from dataclasses import dataclass, field
from pathlib import Path

from backend.models.findings import Finding
from backend.scanners.gitleaks import GitleaksScanner
from backend.scanners.gitleaks_normalizer import normalize_gitleaks_findings
from backend.scanners.semgrep import SemgrepScanner
from backend.scanners.semgrep_normalizer import normalize_semgrep_findings
from backend.services.scan_planner import ScanPlan


@dataclass
class ScanExecutionResult:
    scanner: str
    findings: list[Finding] = field(default_factory=list)


def execute_scan_plan(
    plan: ScanPlan,
    project_path: Path,
) -> list[ScanExecutionResult]:
    results = []

    if "gitleaks" in plan.enabled_scanners:
        scanner = GitleaksScanner()

        raw_findings = scanner.scan(project_path)

        findings = normalize_gitleaks_findings(raw_findings)

        results.append(
            ScanExecutionResult(
                scanner="gitleaks",
                findings=findings,
            )
        )

    if "semgrep" in plan.enabled_scanners:
        scanner = SemgrepScanner()

        raw_findings = scanner.scan(project_path)

        findings = normalize_semgrep_findings(raw_findings)

        results.append(
            ScanExecutionResult(
                scanner="semgrep",
                findings=findings,
            )
        )

    return results
