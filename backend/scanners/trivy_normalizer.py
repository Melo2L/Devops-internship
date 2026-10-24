import hashlib
from pathlib import PurePosixPath

from backend.models.findings import (
    Finding,
    FindingCategory,
    FindingSeverity,
)

SEVERITIES = {
    "CRITICAL": FindingSeverity.CRITICAL,
    "HIGH": FindingSeverity.HIGH,
    "MEDIUM": FindingSeverity.MEDIUM,
    "LOW": FindingSeverity.LOW,
    "UNKNOWN": FindingSeverity.INFORMATIONAL,
}


def _path(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = value.replace("\\", "/").lstrip("/")
    return str(PurePosixPath(normalized))


def _fingerprint(scanner: str, rule: str, file: str, line: int | None) -> str:
    value = f"{scanner}|{rule}|{file}|{line or 0}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_trivy_findings(report: dict) -> list[Finding]:
    findings: list[Finding] = []

    for result in report.get("Results") or []:
        target = _path(result.get("Target"))

        for item in result.get("Vulnerabilities") or []:
            severity = SEVERITIES.get(
                str(item.get("Severity", "")).upper(),
                FindingSeverity.INFORMATIONAL,
            )
            rule_id = str(item.get("VulnerabilityID") or "unknown")
            file = _path(item.get("PkgPath") or target)
            title = str(item.get("Title") or rule_id)
            description = str(item.get("Description") or title)
            fixed = item.get("FixedVersion")
            remediation = (
                f"Upgrade to a fixed version: {fixed}."
                if fixed else
                (
                    "Check the advisory and upgrade to a supported, "
                    "patched version if available."
                )
            )

            findings.append(Finding(
                scanner="trivy",
                category=FindingCategory.DEPENDENCY,
                severity=severity,
                confidence=None,
                title=title,
                description=description,
                file=file,
                remediation=remediation,
                rule_id=rule_id,
                fingerprint=_fingerprint("trivy", rule_id, file, None),
            ))

        for item in result.get("Misconfigurations") or []:
            severity = SEVERITIES.get(
                str(item.get("Severity", "")).upper(),
                FindingSeverity.INFORMATIONAL,
            )
            rule_id = str(item.get("ID") or item.get("AVDID") or "unknown")
            metadata = item.get("CauseMetadata") or {}
            start_line = metadata.get("StartLine")
            file = target
            title = str(item.get("Title") or rule_id)
            description = str(item.get("Description") or item.get("Message") or title)

            findings.append(Finding(
                scanner="trivy",
                category=FindingCategory.CONFIGURATION,
                severity=severity,
                confidence=None,
                title=title,
                description=description,
                file=file,
                line=start_line if isinstance(start_line, int) else None,
                remediation=item.get("Resolution"),
                rule_id=rule_id,
                fingerprint=_fingerprint(
                    "trivy", rule_id, file,
                    start_line if isinstance(start_line, int) else None,
                ),
            ))

    return findings
