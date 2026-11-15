import pytest

from backend.api.projects import determine_scan_status
from backend.scanners.trivy_normalizer import (
    _path,
    _validate_list,
    normalize_trivy_findings,
)
from backend.services.project_analyzer import (
    _find_project_file,
    analyze_project,
)
from backend.services.scan_executor import ScanExecutionResult


@pytest.mark.parametrize(
    ("results", "expected"),
    [
        ([], "completed"),
        ([ScanExecutionResult("gitleaks", [], "completed")], "completed"),
        ([ScanExecutionResult("gitleaks", [], "failed")], "failed"),
        (
            [
                ScanExecutionResult("gitleaks", [], "completed"),
                ScanExecutionResult("semgrep", [], "failed"),
            ],
            "partial",
        ),
    ],
)
def test_determine_scan_status_all_outcomes(results, expected):
    assert determine_scan_status(results) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "unknown"),
        ("", "unknown"),
        ("C:\\project\\src\\main.py", "project/src/main.py"),
        ("/project/src/main.py", "project/src/main.py"),
    ],
)
def test_trivy_path_normalization_edge_cases(value, expected):
    assert _path(value) == expected


def test_trivy_path_rejects_non_string():
    with pytest.raises(ValueError, match="invalid file path"):
        _path(123)


def test_trivy_validate_list_accepts_none():
    assert _validate_list(None, "Vulnerabilities", 0) == []


def test_trivy_validate_list_accepts_empty_list():
    assert _validate_list([], "Vulnerabilities", 0) == []


def test_trivy_validate_list_rejects_non_list():
    with pytest.raises(ValueError, match="invalid"):
        _validate_list({}, "Vulnerabilities", 0)


def test_trivy_validate_list_rejects_non_object_entries():
    with pytest.raises(ValueError, match="invalid"):
        _validate_list(["invalid"], "Vulnerabilities", 0)


def test_trivy_normalizer_accepts_missing_results():
    assert normalize_trivy_findings({}) == []


def test_trivy_normalizer_accepts_null_results():
    assert normalize_trivy_findings({"Results": None}) == []


def test_trivy_normalizer_accepts_null_finding_lists():
    report = {
        "Results": [
            {
                "Target": "requirements.txt",
                "Vulnerabilities": None,
                "Misconfigurations": None,
            }
        ]
    }
    assert normalize_trivy_findings(report) == []


def test_trivy_normalizer_rejects_invalid_cause_metadata():
    report = {
        "Results": [
            {
                "Target": "main.tf",
                "Misconfigurations": [
                    {
                        "ID": "TEST-001",
                        "CauseMetadata": "invalid",
                    }
                ],
            }
        ]
    }
    with pytest.raises(ValueError, match="CauseMetadata"):
        normalize_trivy_findings(report)


@pytest.mark.parametrize("line", [0, -1, "10", True])
def test_trivy_normalizer_rejects_invalid_start_line(line):
    report = {
        "Results": [
            {
                "Target": "main.tf",
                "Misconfigurations": [
                    {
                        "ID": "TEST-002",
                        "CauseMetadata": {"StartLine": line},
                    }
                ],
            }
        ]
    }
    with pytest.raises(ValueError, match="StartLine"):
        normalize_trivy_findings(report)


def test_project_analyzer_ignores_directory_matching_project_filename(tmp_path):
    (tmp_path / "package.json").mkdir()
    assert _find_project_file(tmp_path, "package.json") is None


def test_project_analyzer_ignores_empty_github_workflows_directory(tmp_path):
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)

    result = analyze_project(tmp_path)

    assert "GitHub Actions" not in result.technologies
    assert ".github/workflows" not in result.detected_files


def test_scan_executor_runs_checkov(monkeypatch, tmp_path):
    from backend.services.scan_executor import execute_scan_plan
    from backend.services.scan_planner import PlannedScan, ScanPlan

    monkeypatch.setattr(
        "backend.services.scan_executor.scan_checkov",
        lambda project_path: [],
    )

    plan = ScanPlan(
        scans=[PlannedScan("checkov", True, "Test Checkov.")],
    )

    results = execute_scan_plan(plan, tmp_path)

    assert len(results) == 1
    assert results[0].scanner == "checkov"
    assert results[0].status == "completed"


def test_scan_executor_rejects_unsupported_scanner(tmp_path):
    from backend.services.scan_executor import _execute_scanner

    with pytest.raises(ValueError):
        _execute_scanner("unsupported", tmp_path)


