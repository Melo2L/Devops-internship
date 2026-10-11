from dataclasses import dataclass, field

from backend.services.project_analyzer import ProjectAnalysis


@dataclass
class PlannedScan:
    scanner: str
    enabled: bool
    reason: str


@dataclass
class ScanPlan:
    scans: list[PlannedScan] = field(default_factory=list)

    @property
    def enabled_scanners(self) -> list[str]:
        return [scan.scanner for scan in self.scans if scan.enabled]

    @property
    def skipped_scanners(self) -> list[str]:
        return [scan.scanner for scan in self.scans if not scan.enabled]


def create_scan_plan(
    analysis: ProjectAnalysis,
) -> ScanPlan:
    """
    Build a security scanning plan based on project intelligence.

    The planner only decides which scanners should run.
    It does not execute scanners.
    """

    scans: list[PlannedScan] = []

    # SAST — source-code security analysis.
    source_languages = {
        "Python",
        "JavaScript",
        "TypeScript",
        "Java",
        "Go",
        "Rust",
        "C",
        "C/C++",
        "C++",
        "C#",
        "PHP",
        "Ruby",
        "Kotlin",
        "Swift",
    }

    detected_source_languages = source_languages & set(analysis.languages)

    if detected_source_languages:
        languages = ", ".join(sorted(detected_source_languages))

        scans.append(
            PlannedScan(
                scanner="semgrep",
                enabled=True,
                reason=(f"Source code detected: {languages}."),
            )
        )
    else:
        scans.append(
            PlannedScan(
                scanner="semgrep",
                enabled=False,
                reason="No supported source languages detected.",
            )
        )

    # Secrets detection should be performed on every project.
    scans.append(
        PlannedScan(
            scanner="gitleaks",
            enabled=True,
            reason=("Secret detection is relevant to every project."),
        )
    )

    # Dependency / filesystem analysis.
    dependency_files = {
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "pom.xml",
        "build.gradle",
        "go.mod",
        "Cargo.toml",
    }

    detected_dependency_files = {
        path.split("/")[-1] for path in analysis.detected_files
    }

    has_docker = "Docker" in analysis.technologies

    if dependency_files & detected_dependency_files or has_docker:
        scans.append(
            PlannedScan(
                scanner="trivy",
                enabled=True,
                reason=("Dependency or container artifacts detected."),
            )
        )
    else:
        scans.append(
            PlannedScan(
                scanner="trivy",
                enabled=False,
                reason=("No dependency or container artifacts detected."),
            )
        )

    # Infrastructure as Code analysis.
    has_terraform = "Terraform" in analysis.technologies
    has_kubernetes = "Kubernetes" in analysis.technologies

    if has_terraform or has_kubernetes:
        detected_iac = []

        if has_terraform:
            detected_iac.append("Terraform")

        if has_kubernetes:
            detected_iac.append("Kubernetes")

        scans.append(
            PlannedScan(
                scanner="checkov",
                enabled=True,
                reason=(
                    "Infrastructure as Code detected: " + ", ".join(detected_iac) + "."
                ),
            )
        )
    else:
        scans.append(
            PlannedScan(
                scanner="checkov",
                enabled=False,
                reason=("No supported Infrastructure as Code detected."),
            )
        )

    return ScanPlan(scans=scans)
