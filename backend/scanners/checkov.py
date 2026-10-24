import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def scan_checkov(project_path: Path) -> list[dict[str, Any]]:
    executable = shutil.which("checkov")
    if not executable:
        raise RuntimeError(
            "Checkov is not installed or is not available in PATH."
        )

    result = subprocess.run(
        [
            executable,
            "-d", str(project_path.resolve()),
            "-o", "json",
            "--quiet",
        ],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )

    # Checkov can return a non-zero status when checks fail.
    # The JSON report must be inspected before deciding whether execution failed.
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

    if not isinstance(data, list) or not all(
        isinstance(item, dict) for item in data
    ):
        raise RuntimeError("Checkov returned an unexpected JSON structure.")

    return data
