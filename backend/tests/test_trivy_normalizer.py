import pytest

from backend.models.findings import (
    FindingCategory,
    FindingSeverity,
    FindingStatus,
)
from backend.scanners.trivy_normalizer import normalize_trivy_findings


def test_normalize_trivy_vulnerability() -> None:
    report = {
        "Results": [
            {
                "Target": "package-lock.json",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-1234",
                        "Severity": "HIGH",
                        "Title": "Vulnerable dependency",
                        "Description": "A dependency contains a vulnerability.",
                        "PkgPath": "node_modules/example/package.json",
                        "FixedVersion": "2.0.0",
                    }
                ],
            }
        ]
    }

    findings = normalize_trivy_findings(report)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.scanner == "trivy"
    assert finding.category == FindingCategory.DEPENDENCY
    assert finding.severity == FindingSeverity.HIGH
    assert finding.confidence is None
    assert finding.title == "Vulnerable dependency"
    assert finding.description == "A dependency contains a vulnerability."
    assert finding.file == "node_modules/example/package.json"
    assert finding.remediation == "Upgrade to a fixed version: 2.0.0."
    assert finding.rule_id == "CVE-2026-1234"
    assert finding.status == FindingStatus.OPEN
    assert len(finding.fingerprint) == 64


def test_normalize_trivy_misconfiguration() -> None:
    report = {
        "Results": [
            {
                "Target": "infrastructure/main.tf",
                "Misconfigurations": [
                    {
                        "ID": "AVD-AWS-0001",
                        "Severity": "CRITICAL",
                        "Title": "Public access enabled",
                        "Description": "Resource allows public access.",
                        "Resolution": "Restrict public access.",
                        "CauseMetadata": {"StartLine": 15},
                    }
                ],
            }
        ]
    }

    findings = normalize_trivy_findings(report)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.scanner == "trivy"
    assert finding.category == FindingCategory.CONFIGURATION
    assert finding.severity == FindingSeverity.CRITICAL
    assert finding.file == "infrastructure/main.tf"
    assert finding.line == 15
    assert finding.title == "Public access enabled"
    assert finding.remediation == "Restrict public access."
    assert finding.rule_id == "AVD-AWS-0001"


def test_normalize_trivy_unknown_severity() -> None:
    report = {
        "Results": [
            {
                "Target": "package.json",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CUSTOM-001",
                        "Severity": "CUSTOM",
                    }
                ],
            }
        ]
    }

    findings = normalize_trivy_findings(report)
    assert findings[0].severity == FindingSeverity.INFORMATIONAL


def test_normalize_trivy_windows_path() -> None:
    report = {
        "Results": [
            {
                "Target": r"C:\temp\workspace\project\main.tf",
                "Misconfigurations": [{"ID": "AVD-TEST-001", "Severity": "LOW"}],
            }
        ]
    }

    findings = normalize_trivy_findings(report)
    assert findings[0].file == "temp/workspace/project/main.tf"


def test_normalize_trivy_fingerprint_is_stable() -> None:
    report = {
        "Results": [
            {
                "Target": "package.json",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-5678",
                        "Severity": "MEDIUM",
                    }
                ],
            }
        ]
    }

    first = normalize_trivy_findings(report)
    second = normalize_trivy_findings(report)

    assert first[0].fingerprint == second[0].fingerprint
    assert len(first[0].fingerprint) == 64


def test_normalize_empty_trivy_report() -> None:
    assert normalize_trivy_findings({"Results": []}) == []


@pytest.mark.parametrize("report", [None, [], "invalid", 123])
def test_normalize_trivy_rejects_invalid_report(report) -> None:
    with pytest.raises(ValueError):
        normalize_trivy_findings(report)


@pytest.mark.parametrize("results", [{}, "invalid", 123])
def test_normalize_trivy_rejects_invalid_results(results) -> None:
    with pytest.raises(ValueError):
        normalize_trivy_findings({"Results": results})


@pytest.mark.parametrize("result", [None, "invalid", 123])
def test_normalize_trivy_rejects_invalid_result_entries(result) -> None:
    with pytest.raises(ValueError):
        normalize_trivy_findings({"Results": [result]})


@pytest.mark.parametrize(
    "field",
    ["Vulnerabilities", "Misconfigurations"],
)
def test_normalize_trivy_rejects_invalid_finding_lists(field) -> None:
    report = {
        "Results": [
            {
                "Target": "project",
                field: {},
            }
        ]
    }

    with pytest.raises(ValueError):
        normalize_trivy_findings(report)
