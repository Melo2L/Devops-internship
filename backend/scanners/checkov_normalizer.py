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
    "INFO": FindingSeverity.INFORMATIONAL,
    "INFORMATIONAL": FindingSeverity.INFORMATIONAL,
}


def _path(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = value.replace("\\", "/").lstrip("/")
    return str(PurePosixPath(normalized))


def normalize_checkov_findings(reports: list[dict]) -> list[Finding]:
    findings: list[Finding] = []

    for report in reports:
        results = report.get("results") or {}
        for item in results.get("failed_checks") or []:
            rule_id = str(item.get("check_id") or "unknown")
            file = _path(item.get("file_path"))
            line_range = item.get("file_line_range") or []
            line = (
                line_range[0]
                if line_range and isinstance(line_range[0], int)
                else None
            )

            metadata = item.get("metadata") or {}
            raw_severity = metadata.get("severity") or item.get("severity")
            severity = SEVERITIES.get(
                str(raw_severity).upper(),
                FindingSeverity.INFORMATIONAL,
            )

            title = str(item.get("check_name") or rule_id)
            guideline = item.get("guideline")
            description = (
                f"{title}. Severity was not supplied by Checkov; "
                "SecureScan marks it informational until severity is verified."
                if not raw_severity else title
            )
            remediation = str(guideline) if guideline else None
            identity = f"checkov|{rule_id}|{file}|{line or 0}"
            fingerprint = hashlib.sha256(identity.encode("utf-8")).hexdigest()

            findings.append(Finding(
                scanner="checkov",
                category=FindingCategory.IAC,
                severity=severity,
                confidence=None,
                title=title,
                description=description,
                file=file,
                line=line,
                remediation=remediation,
                rule_id=rule_id,
                fingerprint=fingerprint,
            ))

    return findings
