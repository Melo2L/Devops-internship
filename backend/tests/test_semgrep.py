import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.scanners.semgrep import (
    SemgrepFinding,
    SemgrepScanner,
)


def make_scanner(
    tmp_path: Path,
    *,
    timeout_seconds: int = 300,
    config: str = "auto",
) -> tuple[SemgrepScanner, Path]:
    executable = tmp_path / "semgrep"
    executable.touch()

    project = tmp_path / "project"
    project.mkdir()

    scanner = SemgrepScanner(
        executable_path=executable,
        timeout_seconds=timeout_seconds,
        config=config,
    )

    return scanner, project


def test_semgrep_requires_executable(
    tmp_path: Path,
) -> None:
    scanner = SemgrepScanner(
        executable_path=tmp_path / "missing-semgrep",
    )

    with pytest.raises(
        FileNotFoundError,
        match="Semgrep executable not found",
    ):
        scanner.scan(tmp_path)


def test_semgrep_requires_project_directory(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "semgrep"
    executable.touch()

    scanner = SemgrepScanner(
        executable_path=executable,
    )

    with pytest.raises(
        ValueError,
        match="Project directory does not exist",
    ):
        scanner.scan(tmp_path / "missing-project")


def test_semgrep_finding_model() -> None:
    finding = SemgrepFinding(
        check_id="python.lang.security.audit.eval-detected",
        message="Detected use of eval().",
        severity="WARNING",
        file="app.py",
        start_line=10,
        end_line=10,
        fingerprint="abc123",
    )

    assert finding.check_id == "python.lang.security.audit.eval-detected"
    assert finding.message == "Detected use of eval()."
    assert finding.severity == "WARNING"
    assert finding.file == "app.py"
    assert finding.start_line == 10
    assert finding.end_line == 10
    assert finding.fingerprint == "abc123"


def test_semgrep_parses_json_output(
    tmp_path: Path,
) -> None:
    scanner, project = make_scanner(
        tmp_path,
        config="p/security-audit",
    )

    report = {
        "results": [
            {
                "check_id": "python.lang.security.audit.eval-detected",
                "path": "app.py",
                "start": {"line": 10},
                "end": {"line": 12},
                "extra": {
                    "message": "Detected use of eval().",
                    "severity": "WARNING",
                    "fingerprint": "abc123",
                },
            }
        ]
    }

    with patch(
        "backend.scanners.semgrep.subprocess.run",
        return_value=Mock(
            returncode=0,
            stdout=json.dumps(report),
            stderr="",
        ),
    ) as run:
        findings = scanner.scan(project)

    assert len(findings) == 1
    assert findings[0] == SemgrepFinding(
        check_id="python.lang.security.audit.eval-detected",
        message="Detected use of eval().",
        severity="WARNING",
        file="app.py",
        start_line=10,
        end_line=12,
        fingerprint="abc123",
    )

    command = run.call_args.args[0]
    assert command[1:5] == [
        "scan",
        "--json",
        "--config",
        "p/security-audit",
    ]
    assert command[-1] == str(project)
    assert run.call_args.kwargs["timeout"] == 300


def test_semgrep_returns_empty_for_empty_stdout(
    tmp_path: Path,
) -> None:
    scanner, project = make_scanner(tmp_path)

    with patch(
        "backend.scanners.semgrep.subprocess.run",
        return_value=Mock(
            returncode=0,
            stdout="  \n",
            stderr="",
        ),
    ):
        assert scanner.scan(project) == []


def test_semgrep_empty_stdout_with_exit_one_is_empty(
    tmp_path: Path,
) -> None:
    scanner, project = make_scanner(tmp_path)

    with patch(
        "backend.scanners.semgrep.subprocess.run",
        return_value=Mock(
            returncode=1,
            stdout="",
            stderr="",
        ),
    ):
        assert scanner.scan(project) == []


@pytest.mark.parametrize(
    ("returncode", "stderr", "expected"),
    [
        (2, "", "Semgrep execution failed."),
        (
            2,
            "permission denied",
            "Semgrep execution failed. Details: permission denied",
        ),
    ],
)
def test_semgrep_rejects_failed_process_without_output(
    tmp_path: Path,
    returncode: int,
    stderr: str,
    expected: str,
) -> None:
    scanner, project = make_scanner(tmp_path)

    with (
        patch(
            "backend.scanners.semgrep.subprocess.run",
            return_value=Mock(
                returncode=returncode,
                stdout="",
                stderr=stderr,
            ),
        ),
        pytest.raises(RuntimeError) as error,
    ):
        scanner.scan(project)

    assert str(error.value) == expected


def test_semgrep_timeout_raises_runtime_error(
    tmp_path: Path,
) -> None:
    scanner, project = make_scanner(
        tmp_path,
        timeout_seconds=10,
    )

    with (
        patch(
            "backend.scanners.semgrep.subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd="semgrep",
                timeout=10,
            ),
        ),
        pytest.raises(
            RuntimeError,
            match="Semgrep scan timed out",
        ),
    ):
        scanner.scan(project)


def test_semgrep_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    scanner, project = make_scanner(tmp_path)

    with (
        patch(
            "backend.scanners.semgrep.subprocess.run",
            return_value=Mock(
                returncode=0,
                stdout="{invalid json",
                stderr="",
            ),
        ),
        pytest.raises(
            RuntimeError,
            match="Semgrep produced invalid JSON output",
        ),
    ):
        scanner.scan(project)


@pytest.mark.parametrize(
    ("returncode", "stderr"),
    [
        (2, ""),
        (2, "scanner crashed"),
    ],
)
def test_semgrep_rejects_failed_process_with_json(
    tmp_path: Path,
    returncode: int,
    stderr: str,
) -> None:
    scanner, project = make_scanner(tmp_path)

    with (
        patch(
            "backend.scanners.semgrep.subprocess.run",
            return_value=Mock(
                returncode=returncode,
                stdout=json.dumps({"results": []}),
                stderr=stderr,
            ),
        ),
        pytest.raises(RuntimeError) as error,
    ):
        scanner.scan(project)

    expected = "Semgrep execution failed."
    if stderr:
        expected += f" Details: {stderr}"

    assert str(error.value) == expected


def test_semgrep_normalizes_missing_optional_fields(
    tmp_path: Path,
) -> None:
    scanner, project = make_scanner(tmp_path)

    report = {
        "results": [
            {},
        ]
    }

    with patch(
        "backend.scanners.semgrep.subprocess.run",
        return_value=Mock(
            returncode=0,
            stdout=json.dumps(report),
            stderr="",
        ),
    ):
        findings = scanner.scan(project)

    assert findings == [
        SemgrepFinding(
            check_id="unknown",
            message="Potential security issue detected.",
            severity="INFO",
            file="",
            start_line=None,
            end_line=None,
            fingerprint=None,
        )
    ]


def test_semgrep_returns_empty_when_results_key_is_missing(
    tmp_path: Path,
) -> None:
    scanner, project = make_scanner(tmp_path)

    with patch(
        "backend.scanners.semgrep.subprocess.run",
        return_value=Mock(
            returncode=0,
            stdout=json.dumps({"errors": []}),
            stderr="",
        ),
    ):
        assert scanner.scan(project) == []
