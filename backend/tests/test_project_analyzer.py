import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from backend.services.project_analyzer import (
    ProjectAnalysis,
    _detect_languages,
    _find_project_file,
    _has_directory,
    _has_file,
    _read_package_json,
    analyze_project,
)


def test_project_analyzer_detects_javascript_stack() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        (root / "src").mkdir()

        (root / "src" / "main.tsx").write_text(
            "export default function App() {}",
            encoding="utf-8",
        )

        package_json = {
            "dependencies": {
                "react": "19.0.0",
                "@tanstack/react-start": "1.0.0",
            },
            "devDependencies": {
                "vite": "8.0.0",
                "typescript": "5.0.0",
                "tailwindcss": "4.0.0",
            },
        }

        (root / "package.json").write_text(
            json.dumps(package_json),
            encoding="utf-8",
        )

        (root / "Dockerfile").write_text(
            "FROM node:24",
            encoding="utf-8",
        )

        analysis = analyze_project(root)

        assert analysis.total_files == 3

        assert analysis.languages["TypeScript"] == 1

        assert "React" in analysis.technologies
        assert "Vite" in analysis.technologies
        assert "TypeScript" in analysis.technologies
        assert "Tailwind CSS" in analysis.technologies
        assert "TanStack Start" in analysis.technologies
        assert "Docker" in analysis.technologies

        assert "package.json" in analysis.detected_files
        assert "Dockerfile" in analysis.detected_files


def test_generated_directories_are_ignored() -> None:
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        (root / "src").mkdir()
        (root / "node_modules" / "react").mkdir(parents=True)
        (root / ".git").mkdir()

        (root / "src" / "main.ts").write_text(
            "console.log('hello')",
            encoding="utf-8",
        )

        (root / "node_modules" / "react" / "index.js").write_text(
            "generated dependency",
            encoding="utf-8",
        )

        (root / ".git" / "config").write_text(
            "git data",
            encoding="utf-8",
        )

        analysis = analyze_project(root)

        assert analysis.total_files == 1
        assert analysis.languages == {"TypeScript": 1}


def test_analyzer_rejects_missing_project_directory(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="Project directory does not exist",
    ):
        analyze_project(tmp_path / "missing")


def test_empty_project_returns_empty_analysis(
    tmp_path: Path,
) -> None:
    analysis = analyze_project(tmp_path)

    assert analysis == ProjectAnalysis()


def test_detect_languages_is_case_insensitive(
    tmp_path: Path,
) -> None:
    files = [
        tmp_path / "main.PY",
        tmp_path / "app.py",
        tmp_path / "index.TSX",
        tmp_path / "README.md",
    ]

    languages = _detect_languages(files)

    assert languages == {
        "Python": 2,
        "TypeScript": 1,
    }


def test_detect_languages_orders_by_frequency(
    tmp_path: Path,
) -> None:
    files = [
        tmp_path / "a.py",
        tmp_path / "b.py",
        tmp_path / "c.js",
        tmp_path / "d.ts",
    ]

    languages = _detect_languages(files)

    assert list(languages.items()) == [
        ("Python", 2),
        ("JavaScript", 1),
        ("TypeScript", 1),
    ]


def test_has_file_is_case_insensitive(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "Dockerfile"
    file_path.touch()

    assert _has_file([file_path], "dockerfile")
    assert not _has_file([file_path], "Makefile")


def test_has_directory_checks_project_root(
    tmp_path: Path,
) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "config").mkdir()

    assert _has_directory(tmp_path, "src")
    assert not _has_directory(tmp_path, "config")


def test_find_project_file_skips_ignored_directories(
    tmp_path: Path,
) -> None:
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "package.json").write_text(
        "{}",
        encoding="utf-8",
    )

    assert _find_project_file(tmp_path, "package.json") is None


def test_read_package_json_when_missing(
    tmp_path: Path,
) -> None:
    assert _read_package_json(tmp_path) == {}


@pytest.mark.parametrize(
    "content",
    [
        "{invalid json",
        "",
    ],
)
def test_read_package_json_handles_invalid_content(
    tmp_path: Path,
    content: str,
) -> None:
    (tmp_path / "package.json").write_text(
        content,
        encoding="utf-8",
    )

    assert _read_package_json(tmp_path) == {}


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        "null",
        '"texto"',
        "123",
        "true",
    ],
)
def test_read_package_json_rejects_non_object_json(
    tmp_path: Path,
    content: str,
) -> None:
    (tmp_path / "package.json").write_text(
        content,
        encoding="utf-8",
    )

    assert _read_package_json(tmp_path) == {}


def test_read_package_json_handles_read_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package_file = tmp_path / "package.json"
    package_file.write_text(
        '{"dependencies": {"react": "19.0.0"}}',
        encoding="utf-8",
    )

    def raise_os_error(*args: object, **kwargs: object) -> str:
        raise OSError("simulated read failure")

    monkeypatch.setattr(
        Path,
        "read_text",
        raise_os_error,
    )

    assert _read_package_json(tmp_path) == {}


def test_analyzer_detects_devops_technologies(
    tmp_path: Path,
) -> None:
    files = {
        "requirements.txt": "fastapi==0.115.12\n",
        "pyproject.toml": "[project]\nname = 'example'\n",
        "poetry.lock": "",
        "docker-compose.yml": "services: {}\n",
        "main.tf": 'resource "example" "test" {}\n',
        "terraform.lock.hcl": "",
        ".env": "APP_ENV=test\n",
        ".env.example": "APP_ENV=\n",
        "Makefile": "test:\n\tpytest\n",
        "Jenkinsfile": "pipeline {}\n",
        "ansible.cfg": "[defaults]\n",
        "playbook.yml": "---\n",
        "playbook.yaml": "---\n",
        ".github/workflows/ci.yml": "name: CI\n",
        "k8s/deployment.yaml": "kind: Deployment\n",
    }

    for filename, content in files.items():
        file_path = tmp_path / filename
        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        file_path.write_text(
            content,
            encoding="utf-8",
        )

    analysis = analyze_project(tmp_path)

    expected_technologies = {
        "Python dependencies",
        "Python project",
        "Poetry",
        "Docker Compose",
        "Terraform",
        "GitHub Actions",
        "Environment configuration",
        "Make",
        "Jenkins",
        "Ansible",
        "Kubernetes",
    }

    assert expected_technologies.issubset(set(analysis.technologies))

    expected_detected_files = {
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "terraform.lock.hcl",
        ".env",
        ".env.example",
        "Makefile",
        "Jenkinsfile",
        "ansible.cfg",
        "playbook.yml",
        "playbook.yaml",
        ".github/workflows",
    }

    assert expected_detected_files.issubset(set(analysis.detected_files))


def test_detects_nextjs_from_package_json(
    tmp_path: Path,
) -> None:
    package_json = {
        "dependencies": {
            "next": "^15.0.0",
        },
    }

    (tmp_path / "package.json").write_text(
        json.dumps(package_json),
        encoding="utf-8",
    )

    analysis = analyze_project(tmp_path)

    assert "Next.js" in analysis.technologies


def test_detects_tanstack_router_from_package_json(
    tmp_path: Path,
) -> None:
    package_json = {
        "dependencies": {
            "@tanstack/react-router": "^1.0.0",
        },
    }

    (tmp_path / "package.json").write_text(
        json.dumps(package_json),
        encoding="utf-8",
    )

    analysis = analyze_project(tmp_path)

    assert "TanStack Router" in analysis.technologies
