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


def test_checkov_parses_valid_json_and_uses_isolated_workspace(
    tmp_path: Path,
) -> None:
    (tmp_path / ".checkov.yaml").write_text(
        "external-checks-dir: [/tmp/untrusted]\n"
    )
    (tmp_path / ".checkov.yml").write_text(
        "external-checks-dir: [/tmp/untrusted]\n"
    )
    (tmp_path / "main.tf").write_text('resource "test" {}\n')
    (tmp_path / ".gitignore").write_text("*.tfstate\n")

    temporary_roots: list[Path] = []

    def inspect_isolated_run(command, **kwargs):
        scan_directory = Path(command[2])
        temporary_roots.append(Path(kwargs["cwd"]).parent)
        assert scan_directory != tmp_path.resolve()
        assert scan_directory.is_dir()
        assert not (scan_directory / ".checkov.yaml").exists()
        assert not (scan_directory / ".checkov.yml").exists()
        assert (scan_directory / "main.tf").is_file()
        assert (scan_directory / ".gitignore").is_file()

        assert Path(kwargs["cwd"]).is_dir()
        assert Path(kwargs["cwd"]) != tmp_path.resolve()
        assert Path(kwargs["env"]["HOME"]).is_dir()
        assert kwargs["env"]["HOME"] != str(Path.home())

        assert "CKV_TEST_SETTING" not in kwargs["env"]
        assert "CHECKOV_TEST_SETTING" not in kwargs["env"]

        return _mock_result()

    with (
        patch(
            "backend.scanners.checkov.shutil.which",
            return_value="/usr/bin/checkov",
        ),
        patch.dict(
            "os.environ",
            {
                "CKV_TEST_SETTING": "untrusted",
                "CHECKOV_TEST_SETTING": "untrusted",
            },
        ),
        patch(
            "backend.scanners.checkov.subprocess.run",
            side_effect=inspect_isolated_run,
        ) as run,
    ):
        report = scan_checkov(tmp_path)

    assert report == _report()
    assert len(temporary_roots) == 1
    assert not temporary_roots[0].exists()

    command = run.call_args.args[0]
    assert command[0] == "/usr/bin/checkov"
    assert command[1] == "-d"
    assert command[2].endswith("/project")
    assert command[3:] == ["-o", "json", "--quiet"]
    assert run.call_args.kwargs["timeout"] == 900
    assert run.call_args.kwargs["check"] is False

    # The original project remains untouched.
    assert (tmp_path / ".checkov.yaml").is_file()
    assert (tmp_path / ".checkov.yml").is_file()


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


def test_checkov_timeout_raises_runtime_error_and_cleans_workspace(
    tmp_path: Path,
) -> None:
    temporary_roots: list[Path] = []

    def simulate_timeout(command, **kwargs):
        temporary_roots.append(Path(kwargs["cwd"]).parent)
        raise subprocess.TimeoutExpired(
            cmd="checkov",
            timeout=900,
        )

    with (
        patch(
            "backend.scanners.checkov.shutil.which",
            return_value="/usr/bin/checkov",
        ),
        patch(
            "backend.scanners.checkov.subprocess.run",
            side_effect=simulate_timeout,
        ),
        pytest.raises(
            RuntimeError,
            match="Checkov scan timed out",
        ),
    ):
        scan_checkov(tmp_path)

    assert len(temporary_roots) == 1
    assert not temporary_roots[0].exists()
