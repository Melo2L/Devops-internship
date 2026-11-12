import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.scanners.checkov import scan_checkov


def _report() -> list[dict]:
    return [
        {
            "check_type": "terraform",
            "results": {
                "failed_checks": [
                    {
                        "check_id": "CKV_AWS_1",
                        "check_name": "Example security check",
                    }
                ]
            },
            "summary": {"failed": 1},
        }
    ]


def _mock_result(
    returncode: int = 0,
    stdout: str | None = None,
    stderr: str = "",
) -> Mock:
    return Mock(
        returncode=returncode,
        stdout=json.dumps(_report()) if stdout is None else stdout,
        stderr=stderr,
    )


def test_checkov_requires_executable(tmp_path: Path) -> None:
    with (
        patch("backend.scanners.checkov.shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="Checkov is not installed"),
    ):
        scan_checkov(tmp_path)


def test_checkov_parses_valid_json(tmp_path: Path) -> None:
    with (
        patch(
            "backend.scanners.checkov.shutil.which",
            return_value="/usr/bin/checkov",
        ),
        patch(
            "backend.scanners.checkov.subprocess.run",
            return_value=_mock_result(),
        ) as run,
    ):
        report = scan_checkov(tmp_path)

    assert report == _report()

    command = run.call_args.args[0]
    assert command[1:] == [
        "-d",
        str(tmp_path.resolve()),
        "-o",
        "json",
        "--quiet",
    ]
    assert run.call_args.kwargs["timeout"] == 900
    assert run.call_args.kwargs["check"] is False


def test_checkov_accepts_valid_report_with_failed_checks(
    tmp_path: Path,
) -> None:
    with (
        patch(
            "backend.scanners.checkov.shutil.which",
            return_value="/usr/bin/checkov",
        ),
        patch(
            "backend.scanners.checkov.subprocess.run",
            return_value=_mock_result(returncode=1),
        ),
    ):
        assert scan_checkov(tmp_path) == _report()


def test_checkov_rejects_crash_exit_code_with_valid_json(
    tmp_path: Path,
) -> None:
    with (
        patch(
            "backend.scanners.checkov.shutil.which",
            return_value="/usr/bin/checkov",
        ),
        patch(
            "backend.scanners.checkov.subprocess.run",
            return_value=_mock_result(returncode=2),
        ),
        pytest.raises(RuntimeError),
    ):
        scan_checkov(tmp_path)


def test_checkov_rejects_invalid_json(tmp_path: Path) -> None:
    with (
        patch(
            "backend.scanners.checkov.shutil.which",
            return_value="/usr/bin/checkov",
        ),
        patch(
            "backend.scanners.checkov.subprocess.run",
            return_value=_mock_result(stdout="{invalid json"),
        ),
        pytest.raises(RuntimeError, match="valid JSON"),
    ):
        scan_checkov(tmp_path)


@pytest.mark.parametrize(
    "stdout",
    [
        json.dumps("unexpected"),
        json.dumps([{"valid": True}, "invalid"]),
    ],
)
def test_checkov_rejects_unexpected_json_structure(
    tmp_path: Path,
    stdout: str,
) -> None:
    with (
        patch(
            "backend.scanners.checkov.shutil.which",
            return_value="/usr/bin/checkov",
        ),
        patch(
            "backend.scanners.checkov.subprocess.run",
            return_value=_mock_result(stdout=stdout),
        ),
        pytest.raises(RuntimeError, match="unexpected JSON structure"),
    ):
        scan_checkov(tmp_path)


def test_checkov_timeout_raises_runtime_error(
    tmp_path: Path,
) -> None:
    with (
        patch(
            "backend.scanners.checkov.shutil.which",
            return_value="/usr/bin/checkov",
        ),
        patch(
            "backend.scanners.checkov.subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd="checkov",
                timeout=900,
            ),
        ),
        pytest.raises(
            RuntimeError,
            match="Checkov scan timed out",
        ),
    ):
        scan_checkov(tmp_path)
