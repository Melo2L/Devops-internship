import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def scan_trivy(project_path: Path) -> dict[str, Any]:
    executable = shutil.which("trivy")
    if not executable:
        raise RuntimeError(
            "Trivy is not installed or is not available in PATH."
        )

    result = subprocess.run(
        [
            executable,
            "fs",
            "--format", "json",
            "--scanners", "vuln,misconfig",
            "--quiet",
            str(project_path.resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Trivy failed with exit code {result.returncode}: "
            f"{result.stderr[-2000:]}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Trivy returned invalid JSON.") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Trivy returned an unexpected JSON structure.")

    return data
