"""Dependency and DevOps manifest detection across common ecosystems."""

from collections.abc import Iterable
from pathlib import Path

MANIFEST_TECHNOLOGIES: dict[str, str] = {
    # JavaScript / TypeScript
    "package.json": "Node.js",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "Yarn",
    "bun.lock": "Bun",
    "bun.lockb": "Bun",
    # Python
    "requirements.txt": "Python dependencies",
    "requirements-dev.txt": "Python development dependencies",
    "pyproject.toml": "Python project",
    "Pipfile": "Pipenv",
    "Pipfile.lock": "Pipenv",
    "uv.lock": "uv",
    "poetry.lock": "Poetry",
    # Java / JVM
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle",
    "settings.gradle": "Gradle",
    "settings.gradle.kts": "Gradle",
    "gradlew": "Gradle",
    "mvnw": "Maven",
    # Go
    "go.mod": "Go modules",
    "go.sum": "Go dependencies",
    # Rust
    "Cargo.toml": "Cargo",
    "Cargo.lock": "Cargo",
    # PHP
    "composer.json": "Composer",
    "composer.lock": "Composer",
    # .NET
    "packages.lock.json": ".NET dependency lockfile",
    "nuget.config": ".NET NuGet",
    # Ruby
    "Gemfile": "Bundler",
    "Gemfile.lock": "Bundler",
    # Dart / Flutter
    "pubspec.yaml": "Dart / Flutter",
    "pubspec.lock": "Dart / Flutter",
    # Elixir
    "mix.exs": "Mix",
    "mix.lock": "Mix",
    # Swift
    "Package.swift": "Swift Package Manager",
    "Package.resolved": "Swift Package Manager",
    # Scala
    "build.sbt": "sbt",
    # Infrastructure as Code
    "terraform.lock.hcl": "Terraform",
    "Terragrunt.hcl": "Terragrunt",
    "terragrunt.hcl": "Terragrunt",
    "Pulumi.yaml": "Pulumi",
    "cdk.json": "AWS CDK",
    "serverless.yml": "Serverless Framework",
    "serverless.yaml": "Serverless Framework",
    # Containers
    "Dockerfile": "Docker",
    "Containerfile": "Containers",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "compose.yml": "Docker Compose",
    "compose.yaml": "Docker Compose",
    # Kubernetes / Helm
    "Chart.yaml": "Helm",
    "Chart.lock": "Helm",
    "kustomization.yaml": "Kustomize",
    "kustomization.yml": "Kustomize",
    # CI/CD
    "Jenkinsfile": "Jenkins",
    ".gitlab-ci.yml": "GitLab CI",
    "azure-pipelines.yml": "Azure Pipelines",
    "bitbucket-pipelines.yml": "Bitbucket Pipelines",
    "Taskfile.yml": "Task",
    "Taskfile.yaml": "Task",
    # Configuration management
    "ansible.cfg": "Ansible",
    "Vagrantfile": "Vagrant",
    # Security and quality tooling
    ".gitleaks.toml": "Gitleaks",
    ".trivy.yaml": "Trivy",
    ".trivy.yml": "Trivy",
    ".checkov.yaml": "Checkov",
    ".pre-commit-config.yaml": "pre-commit",
    ".hadolint.yaml": "Hadolint",
    ".hadolint.yml": "Hadolint",
}

PROJECT_FILE_EXTENSIONS: dict[str, str] = {
    ".csproj": ".NET",
    ".fsproj": ".NET",
    ".vbproj": ".NET",
}


def detect_dependency_manifests(
    files: Iterable[Path],
) -> tuple[set[str], list[str]]:
    """Detect dependency manifests and DevOps files from project paths."""

    technologies: set[str] = set()
    detected_files: set[str] = set()

    # These names are case-sensitive because many ecosystems use
    # canonical filenames. Extensions are normalized separately.
    for file_path in files:
        filename = file_path.name

        technology = MANIFEST_TECHNOLOGIES.get(filename)

        if technology is None:
            technology = PROJECT_FILE_EXTENSIONS.get(file_path.suffix.lower())

        if technology is not None:
            technologies.add(technology)
            detected_files.add(file_path.as_posix())

    return technologies, sorted(detected_files)
