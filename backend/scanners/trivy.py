import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def scan_trivy(project_path: Path) -> dict[str, Any]:
    project_path = Path(project_path)

    if not project_path.exists() or not project_path.is_dir():
        raise ValueError("Project directory does not exist or is not a directory.")

    executable = shutil.which("trivy")
    if not executable:
        raise RuntimeError("Trivy is not installed or is not available in PATH.")

    try:
        result = subprocess.run(
            [
                executable,
                "fs",
                "--format",
                "json",
                "--scanners",
                "vuln,misconfig",
                "--quiet",
                str(project_path.resolve()),
            ],
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Trivy scan exceeded the 900-second timeout.") from exc

    if result.returncode != 0:
        raise RuntimeError(
            f"Trivy failed with exit code {result.returncode}: {result.stderr[-2000:]}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Trivy returned invalid JSON.") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Trivy returned an unexpected JSON structure.")

    results = data.get("Results", [])

    if results is None:
        results = []

    if not isinstance(results, list):
        raise RuntimeError("Trivy report contains an invalid 'Results' list.")

    for index, result_data in enumerate(results):
        if not isinstance(result_data, dict):
            raise RuntimeError(
                f"Trivy report contains an invalid 'Results[{index}]' object."
            )

    return data
