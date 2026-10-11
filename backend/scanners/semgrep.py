import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SEMGREP_PATH = Path(
    os.getenv(
        "SEMGREP_PATH",
        "semgrep",
    )
)


@dataclass
class SemgrepFinding:
    check_id: str
    message: str
    severity: str
    file: str
    start_line: int | None
    end_line: int | None
    fingerprint: str | None


class SemgrepScanner:
    def __init__(
        self,
        executable_path: Path = DEFAULT_SEMGREP_PATH,
        timeout_seconds: int = 300,
        config: str = "/app/backend/rules/python-security.yml",
    ) -> None:
        self.executable_path = executable_path
        self.timeout_seconds = timeout_seconds
        self.config = config

    def scan(self, project_path: Path) -> list[SemgrepFinding]:
        executable = str(self.executable_path)

        # Resolve absolute paths directly and command names through PATH.
        if self.executable_path.is_absolute():
            if not self.executable_path.is_file():
                raise FileNotFoundError(
                    f"Semgrep executable not found: {self.executable_path}"
                )
        else:
            resolved_executable = shutil.which(executable)

            if resolved_executable is None:
                raise FileNotFoundError(
                    f"Semgrep executable not found in PATH: {executable}"
                )

            executable = resolved_executable

        if not project_path.is_dir():
            raise ValueError(
                f"Project directory does not exist: {project_path}"
            )

        command = [
            executable,
            "scan",
            "--json",
            "--config",
            self.config,
            str(project_path),
        ]

        env = os.environ.copy()
        env["SEMGREP_SEND_METRICS"] = "off"
        env["SEMGREP_ENABLE_VERSION_CHECK"] = "0"

        try:
            result = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Semgrep scan timed out.") from exc

        stdout = result.stdout.strip()

        if not stdout:
            stderr = result.stderr.strip()

            if result.returncode not in (0, 1):
                raise RuntimeError(
                    "Semgrep execution failed."
                    + (f" Details: {stderr}" if stderr else "")
                )

            return []

        try:
            report = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Semgrep produced invalid JSON output."
            ) from exc

        if result.returncode not in (0, 1):
            stderr = result.stderr.strip()

            raise RuntimeError(
                "Semgrep execution failed."
                + (f" Details: {stderr}" if stderr else "")
            )

        findings = []

        for result_data in report.get("results", []):
            extra = result_data.get("extra", {})
            start = result_data.get("start", {})
            end = result_data.get("end", {})

            findings.append(
                SemgrepFinding(
                    check_id=str(
                        result_data.get(
                            "check_id",
                            "unknown",
                        )
                    ),
                    message=str(
                        extra.get(
                            "message",
                            "Potential security issue detected.",
                        )
                    ),
                    severity=str(
                        extra.get(
                            "severity",
                            "INFO",
                        )
                    ),
                    file=str(
                        result_data.get(
                            "path",
                            "",
                        )
                    ),
                    start_line=(
                        int(start["line"])
                        if start.get("line") is not None
                        else None
                    ),
                    end_line=(
                        int(end["line"])
                        if end.get("line") is not None
                        else None
                    ),
                    fingerprint=(
                        str(extra["fingerprint"])
                        if extra.get("fingerprint")
                        else None
                    ),
                )
            )

        return findings