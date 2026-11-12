import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from backend.scanners.trivy import scan_trivy


def make_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    return project


def test_trivy_requires_executable(
    tmp_path: Path,
) -> None:
    with (
        patch(
            "backend.scanners.trivy.shutil.which",
            return_value=None,
        ),
        pytest.raises(
            RuntimeError,
            match="Trivy is not installed",
        ),
    ):
        scan_trivy(tmp_path)


def test_trivy_parses_valid_json(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    report = {"Results": []}

    with (
        patch(
            "backend.scanners.trivy.shutil.which",
            return_value="/usr/bin/trivy",
        ),
        patch(
            "backend.scanners.trivy.subprocess.run",
            return_value=Mock(
                returncode=0,
                stdout=json.dumps(report),
                stderr="",
            ),
        ),
    ):
        result = scan_trivy(project)

    assert result == report


def test_trivy_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)

    with (
        patch(
            "backend.scanners.trivy.shutil.which",
            return_value="/usr/bin/trivy",
        ),
        patch(
            "backend.scanners.trivy.subprocess.run",
            return_value=Mock(
                returncode=0,
                stdout="{invalid json",
                stderr="",
            ),
        ),
        pytest.raises(
            RuntimeError,
            match="Trivy returned invalid JSON",
        ),
    ):
        scan_trivy(project)


def test_trivy_rejects_non_object_json(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)

    with (
        patch(
            "backend.scanners.trivy.shutil.which",
            return_value="/usr/bin/trivy",
        ),
        patch(
            "backend.scanners.trivy.subprocess.run",
            return_value=Mock(
                returncode=0,
                stdout=json.dumps([]),
                stderr="",
            ),
        ),
        pytest.raises(
            RuntimeError,
            match="Trivy returned an unexpected JSON structure",
        ),
    ):
        scan_trivy(project)


def test_trivy_rejects_failed_process(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)

    with (
        patch(
            "backend.scanners.trivy.shutil.which",
            return_value="/usr/bin/trivy",
        ),
        patch(
            "backend.scanners.trivy.subprocess.run",
            return_value=Mock(
                returncode=2,
                stdout="",
                stderr="scanner crashed",
            ),
        ),
        pytest.raises(RuntimeError) as error,
    ):
        scan_trivy(project)

    assert "exit code 2" in str(error.value)
    assert "scanner crashed" in str(error.value)


def test_trivy_handles_timeout(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)

    with (
        patch(
            "backend.scanners.trivy.shutil.which",
            return_value="/usr/bin/trivy",
        ),
        patch(
            "backend.scanners.trivy.subprocess.run",
            side_effect=subprocess.TimeoutExpired(
                cmd="trivy",
                timeout=900,
            ),
        ),
        pytest.raises(RuntimeError) as error,
    ):
        scan_trivy(project)

    assert str(error.value) == ("Trivy scan exceeded the 900-second timeout.")


def test_trivy_requires_project_directory(
    tmp_path: Path,
) -> None:
    missing_project = tmp_path / "missing-project"

    with (
        patch(
            "backend.scanners.trivy.shutil.which",
            return_value="/usr/bin/trivy",
        ),
        patch(
            "backend.scanners.trivy.subprocess.run",
            return_value=Mock(
                returncode=0,
                stdout=json.dumps({"Results": []}),
                stderr="",
            ),
        ) as run,
        pytest.raises(
            ValueError,
            match="Project directory does not exist",
        ),
    ):
        scan_trivy(missing_project)

    run.assert_not_called()


@pytest.mark.parametrize(
    ("report", "expected_message"),
    [
        (
            {"Results": {}},
            "Trivy report contains an invalid 'Results' list.",
        ),
        (
            {"Results": "invalid"},
            "Trivy report contains an invalid 'Results' list.",
        ),
        (
            {"Results": [None]},
            "Trivy report contains an invalid 'Results[0]' object.",
        ),
    ],
)
def test_trivy_rejects_invalid_results_structure(
    tmp_path: Path,
    report: dict,
    expected_message: str,
) -> None:
    project = make_project(tmp_path)

    with (
        patch(
            "backend.scanners.trivy.shutil.which",
            return_value="/usr/bin/trivy",
        ),
        patch(
            "backend.scanners.trivy.subprocess.run",
            return_value=Mock(
                returncode=0,
                stdout=json.dumps(report),
                stderr="",
            ),
        ),
        pytest.raises(RuntimeError) as error,
    ):
        scan_trivy(project)

    assert str(error.value) == expected_message
