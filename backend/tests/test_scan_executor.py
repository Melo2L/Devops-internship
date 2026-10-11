from pathlib import Path
from tempfile import TemporaryDirectory

from backend.services.project_analyzer import ProjectAnalysis
from backend.services.scan_executor import execute_scan_plan
from backend.services.scan_planner import (
    PlannedScan,
    ScanPlan,
    create_scan_plan,
)


def test_scan_executor_runs_gitleaks() -> None:
    with TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        (project_path / "main.py").write_text(
            "print('hello')",
            encoding="utf-8",
        )

        plan = ScanPlan(
            scans=[
                PlannedScan(
                    scanner="gitleaks",
                    enabled=True,
                    reason="Secret detection is enabled.",
                )
            ]
        )

        results = execute_scan_plan(
            plan,
            project_path,
        )

        assert len(results) == 1

        result = results[0]

        assert result.scanner == "gitleaks"
        assert result.findings == []


def test_scan_executor_skips_disabled_gitleaks() -> None:
    with TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        (project_path / "main.py").write_text(
            "print('hello')",
            encoding="utf-8",
        )

        plan = ScanPlan(
            scans=[
                PlannedScan(
                    scanner="gitleaks",
                    enabled=False,
                    reason="Scanner disabled for this test.",
                )
            ]
        )

        results = execute_scan_plan(
            plan,
            project_path,
        )

        assert results == []


def test_scan_executor_uses_real_scan_plan(monkeypatch) -> None:
    with TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        (project_path / "main.py").write_text(
            "print('hello')",
            encoding="utf-8",
        )

        analysis = ProjectAnalysis(
            total_files=1,
            languages={
                "Python": 1,
            },
            technologies=[],
            detected_files=[],
        )

        plan = create_scan_plan(analysis)

        def fake_semgrep_scan(self, project_path):
            return []

        monkeypatch.setattr(
            "backend.scanners.semgrep.SemgrepScanner.scan",
            fake_semgrep_scan,
        )

        results = execute_scan_plan(
            plan,
            project_path,
        )

        assert "gitleaks" in plan.enabled_scanners

        assert len(results) == 2
        assert {result.scanner for result in results} == {
            "gitleaks",
            "semgrep",
        }
        assert results[0].scanner == "gitleaks"
        assert results[0].findings == []


def test_scan_executor_runs_semgrep(
    monkeypatch,
    tmp_path,
) -> None:
    from backend.models.findings import (
        FindingCategory,
        FindingSeverity,
    )
    from backend.scanners.semgrep import SemgrepFinding
    from backend.services.scan_executor import execute_scan_plan
    from backend.services.scan_planner import (
        PlannedScan,
        ScanPlan,
    )

    plan = ScanPlan(
        scans=[
            PlannedScan(
                scanner="semgrep",
                enabled=True,
                reason="Test Semgrep execution.",
            )
        ]
    )

    def fake_scan(self, project_path):
        return [
            SemgrepFinding(
                check_id="test-rule",
                message="Test Semgrep finding",
                severity="WARNING",
                file="app.py",
                start_line=10,
                end_line=10,
                fingerprint="test-fingerprint",
            )
        ]

    monkeypatch.setattr(
        "backend.scanners.semgrep.SemgrepScanner.scan",
        fake_scan,
    )

    results = execute_scan_plan(
        plan,
        tmp_path,
    )

    assert len(results) == 1
    assert results[0].scanner == "semgrep"
    assert len(results[0].findings) == 1

    finding = results[0].findings[0]

    assert finding.scanner == "semgrep"
    assert finding.category == FindingCategory.SOURCE_CODE
    assert finding.severity == FindingSeverity.MEDIUM
    assert finding.rule_id == "test-rule"
    assert finding.file == "app.py"
    assert finding.line == 10
    assert finding.fingerprint == "test-fingerprint"
