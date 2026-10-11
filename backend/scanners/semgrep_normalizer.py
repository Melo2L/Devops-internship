import hashlib
from pathlib import PurePosixPath, PureWindowsPath

from backend.models.findings import (
    Finding,
    FindingCategory,
    FindingSeverity,
)
from backend.scanners.semgrep import SemgrepFinding

SEVERITY_MAPPING = {
    "ERROR": FindingSeverity.HIGH,
    "WARNING": FindingSeverity.MEDIUM,
    "INFO": FindingSeverity.INFORMATIONAL,
}

# Rule-specific guidance can be expanded as more scanners are integrated.
REMEDIATION_BY_RULE = {
    "python.lang.security.audit.subprocess-shell-true.subprocess-shell-true": (
        "Avoid shell=True when passing variable or untrusted input to "
        "subprocess. Prefer shell=False and pass the executable and "
        "arguments as a list. Validate inputs and avoid constructing "
        "shell commands from user-controlled data."
    ),
}


def _normalize_file_path(file_path: str) -> str:
    """
    Convert an absolute or platform-specific path into a normalized
    project-relative-looking path without exposing temporary directories.

    The scanner should ideally receive a project root so that paths can
    be made reliably relative to that root. This fallback removes common
    temporary workspace prefixes when the root is unavailable.
    """
    path = file_path.replace("\\", "/").strip()

    # Remove common temporary workspace prefixes.
    markers = ("/workspace/", "workspace/")
    for marker in markers:
        index = path.lower().find(marker.lower())
        if index >= 0:
            path = path[index + len(marker) :]
            break

    # Remove leading separators and normalize the remaining path.
    path = path.lstrip("/")
    normalized = str(PurePosixPath(path))

    # Defensive fallback for Windows-style paths.
    if PureWindowsPath(normalized).is_absolute():
        normalized = PureWindowsPath(normalized).name

    return normalized or "unknown"


def _stable_fingerprint(
    finding: SemgrepFinding,
    normalized_file: str,
) -> str:
    """
    Generate a deterministic identifier when Semgrep does not provide
    a usable fingerprint.
    """
    provided = (finding.fingerprint or "").strip()

    if provided and provided.lower() not in {
        "requires login",
        "none",
        "null",
        "unknown",
    }:
        return provided

    identity = "|".join(
        (
            finding.check_id.strip(),
            normalized_file,
            str(finding.start_line or 0),
            finding.message.strip(),
        )
    )

    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _remediation_for(finding: SemgrepFinding) -> str:
    for rule_prefix, remediation in REMEDIATION_BY_RULE.items():
        if finding.check_id == rule_prefix:
            return remediation

    return (
        "Review the affected source code and consult the Semgrep rule "
        "guidance. Validate the finding, apply the appropriate fix, "
        "and add a regression test where practical."
    )


def normalize_semgrep_finding(
    finding: SemgrepFinding,
) -> Finding:
    severity = SEVERITY_MAPPING.get(
        finding.severity.upper(),
        FindingSeverity.MEDIUM,
    )

    normalized_file = _normalize_file_path(finding.file)
    fingerprint = _stable_fingerprint(finding, normalized_file)

    return Finding(
        scanner="semgrep",
        category=FindingCategory.SOURCE_CODE,
        severity=severity,
        confidence=0.90,
        title=finding.message,
        description=(
            "Semgrep detected a potential source-code security issue "
            f"using rule '{finding.check_id}'."
        ),
        file=normalized_file,
        line=finding.start_line,
        remediation=_remediation_for(finding),
        rule_id=finding.check_id,
        fingerprint=fingerprint,
    )


def normalize_semgrep_findings(
    findings: list[SemgrepFinding],
) -> list[Finding]:
    return [normalize_semgrep_finding(finding) for finding in findings]
