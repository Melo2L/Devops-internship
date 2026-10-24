from backend.models.findings import (
    FindingCategory,
    FindingSeverity,
)
from backend.scanners.semgrep import SemgrepFinding
from backend.scanners.semgrep_normalizer import (
    normalize_semgrep_finding,
    normalize_semgrep_findings,
)


def test_normalize_semgrep_finding() -> None:
    semgrep_finding = SemgrepFinding(
        check_id="python.lang.security.audit.eval-detected",
        message="Detected use of eval().",
        severity="WARNING",
        file="app.py",
        start_line=10,
        end_line=10,
        fingerprint="abc123",
    )

    finding = normalize_semgrep_finding(semgrep_finding)

    assert finding.scanner == "semgrep"
    assert finding.category == FindingCategory.SOURCE_CODE
    assert finding.severity == FindingSeverity.MEDIUM
    assert finding.confidence is None
    assert finding.title == "Detected use of eval()."
    assert finding.file == "app.py"
    assert finding.line == 10
    assert finding.rule_id == "python.lang.security.audit.eval-detected"
    assert finding.fingerprint == "abc123"
    assert finding.status.value == "Open"


def test_normalize_semgrep_severities() -> None:
    error_finding = SemgrepFinding(
        check_id="rule-error",
        message="Error finding",
        severity="ERROR",
        file="app.py",
        start_line=1,
        end_line=1,
        fingerprint=None,
    )

    info_finding = SemgrepFinding(
        check_id="rule-info",
        message="Informational finding",
        severity="INFO",
        file="app.py",
        start_line=2,
        end_line=2,
        fingerprint=None,
    )

    normalized_error = normalize_semgrep_finding(error_finding)
    normalized_info = normalize_semgrep_finding(info_finding)

    assert normalized_error.severity == FindingSeverity.HIGH
    assert normalized_info.severity == FindingSeverity.INFORMATIONAL


def test_normalize_multiple_semgrep_findings() -> None:
    findings = [
        SemgrepFinding(
            check_id="rule-one",
            message="Finding one",
            severity="WARNING",
            file="app.py",
            start_line=5,
            end_line=5,
            fingerprint="fingerprint-one",
        ),
        SemgrepFinding(
            check_id="rule-two",
            message="Finding two",
            severity="ERROR",
            file="server.py",
            start_line=12,
            end_line=12,
            fingerprint="fingerprint-two",
        ),
    ]

    normalized = normalize_semgrep_findings(findings)

    assert len(normalized) == 2
    assert normalized[0].scanner == "semgrep"
    assert normalized[1].scanner == "semgrep"
    assert normalized[0].rule_id == "rule-one"
    assert normalized[1].rule_id == "rule-two"


def test_normalize_windows_path_and_temporary_workspace() -> None:
    finding = SemgrepFinding(
        check_id="rule-path",
        message="Path test",
        severity="WARNING",
        file=r"C:\temp\workspace\project\app.py",
        start_line=7,
        end_line=7,
        fingerprint=None,
    )

    normalized = normalize_semgrep_finding(finding)

    assert normalized.file == "project/app.py"
    assert len(normalized.fingerprint) == 64


def test_normalize_unknown_severity_uses_medium() -> None:
    finding = SemgrepFinding(
        check_id="rule-unknown",
        message="Unknown severity",
        severity="CUSTOM",
        file="app.py",
        start_line=1,
        end_line=1,
        fingerprint=None,
    )

    normalized = normalize_semgrep_finding(finding)

    assert normalized.severity == FindingSeverity.MEDIUM


def test_normalize_fingerprint_placeholders_generates_stable_hash() -> None:
    finding = SemgrepFinding(
        check_id="rule-fingerprint",
        message="Finding message",
        severity="ERROR",
        file="app.py",
        start_line=12,
        end_line=12,
        fingerprint="unknown",
    )

    first = normalize_semgrep_finding(finding)
    second = normalize_semgrep_finding(finding)

    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64


def test_normalize_known_rule_includes_specific_remediation() -> None:
    finding = SemgrepFinding(
        check_id=(
            "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true"
        ),
        message="Unsafe subprocess call",
        severity="ERROR",
        file="app.py",
        start_line=20,
        end_line=20,
        fingerprint="rule-test",
    )

    normalized = normalize_semgrep_finding(finding)

    assert "shell=False" in normalized.remediation


def test_normalize_windows_absolute_path_without_workspace_prefix() -> None:
    from backend.scanners.semgrep_normalizer import _normalize_file_path

    assert _normalize_file_path("C:/outside/app.py") == "app.py"
