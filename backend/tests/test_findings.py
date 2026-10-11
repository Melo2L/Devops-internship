from backend.models.findings import (
    Finding,
    FindingCategory,
    FindingSeverity,
    FindingStatus,
)


def test_finding_uses_secure_defaults() -> None:
    finding = Finding(
        scanner="gitleaks",
        category=FindingCategory.SECRET,
        severity=FindingSeverity.HIGH,
        confidence=0.95,
        title="Potential secret detected",
        description="A potential secret was detected.",
        file=".env",
    )

    assert finding.scanner == "gitleaks"
    assert finding.category == FindingCategory.SECRET
    assert finding.severity == FindingSeverity.HIGH
    assert finding.confidence == 0.95
    assert finding.status == FindingStatus.OPEN
    assert finding.line is None
    assert finding.remediation is None


def test_finding_supports_location_and_remediation() -> None:
    finding = Finding(
        scanner="gitleaks",
        category=FindingCategory.SECRET,
        severity=FindingSeverity.CRITICAL,
        confidence=0.99,
        title="Exposed credential",
        description="A credential was detected.",
        file=".env.production",
        line=12,
        remediation="Remove the secret and rotate the credential.",
        rule_id="aws-access-token",
        fingerprint="example-fingerprint",
    )

    assert finding.line == 12
    assert finding.remediation is not None
    assert finding.rule_id == "aws-access-token"
    assert finding.fingerprint == "example-fingerprint"
    assert finding.status == FindingStatus.OPEN
