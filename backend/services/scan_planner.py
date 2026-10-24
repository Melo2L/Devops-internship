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


def create_scan_plan(analysis: ProjectAnalysis) -> ScanPlan:
    scans: list[PlannedScan] = []
    languages = set(analysis.languages)
    technologies = {item.lower() for item in analysis.technologies}
    files = [item.lower() for item in analysis.detected_files]

    source_languages = {
        "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust",
        "C", "C/C++", "C++", "C#", "PHP", "Ruby", "Kotlin", "Swift",
    }
    detected_languages = source_languages & languages

    scans.append(PlannedScan(
        "semgrep",
        bool(detected_languages),
        (
            "Supported source code detected."
            if detected_languages
            else "No supported source languages detected."
        ),
    ))
    scans.append(PlannedScan(
        "gitleaks",
        True,
        "Secret detection is relevant to every project.",
    ))

    code_or_manifest = bool(detected_languages) or any(
        item.endswith((
            "package.json", "package-lock.json", "pnpm-lock.yaml",
            "yarn.lock", "requirements.txt", "pyproject.toml",
            "poetry.lock", "go.mod", "cargo.toml", "pom.xml",
            "build.gradle", "dockerfile",
        ))
        for item in files
    )
    scans.append(PlannedScan(
        "trivy",
        code_or_manifest,
        (
            (
                "Project files are suitable for filesystem vulnerability "
                "and misconfiguration scanning."
            )
            if code_or_manifest
            else "No supported source code or dependency manifest detected."
        ),
    ))

    has_iac = (
        "terraform" in technologies
        or "kubernetes" in technologies
        or any(
            item.endswith((".tf", ".tf.json"))
            or "k8s/" in item
            or "kubernetes/" in item
            for item in files
        )
    )
    scans.append(PlannedScan(
        "checkov",
        has_iac,
        (
            "Terraform or Kubernetes infrastructure detected."
            if has_iac
            else "No supported infrastructure-as-code files detected."
        ),
    ))

    return ScanPlan(scans=scans)
