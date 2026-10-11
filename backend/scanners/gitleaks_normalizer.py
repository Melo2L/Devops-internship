from backend.models.findings import (
    Finding,
    FindingCategory,
    FindingSeverity,
)
from backend.scanners.gitleaks import GitleaksFinding


def normalize_gitleaks_finding(
    finding: GitleaksFinding,
) -> Finding:
    """
    Convert a Gitleaks finding into the SecureScan finding model.
    """

    return Finding(
        scanner="gitleaks",
        category=FindingCategory.SECRET,
        severity=FindingSeverity.HIGH,
        confidence=0.95,
        title=finding.description,
        description=(
            f"Gitleaks detected a potential secret using rule '{finding.rule_id}'."
        ),
        file=finding.file,
        line=finding.line,
        remediation=(
            "Remove the exposed secret, rotate the affected "
            "credential, and verify that it is no longer present "
            "in the project or Git history."
        ),
        rule_id=finding.rule_id,
    )


def normalize_gitleaks_findings(
    findings: list[GitleaksFinding],
) -> list[Finding]:
    """
    Normalize all Gitleaks findings into SecureScan findings.
    """

    return [normalize_gitleaks_finding(finding) for finding in findings]
