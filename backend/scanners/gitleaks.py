import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_GITLEAKS_PATH = Path(
    os.getenv(
        "GITLEAKS_PATH",
        "/usr/local/bin/gitleaks",
    )
)


@dataclass
class GitleaksFinding:
    rule_id: str
    description: str
    severity: str
    file: str
    line: int | None
    commit: str | None


class GitleaksScanner:
    """
    Execute Gitleaks against an extracted project directory.

    The scanned project is treated as untrusted input.
    Gitleaks only performs static secret detection.
    """

    def __init__(
        self,
        executable_path: Path = DEFAULT_GITLEAKS_PATH,
        timeout_seconds: int = 120,
    ) -> None:
        self.executable_path = executable_path
        self.timeout_seconds = timeout_seconds

    def scan(self, project_path: Path) -> list[GitleaksFinding]:
        """
        Run Gitleaks and return normalized findings.
        """

        if not self.executable_path.is_file():
            raise FileNotFoundError(
                f"Gitleaks executable not found: {self.executable_path}"
            )

        if not project_path.is_dir():
            raise ValueError(f"Project directory does not exist: {project_path}")

        with tempfile.NamedTemporaryFile(
            suffix=".json",
            delete=False,
        ) as report_file:
            report_path = Path(report_file.name)

        command = [
            str(self.executable_path),
            "dir",
            str(project_path),
            "--report-format",
            "json",
            "--report-path",
            str(report_path),
            "--no-banner",
        ]

        try:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Gitleaks scan timed out.") from exc

            if result.returncode not in (0, 1):
                stderr = result.stderr.strip()
                raise RuntimeError(
                    "Gitleaks execution failed."
                    + (f" Details: {stderr}" if stderr else "")
                )

            try:
                if report_path.exists():
                    report_data = json.loads(report_path.read_text(encoding="utf-8"))
                else:
                    report_data = []
            except (json.JSONDecodeError, OSError) as exc:
                raise RuntimeError("Gitleaks produced an invalid JSON report.") from exc

        finally:
            report_path.unlink(missing_ok=True)

        findings: list[GitleaksFinding] = []

        for finding in report_data:
            findings.append(
                GitleaksFinding(
                    rule_id=str(finding.get("RuleID", "unknown")),
                    description=str(
                        finding.get(
                            "Description",
                            "Potential secret detected.",
                        )
                    ),
                    severity="High",
                    file=str(finding.get("File", "")),
                    line=(
                        int(finding["StartLine"]) if finding.get("StartLine") else None
                    ),
                    commit=(str(finding["Commit"]) if finding.get("Commit") else None),
                )
            )

        return findings