def test_checkov_accepts_json_object_report(monkeypatch, tmp_path):
    import json
    from unittest.mock import Mock

    from backend.scanners.checkov import scan_checkov

    report = {"check_type": "terraform", "results": {}}

    monkeypatch.setattr(
        "backend.scanners.checkov.shutil.which",
        lambda _: "/usr/bin/checkov",
    )
    monkeypatch.setattr(
        "backend.scanners.checkov.subprocess.run",
        lambda *args, **kwargs: Mock(
            returncode=0,
            stdout=json.dumps(report),
            stderr="",
        ),
    )

    assert scan_checkov(tmp_path) == [report]


def test_gitleaks_accepts_empty_report(monkeypatch, tmp_path):
    from pathlib import Path
    from unittest.mock import Mock

    from backend.scanners.gitleaks import GitleaksScanner

    executable = tmp_path / "gitleaks"
    executable.touch()
    project = tmp_path / "project"
    project.mkdir()

    scanner = GitleaksScanner(executable_path=executable)

    def fake_run(command, *args, **kwargs):
        report_path = Path(command[command.index("--report-path") + 1])
        report_path.write_text("[]", encoding="utf-8")
        return Mock(returncode=0, stderr="")

    monkeypatch.setattr(
        "backend.scanners.gitleaks.subprocess.run",
        fake_run,
    )

    assert scanner.scan(project) == []


def test_trivy_accepts_null_results(monkeypatch, tmp_path):
    import json
    from unittest.mock import Mock

    from backend.scanners.trivy import scan_trivy

    project = tmp_path / "project"
    project.mkdir()

    monkeypatch.setattr(
        "backend.scanners.trivy.shutil.which",
        lambda _: "/usr/bin/trivy",
    )
    monkeypatch.setattr(
        "backend.scanners.trivy.subprocess.run",
        lambda *args, **kwargs: Mock(
            returncode=0,
            stdout=json.dumps({"Results": None}),
            stderr="",
        ),
    )

    assert scan_trivy(project) == {"Results": None}


def test_trivy_accepts_empty_result_object(monkeypatch, tmp_path):
    import json
    from unittest.mock import Mock

    from backend.scanners.trivy import scan_trivy

    project = tmp_path / "project"
    project.mkdir()

    monkeypatch.setattr(
        "backend.scanners.trivy.shutil.which",
        lambda _: "/usr/bin/trivy",
    )
    monkeypatch.setattr(
        "backend.scanners.trivy.subprocess.run",
        lambda *args, **kwargs: Mock(
            returncode=0,
            stdout=json.dumps({"Results": [{}]}),
            stderr="",
        ),
    )

    assert scan_trivy(project) == {"Results": [{}]}


def test_semgrep_resolves_executable_from_path(monkeypatch, tmp_path):
    import json
    from pathlib import Path
    from unittest.mock import Mock

    from backend.scanners.semgrep import SemgrepScanner

    project = tmp_path / "project"
    project.mkdir()

    executable = tmp_path / "semgrep"
    executable.touch()

    scanner = SemgrepScanner(executable_path=Path("semgrep"))

    monkeypatch.setattr(
        "backend.scanners.semgrep.shutil.which",
        lambda name: str(executable) if name == "semgrep" else None,
    )
    monkeypatch.setattr(
        "backend.scanners.semgrep.subprocess.run",
        lambda *args, **kwargs: Mock(
            returncode=0,
            stdout=json.dumps({"results": []}),
            stderr="",
        ),
    )

    assert scanner.scan(project) == []


def test_gitleaks_accepts_missing_report_file(tmp_path):
    from unittest.mock import Mock, patch

    from backend.scanners.gitleaks import GitleaksScanner

    executable = tmp_path / "gitleaks"
    executable.touch()

    scanner = GitleaksScanner(executable_path=executable)

    def fake_run(command, *args, **kwargs):
        report_path = command[command.index("--report-path") + 1]
        from pathlib import Path
        Path(report_path).unlink(missing_ok=True)
        return Mock(returncode=0, stderr="")

    with patch(
        "backend.scanners.gitleaks.subprocess.run",
        side_effect=fake_run,
    ):
        assert scanner.scan(tmp_path) == []


def test_semgrep_raises_when_executable_is_not_in_path(tmp_path):
    from pathlib import Path
    from unittest.mock import patch

    from backend.scanners.semgrep import SemgrepScanner

    scanner = SemgrepScanner(executable_path=Path("semgrep"))

    with patch(
        "backend.scanners.semgrep.shutil.which",
        return_value=None,
    ), pytest.raises(FileNotFoundError, match="not found in PATH"):
        scanner.scan(tmp_path)
