from backend.models.findings import (
    FindingCategory,
    FindingSeverity,
)
from backend.scanners.gitleaks import GitleaksFinding
from backend.scanners.gitleaks_normalizer import (
    normalize_gitleaks_finding,
    normalize_gitleaks_findings,
)


def test_normalize_gitleaks_finding() -> None:
    gitleaks_finding = GitleaksFinding(
        rule_id="aws-access-token",
        description="AWS Access Key",
        severity="High",
        file=".env",
        line=12,
        secret="SECRET_VALUE_MUST_NOT_BE_PROPAGATED",
        commit=None,
    )

    finding = normalize_gitleaks_finding(
        gitleaks_finding,
    )

    assert finding.scanner == "gitleaks"
    assert finding.category == FindingCategory.SECRET
    assert finding.severity == FindingSeverity.HIGH
    assert finding.confidence is None
    assert finding.file == ".env"
    assert finding.line == 12
    assert finding.rule_id == "aws-access-token"
    assert finding.status.value == "Open"

    assert not hasattr(finding, "secret")


def test_normalize_multiple_gitleaks_findings() -> None:
    findings = [
        GitleaksFinding(
            rule_id="rule-one",
            description="Secret one",
            severity="High",
            file="config/.env",
            line=5,
            secret="SECRET_ONE",
            commit=None,
        ),
        GitleaksFinding(
            rule_id="rule-two",
            description="Secret two",
            severity="High",
            file="config/prod.env",
            line=8,
            secret="SECRET_TWO",
            commit=None,
        ),
    ]

    normalized = normalize_gitleaks_findings(findings)

    assert len(normalized) == 2
    assert normalized[0].scanner == "gitleaks"
    assert normalized[1].scanner == "gitleaks"
    assert normalized[0].rule_id == "rule-one"
    assert normalized[1].rule_id == "rule-two"
