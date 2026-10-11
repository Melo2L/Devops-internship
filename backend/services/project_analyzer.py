import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from backend.services.catalogs.dependencies import (
    detect_dependency_manifests,
)
from backend.services.catalogs.javascript import (
    detect_javascript_technologies,
)

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".turbo",
}

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".sh": "Shell",
    ".bash": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".vue": "Vue",
    ".svelte": "Svelte",
}


@dataclass
class ProjectAnalysis:
    total_files: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    technologies: list[str] = field(default_factory=list)
    detected_files: list[str] = field(default_factory=list)


def _iter_project_files(root: Path):
    """Yield project files while skipping generated/vendor directories."""

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative_parts = path.relative_to(root).parts

        if any(part in IGNORED_DIRECTORIES for part in relative_parts):
            continue

        yield path


def _detect_languages(files: list[Path]) -> dict[str, int]:
    """Count source files by programming language."""

    counter: Counter[str] = Counter()

    for path in files:
        language = LANGUAGE_EXTENSIONS.get(path.suffix.lower())

        if language:
            counter[language] += 1

    return dict(
        sorted(
            counter.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )


def _has_file(files: list[Path], filename: str) -> bool:
    """Check whether a specific filename exists."""

    return any(path.name.lower() == filename.lower() for path in files)


def _has_directory(root: Path, directory: str) -> bool:
    """Check whether a directory exists at the project root."""

    return (root / directory).is_dir()


def _find_project_file(
    root: Path,
    filename: str,
) -> Path | None:
    """Find a project file anywhere inside the workspace."""

    for path in root.rglob(filename):
        if path.is_file():
            relative_parts = path.relative_to(root).parts

            if any(part in IGNORED_DIRECTORIES for part in relative_parts):
                continue

            return path

    return None


def _read_package_json(root: Path) -> dict:
    """Read a valid package.json object without executing anything."""

    package_path = _find_project_file(
        root,
        "package.json",
    )

    if package_path is None:
        return {}

    try:
        data = json.loads(
            package_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def _detect_technologies(
    root: Path,
    files: list[Path],
) -> tuple[list[str], list[str]]:
    """Detect frameworks, tooling and important project files."""

    technologies: set[str] = set()
    detected_files: set[str] = set()

    # Dependency manifests across supported ecosystems.
    manifest_technologies, manifest_files = detect_dependency_manifests(
        [path.relative_to(root) for path in files]
    )
    technologies.update(manifest_technologies)
    detected_files.update(manifest_files)

    filenames = {path.name.lower() for path in files}

    # JavaScript / TypeScript ecosystem.
    package_json = _read_package_json(root)

    if package_json:
        technologies.update(detect_javascript_technologies(package_json))

    # Containerization.
    if "dockerfile" in filenames:
        detected_files.add("Dockerfile")
        technologies.add("Docker")

    if "docker-compose.yml" in filenames or "docker-compose.yaml" in filenames:
        detected_files.update(
            filename
            for filename in ("docker-compose.yml", "docker-compose.yaml")
            if filename in filenames
        )
        technologies.add("Docker Compose")

    # Infrastructure as Code.
    terraform_files = [path for path in files if path.suffix.lower() == ".tf"]

    if terraform_files:
        technologies.add("Terraform")

    if "terraform.lock.hcl" in filenames:
        detected_files.add("terraform.lock.hcl")

    # CI/CD.
    github_workflows = root / ".github" / "workflows"

    if github_workflows.is_dir():
        workflow_files = list(github_workflows.glob("*"))

        if workflow_files:
            detected_files.add(".github/workflows")
            technologies.add("GitHub Actions")

    # Common configuration/security files.
    for filename, technology in (
        (".env", "Environment configuration"),
        (".env.example", "Environment configuration"),
        ("Makefile", "Make"),
        ("Jenkinsfile", "Jenkins"),
        ("ansible.cfg", "Ansible"),
        ("playbook.yml", "Ansible"),
        ("playbook.yaml", "Ansible"),
    ):
        if filename.lower() in filenames:
            detected_files.add(filename)
            technologies.add(technology)

    # Kubernetes manifests.
    kubernetes_files = [
        path
        for path in files
        if path.suffix.lower() in {".yaml", ".yml"}
        and any(
            marker in path.name.lower()
            for marker in ("deployment", "service", "ingress")
        )
    ]

    if kubernetes_files:
        technologies.add("Kubernetes")

    return sorted(technologies), sorted(detected_files)


def analyze_project(root: Path) -> ProjectAnalysis:
    """
    Analyze a project directory without executing project code.

    The analyzer only reads file paths and selected text configuration
    files such as package.json.
    """

    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")

    files = list(_iter_project_files(root))

    languages = _detect_languages(files)

    technologies, detected_files = _detect_technologies(
        root,
        files,
    )

    return ProjectAnalysis(
        total_files=len(files),
        languages=languages,
        technologies=technologies,
        detected_files=detected_files,
    )
