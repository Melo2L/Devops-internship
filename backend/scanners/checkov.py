import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

UNTRUSTED_CHECKOV_CONFIGS = {".checkov.yaml", ".checkov.yml"}


def _make_config_ignore(source_root: Path):
    """Create an ignore callback isolated to one scan."""
    def ignore(directory: str, names: list[str]) -> set[str]:
        if Path(directory).resolve() == source_root:
            return UNTRUSTED_CHECKOV_CONFIGS.intersection(names)
        return set()

    return ignore


def scan_checkov(project_path: Path) -> list[dict[str, Any]]:
    executable = shutil.which("checkov")
    if not executable:
        raise RuntimeError("Checkov is not installed or is not available in PATH.")

    source_project = project_path.resolve()
    if not source_project.is_dir():
        raise RuntimeError("Checkov project directory does not exist.")

    try:
        with tempfile.TemporaryDirectory(prefix="securescan-checkov-") as temp_dir:
            isolated_root = Path(temp_dir)
            scan_project = isolated_root / "project"
            isolated_cwd = isolated_root / "cwd"
            isolated_home = isolated_root / "home"

            isolated_cwd.mkdir()
            isolated_home.mkdir()

            shutil.copytree(
                source_project,
                scan_project,
                ignore=_make_config_ignore(source_project),
            )

            env = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith(("CKV_", "CHECKOV_"))
            }
            env["HOME"] = str(isolated_home)

            try:
                result = subprocess.run(
                    [
                        executable,
                        "-d",
                        str(scan_project),
                        "-o",
                        "json",
                        "--quiet",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=900,
                    check=False,
                    cwd=isolated_cwd,
                    env=env,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(
                    "Checkov scan timed out after 900 seconds."
                ) from exc

    except OSError as exc:
        raise RuntimeError(
            f"Could not prepare isolated Checkov workspace: {exc}"
        ) from exc

    if result.returncode not in (0, 1):
        raise RuntimeError(
            "Checkov execution failed. "
            f"Exit code: {result.returncode}. "
            f"Stderr: {result.stderr[-2000:]}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Checkov did not return valid JSON. "
            f"Exit code: {result.returncode}. "
            f"Stderr: {result.stderr[-2000:]}"
        ) from exc

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise RuntimeError("Checkov returned an unexpected JSON structure.")

    return data
