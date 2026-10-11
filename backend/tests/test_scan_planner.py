from backend.services.project_analyzer import ProjectAnalysis
from backend.services.scan_planner import create_scan_plan


def test_javascript_project_enables_expected_scanners() -> None:
    analysis = ProjectAnalysis(
        total_files=100,
        languages={
            "TypeScript": 80,
            "CSS": 10,
        },
        technologies=[
            "React",
            "TypeScript",
            "Vite",
            "Tailwind CSS",
        ],
        detected_files=[
            "frontend/package.json",
        ],
    )

    plan = create_scan_plan(analysis)

    assert "semgrep" in plan.enabled_scanners
    assert "gitleaks" in plan.enabled_scanners
    assert "trivy" in plan.enabled_scanners

    assert "checkov" in plan.skipped_scanners


def test_terraform_project_enables_checkov() -> None:
    analysis = ProjectAnalysis(
        total_files=50,
        languages={
            "HCL": 10,
        },
        technologies=[
            "Terraform",
        ],
        detected_files=[
            "infra/main.tf",
            "infra/terraform.lock.hcl",
        ],
    )

    plan = create_scan_plan(analysis)

    assert "gitleaks" in plan.enabled_scanners
    assert "checkov" in plan.enabled_scanners

    assert "checkov" not in plan.skipped_scanners


def test_project_without_source_code_skips_semgrep() -> None:
    analysis = ProjectAnalysis(
        total_files=5,
        languages={
            "Markdown": 5,
        },
        technologies=[],
        detected_files=[
            "README.md",
        ],
    )

    plan = create_scan_plan(analysis)

    assert "semgrep" in plan.skipped_scanners
    assert "gitleaks" in plan.enabled_scanners
    assert "trivy" in plan.skipped_scanners
    assert "checkov" in plan.skipped_scanners


def test_project_with_terraform_and_kubernetes_enables_checkov() -> None:
    analysis = ProjectAnalysis(
        total_files=10,
        languages={"HCL": 5, "YAML": 5},
        technologies=["Terraform", "Kubernetes"],
        detected_files=[
            "infra/main.tf",
            "k8s/deployment.yaml",
        ],
    )

    plan = create_scan_plan(analysis)

    assert "checkov" in plan.enabled_scanners
    assert "checkov" not in plan.skipped_scanners
