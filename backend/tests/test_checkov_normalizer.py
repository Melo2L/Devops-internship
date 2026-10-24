from backend.models.findings import (
    FindingCategory,
    FindingSeverity,
    FindingStatus,
)
from backend.scanners.checkov_normalizer import normalize_checkov_findings


def _report(*checks: dict) -> list[dict]:
    return [
        {
            "check_type": "terraform",
            "results": {"failed_checks": list(checks)},
            "summary": {},
        }
    ]


def _check(**overrides: object) -> dict:
    item: dict = {
        "check_id": "CKV_AWS_1",
        "check_name": "Example security check",
        "file_path": "/main.tf",
        "file_line_range": [3, 5],
        "guideline": "Apply the recommended security configuration.",
        "metadata": {"severity": "HIGH"},
    }
    item.update(overrides)
    return item


def test_normalize_checkov_finding() -> None:
    findings = normalize_checkov_findings(_report(_check()))

    assert len(findings) == 1
    finding = findings[0]

    assert finding.scanner == "checkov"
    assert finding.category == FindingCategory.IAC
    assert finding.severity == FindingSeverity.HIGH
    assert finding.confidence is None
    assert finding.title == "Example security check"
    assert finding.file == "main.tf"
    assert finding.line == 3
    assert finding.rule_id == "CKV_AWS_1"
    assert finding.remediation == "Apply the recommended security configuration."
    assert finding.status == FindingStatus.OPEN
    assert len(finding.fingerprint or "") == 64


def test_missing_severity_uses_informational() -> None:
    findings = normalize_checkov_findings(
        _report(_check(metadata=None, severity=None))
    )

    assert len(findings) == 1
    assert findings[0].severity == FindingSeverity.INFORMATIONAL
    assert "Severity was not supplied by Checkov" in findings[0].description


def test_normalize_supported_severities() -> None:
    cases = [
        ("CRITICAL", FindingSeverity.CRITICAL),
        ("HIGH", FindingSeverity.HIGH),
        ("MEDIUM", FindingSeverity.MEDIUM),
        ("LOW", FindingSeverity.LOW),
        ("INFO", FindingSeverity.INFORMATIONAL),
        ("INFORMATIONAL", FindingSeverity.INFORMATIONAL),
    ]

    for raw_severity, expected in cases:
        findings = normalize_checkov_findings(
            _report(_check(metadata={"severity": raw_severity}))
        )
        assert findings[0].severity == expected


def test_severity_can_come_from_top_level_item() -> None:
    findings = normalize_checkov_findings(
        _report(_check(metadata=None, severity="MEDIUM"))
    )

    assert findings[0].severity == FindingSeverity.MEDIUM


def test_normalize_windows_path() -> None:
    findings = normalize_checkov_findings(
        _report(_check(file_path=r"C:\workspace\project\main.tf"))
    )

    assert findings[0].file == "C:/workspace/project/main.tf"


def test_missing_path_and_line_use_safe_defaults() -> None:
    findings = normalize_checkov_findings(
        _report(_check(file_path=None, file_line_range=[]))
    )

    assert findings[0].file == "unknown"
    assert findings[0].line is None


def test_multiple_findings_and_stable_fingerprints() -> None:
    report = _report(
        _check(check_id="CKV_AWS_1"),
        _check(check_id="CKV_AWS_2"),
    )

    first = normalize_checkov_findings(report)
    second = normalize_checkov_findings(report)

    assert len(first) == 2
    assert first[0].rule_id == "CKV_AWS_1"
    assert first[1].rule_id == "CKV_AWS_2"
    assert first[0].fingerprint == second[0].fingerprint
    assert first[1].fingerprint == second[1].fingerprint
    assert first[0].fingerprint != first[1].fingerprint


def test_empty_report_returns_no_findings() -> None:
    assert normalize_checkov_findings([]) == []
    assert normalize_checkov_findings(
        [{"results": {"failed_checks": []}}]
    ) == []
