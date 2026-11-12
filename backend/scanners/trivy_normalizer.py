import hashlib
import re
from pathlib import PurePosixPath
from typing import Any

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
    if value is None or value == "":
        return "unknown"

    if not isinstance(value, str):
        raise ValueError("Trivy report contains an invalid file path.")

    normalized = value.replace("\\", "/")
    normalized = re.sub(r"^[A-Za-z]:", "", normalized)
    normalized = normalized.lstrip("/")

    return str(PurePosixPath(normalized))


def _fingerprint(
    scanner: str,
    rule: str,
    file: str,
    line: int | None,
) -> str:
    value = f"{scanner}|{rule}|{file}|{line or 0}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_list(
    value: Any,
    field: str,
    result_index: int,
) -> list:
    if value is None:
        return []

    if not isinstance(value, list):
        raise ValueError(
            f"Trivy report contains an invalid 'Results[{result_index}].{field}' list."
        )

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(
                f"Trivy report contains an invalid "
                f"'Results[{result_index}].{field}[{index}]' object."
            )

    return value


def normalize_trivy_findings(report: dict) -> list[Finding]:
    if not isinstance(report, dict):
        raise ValueError("Trivy report must be a JSON object.")

    results = report.get("Results")

    if results is None:
        results = []

    if not isinstance(results, list):
        raise ValueError("Trivy report contains an invalid 'Results' list.")

    findings: list[Finding] = []

    for result_index, result in enumerate(results):
        if not isinstance(result, dict):
            raise ValueError(
                f"Trivy report contains an invalid 'Results[{result_index}]' object."
            )

        target = _path(result.get("Target"))

        vulnerabilities = _validate_list(
            result.get("Vulnerabilities"),
            "Vulnerabilities",
            result_index,
        )

        misconfigurations = _validate_list(
            result.get("Misconfigurations"),
            "Misconfigurations",
            result_index,
        )

        for item in vulnerabilities:
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
                if fixed
                else (
                    "Check the advisory and upgrade to a supported, "
                    "patched version if available."
                )
            )

            findings.append(
                Finding(
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
                )
            )

        for item in misconfigurations:
            severity = SEVERITIES.get(
                str(item.get("Severity", "")).upper(),
                FindingSeverity.INFORMATIONAL,
            )

            rule_id = str(item.get("ID") or item.get("AVDID") or "unknown")

            metadata = item.get("CauseMetadata")

            if metadata is None:
                metadata = {}

            if not isinstance(metadata, dict):
                raise ValueError("Trivy report contains invalid 'CauseMetadata'.")

            start_line = metadata.get("StartLine")

            if start_line is not None and (
                not isinstance(start_line, int)
                or isinstance(start_line, bool)
                or start_line < 1
            ):
                raise ValueError("Trivy report contains an invalid 'StartLine'.")

            file = target
            title = str(item.get("Title") or rule_id)
            description = str(item.get("Description") or item.get("Message") or title)

            findings.append(
                Finding(
                    scanner="trivy",
                    category=FindingCategory.CONFIGURATION,
                    severity=severity,
                    confidence=None,
                    title=title,
                    description=description,
                    file=file,
                    line=start_line,
                    remediation=item.get("Resolution"),
                    rule_id=rule_id,
                    fingerprint=_fingerprint("trivy", rule_id, file, start_line),
                )
            )

    return findings
