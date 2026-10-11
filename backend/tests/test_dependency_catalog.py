from pathlib import Path

import pytest

from backend.services.catalogs.dependencies import (
    detect_dependency_manifests,
)


@pytest.mark.parametrize(
    ("filenames", "expected_technologies"),
    [
        (
            ["package.json", "pnpm-lock.yaml"],
            {"Node.js", "pnpm"},
        ),
        (
            ["pyproject.toml", "uv.lock", "requirements.txt"],
            {"Python project", "uv", "Python dependencies"},
        ),
        (
            ["pom.xml", "build.gradle.kts"],
            {"Maven", "Gradle"},
        ),
        (
            ["go.mod", "go.sum", "Cargo.toml"],
            {"Go modules", "Go dependencies", "Cargo"},
        ),
        (
            ["composer.json", "Gemfile.lock", "pubspec.yaml"],
            {"Composer", "Bundler", "Dart / Flutter"},
        ),
        (
            ["project.csproj", "project.fsproj"],
            {".NET"},
        ),
        (
            ["Dockerfile", "compose.yaml", "Containerfile"],
            {"Docker", "Docker Compose", "Containers"},
        ),
        (
            ["Chart.yaml", "Chart.lock", "kustomization.yaml"],
            {"Helm", "Kustomize"},
        ),
        (
            [
                ".gitlab-ci.yml",
                "azure-pipelines.yml",
                "bitbucket-pipelines.yml",
            ],
            {"GitLab CI", "Azure Pipelines", "Bitbucket Pipelines"},
        ),
        (
            [
                ".gitleaks.toml",
                ".trivy.yaml",
                ".pre-commit-config.yaml",
            ],
            {"Gitleaks", "Trivy", "pre-commit"},
        ),
        (
            ["terraform.lock.hcl", "terragrunt.hcl", "Pulumi.yaml"],
            {"Terraform", "Terragrunt", "Pulumi"},
        ),
        (
            ["gradlew", "mvnw"],
            {"Gradle", "Maven"},
        ),
    ],
)
def test_detects_dependency_manifests(
    filenames: list[str],
    expected_technologies: set[str],
) -> None:
    files = [Path("project") / filename for filename in filenames]

    technologies, detected_files = detect_dependency_manifests(files)

    assert technologies == expected_technologies
    assert set(detected_files) == {file.as_posix() for file in files}


def test_detects_manifests_in_nested_directories() -> None:
    files = [
        Path("frontend/package.json"),
        Path("backend/pyproject.toml"),
        Path("infrastructure/terraform.lock.hcl"),
    ]

    technologies, detected_files = detect_dependency_manifests(files)

    assert technologies == {
        "Node.js",
        "Python project",
        "Terraform",
    }
    assert detected_files == [
        "backend/pyproject.toml",
        "frontend/package.json",
        "infrastructure/terraform.lock.hcl",
    ]


def test_detects_dotnet_project_extensions_case_insensitively() -> None:
    files = [
        Path("src/App.CSPROJ"),
        Path("src/Library.fsproj"),
        Path("src/Legacy.VBPROJ"),
    ]

    technologies, detected_files = detect_dependency_manifests(files)

    assert technologies == {".NET"}
    assert detected_files == [
        "src/App.CSPROJ",
        "src/Legacy.VBPROJ",
        "src/Library.fsproj",
    ]


def test_manifest_filename_matching_is_case_sensitive() -> None:
    files = [
        Path("Dockerfile"),
        Path("dockerfile"),
        Path("package.json"),
        Path("PACKAGE.JSON"),
    ]

    technologies, detected_files = detect_dependency_manifests(files)

    assert technologies == {"Docker", "Node.js"}
    assert detected_files == ["Dockerfile", "package.json"]


def test_ignores_unknown_files() -> None:
    files = [
        Path("README.md"),
        Path("config.yaml"),
        Path("random.txt"),
    ]

    technologies, detected_files = detect_dependency_manifests(files)

    assert technologies == set()
    assert detected_files == []


def test_empty_input_returns_empty_results() -> None:
    technologies, detected_files = detect_dependency_manifests([])

    assert technologies == set()
    assert detected_files == []
