from backend.services.catalogs.javascript import (
    detect_javascript_technologies,
)


def test_detects_common_javascript_ecosystem() -> None:
    package_json = {
        "dependencies": {
            "react": "^19.0.0",
            "next": "^15.0.0",
            "@angular/core": "^20.0.0",
            "express": "^5.0.0",
            "prisma": "^6.0.0",
        },
        "devDependencies": {
            "typescript": "^5.0.0",
            "vitest": "^3.0.0",
            "eslint": "^9.0.0",
        },
    }

    technologies = detect_javascript_technologies(package_json)

    assert technologies == {
        "React",
        "Next.js",
        "Angular",
        "Express",
        "Prisma",
        "TypeScript",
        "Vitest",
        "ESLint",
    }


def test_detects_peer_dependencies() -> None:
    package_json = {
        "peerDependencies": {
            "react": "^19.0.0",
        },
    }

    assert detect_javascript_technologies(package_json) == {"React"}


def test_ignores_malformed_dependency_sections() -> None:
    package_json = {
        "dependencies": None,
        "devDependencies": ["react", "vite"],
        "peerDependencies": {
            "typescript": "^5.0.0",
        },
    }

    assert detect_javascript_technologies(package_json) == {
        "TypeScript",
    }


def test_unknown_packages_are_not_reported() -> None:
    package_json = {
        "dependencies": {
            "unknown-package-example": "1.0.0",
        },
    }

    assert detect_javascript_technologies(package_json) == set()


def test_empty_manifest_returns_no_technologies() -> None:
    assert detect_javascript_technologies({}) == set()
