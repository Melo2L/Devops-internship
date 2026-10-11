import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.scanners.gitleaks import (
    GitleaksScanner,
)


def create_scanner(
    executable_path: Path,
    timeout_seconds: int = 120,
) -> GitleaksScanner:
    executable_path.touch()

    return GitleaksScanner(
        executable_path=executable_path,
        timeout_seconds=timeout_seconds,
    )


def test_gitleaks_rejects_missing_executable(
    tmp_path: Path,
) -> None:
    scanner = GitleaksScanner(
        executable_path=tmp_path / "missing-gitleaks",
    )

    with pytest.raises(
        FileNotFoundError,
        match="Gitleaks executable not found",
    ):
        scanner.scan(tmp_path)


def test_gitleaks_rejects_missing_project_directory(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "gitleaks"
    executable.touch()

    scanner = GitleaksScanner(
        executable_path=executable,
    )

    with pytest.raises(
        ValueError,
        match="Project directory does not exist",
    ):
        scanner.scan(tmp_path / "missing-project")


def test_gitleaks_timeout_raises_runtime_error(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "gitleaks"
    project = tmp_path / "project"
    executable.touch()
    project.mkdir()

    scanner = GitleaksScanner(
        executable_path=executable,
        timeout_seconds=5,
    )

    with (
        patch(
            "backend.scanners.gitleaks.subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd="gitleaks",
                timeout=5,
            ),
        ),
        pytest.raises(
            RuntimeError,
            match="Gitleaks scan timed out",
        ),
    ):
        scanner.scan(project)


def test_gitleaks_rejects_invalid_json_report(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "gitleaks"
    project = tmp_path / "project"
    executable.touch()
    project.mkdir()

    scanner = GitleaksScanner(
        executable_path=executable,
    )

    def fake_run(*args: object, **kwargs: object) -> Mock:
        report_path = project / ".gitleaks-report.json"
        report_path.write_text(
            "{invalid json",
            encoding="utf-8",
        )

        return Mock(returncode=0, stderr="")

    with (
        patch(
            "backend.scanners.gitleaks.subprocess.run",
            side_effect=fake_run,
        ),
        pytest.raises(
            RuntimeError,
            match="Gitleaks produced an invalid JSON report",
        ),
    ):
        scanner.scan(project)

    assert not (project / ".gitleaks-report.json").exists()


@pytest.mark.parametrize(
    ("stderr", "expected_message"),
    [
        (
            "",
            "Gitleaks execution failed.",
        ),
        (
            "permission denied",
            "Gitleaks execution failed. Details: permission denied",
        ),
    ],
)
def test_gitleaks_rejects_unexpected_exit_code(
    tmp_path: Path,
    stderr: str,
    expected_message: str,
) -> None:
    executable = tmp_path / "gitleaks"
    project = tmp_path / "project"
    executable.touch()
    project.mkdir()

    scanner = GitleaksScanner(
        executable_path=executable,
    )

    with (
        patch(
            "backend.scanners.gitleaks.subprocess.run",
            return_value=Mock(
                returncode=2,
                stderr=stderr,
            ),
        ),
        pytest.raises(
            RuntimeError,
            match="^" + expected_message.replace(".", r"\.") + "$",
        ),
    ):
        scanner.scan(project)


def test_gitleaks_normalizes_findings_and_removes_report(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "gitleaks"
    project = tmp_path / "project"
    executable.touch()
    project.mkdir()

    scanner = GitleaksScanner(
        executable_path=executable,
    )

    report = [
        {
            "RuleID": "test-secret",
            "Description": "Test credential",
            "File": "config.py",
            "StartLine": 12,
            "Secret": "REDACTED_TEST_VALUE",
            "Commit": "abc123",
        },
        {
            "RuleID": "minimal-rule",
        },
    ]

    def fake_run(*args: object, **kwargs: object) -> Mock:
        report_path = project / ".gitleaks-report.json"
        report_path.write_text(
            json.dumps(report),
            encoding="utf-8",
        )

        return Mock(returncode=1, stderr="")

    with patch(
        "backend.scanners.gitleaks.subprocess.run",
        side_effect=fake_run,
    ):
        findings = scanner.scan(project)

    assert len(findings) == 2

    assert findings[0].rule_id == "test-secret"
    assert findings[0].description == "Test credential"
    assert findings[0].severity == "High"
    assert findings[0].file == "config.py"
    assert findings[0].line == 12
    assert findings[0].secret == "REDACTED_TEST_VALUE"
    assert findings[0].commit == "abc123"

    assert findings[1].rule_id == "minimal-rule"
    assert findings[1].description == "Potential secret detected."
    assert findings[1].file == ""
    assert findings[1].line is None
    assert findings[1].secret is None
    assert findings[1].commit is None

    assert not (project / ".gitleaks-report.json").exists()
