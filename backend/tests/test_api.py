import io
import zipfile
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def create_zip(files: dict[str, str]) -> bytes:
    """Create an in-memory ZIP archive for API tests."""
    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)

    return buffer.getvalue()


def test_health_endpoint_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "securescan-api",
        "version": "0.1.0",
    }


def test_upload_rejects_non_zip_file():
    response = client.post(
        "/api/projects/upload",
        files={
            "file": (
                "project.txt",
                b"not a ZIP archive",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only ZIP archives are supported."


def test_upload_rejects_invalid_zip():
    response = client.post(
        "/api/projects/upload",
        files={
            "file": (
                "project.zip",
                b"not a valid ZIP archive",
                "application/zip",
            )
        },
    )

    assert response.status_code == 400


def test_upload_accepts_valid_zip():
    archive = create_zip(
        {
            "README.md": "# SecureScan test project",
        }
    )

    response = client.post(
        "/api/projects/upload",
        files={
            "file": (
                "project.zip",
                archive,
                "application/zip",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "completed"
    assert result["filename"] == "project.zip"
    assert result["files_detected"] >= 1
    assert result["files_extracted"] >= 1
    assert "analysis" in result
    assert "scan_plan" in result
    assert "scans" in result
    assert result["message"] == ("Project analysis completed successfully.")

    # The scan must be persisted before the API returns.
    assert result["id"]
    assert result["created_at"]

    # Every executed scanner must expose its execution status.
    for scan in result["scans"]:
        assert scan["status"] in {"completed", "partial", "failed"}
        assert "error" in scan
        assert "findings" in scan


def test_upload_returns_500_when_analysis_fails():
    archive = create_zip(
        {
            "README.md": "# SecureScan test project",
        }
    )

    with patch(
        "backend.api.projects.analyze_project",
        side_effect=RuntimeError("Simulated analysis failure"),
    ):
        response = client.post(
            "/api/projects/upload",
            files={
                "file": (
                    "project.zip",
                    archive,
                    "application/zip",
                )
            },
        )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Project analysis failed: Simulated analysis failure"
    )


def test_upload_rejects_archive_over_size_limit():
    from unittest.mock import AsyncMock, patch

    from backend.api import projects

    archive = create_zip({"README.md": "# Test"})

    async def read_upload(*args, **kwargs):
        if not hasattr(read_upload, "called"):
            read_upload.called = True
            return b"x" * (projects.MAX_ARCHIVE_SIZE + 1)
        return b""

    with (
        patch.object(
            projects,
            "MAX_ARCHIVE_SIZE",
            100,
        ),
        patch.object(
            projects.UploadFile,
            "read",
            new_callable=AsyncMock,
            side_effect=read_upload,
        ),
    ):
        response = client.post(
            "/api/projects/upload",
            files={
                "file": (
                    "project.zip",
                    archive,
                    "application/zip",
                )
            },
        )

    assert response.status_code == 413
    assert response.json()["detail"] == (
        "Archive exceeds the maximum allowed size of 100 MB."
    )


def test_metrics_endpoint_exposes_http_request_metrics():
    health_response = client.get("/health")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert "text/plain" in metrics_response.headers["content-type"]

    content = metrics_response.text
    assert "securescan_http_requests_total" in content
    assert "securescan_http_request_duration_seconds" in content
    assert 'endpoint="/health"' in content


def test_upload_records_findings_metrics(tmp_path):
    from backend.models.findings import (
        Finding,
        FindingCategory,
        FindingSeverity,
    )
    from backend.services.scan_executor import ScanExecutionResult

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("README.md", "# Test project")

    finding = Finding(
        scanner="semgrep",
        category=FindingCategory.SOURCE_CODE,
        severity=FindingSeverity.HIGH,
        confidence=0.95,
        title="Test finding",
        description="Finding used to test metrics.",
        file="app.py",
        line=1,
    )

    scan_result = ScanExecutionResult(
        scanner="semgrep",
        findings=[finding],
        status="completed",
    )

    def metric_value(metrics, metric_name, label, value):
        prefix = f'{metric_name}{{{label}="{value}"}} '
        for line in metrics.splitlines():
            if line.startswith(prefix):
                return float(line[len(prefix):])
        return 0.0

    before_metrics = client.get("/metrics")
    assert before_metrics.status_code == 200

    before_findings = metric_value(
        before_metrics.text,
        "securescan_findings_total",
        "severity",
        "high",
    )
    before_scans = metric_value(
        before_metrics.text,
        "securescan_scans_total",
        "status",
        "completed",
    )

    with patch(
        "backend.api.projects.execute_scan_plan",
        return_value=[scan_result],
    ):
        response = client.post(
            "/api/projects/upload",
            files={
                "file": (
                    "metrics-test.zip",
                    archive.getvalue(),
                    "application/zip",
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["scans"][0]["findings"][0]["title"] == "Test finding"

    after_metrics = client.get("/metrics")
    assert after_metrics.status_code == 200

    after_findings = metric_value(
        after_metrics.text,
        "securescan_findings_total",
        "severity",
        "high",
    )
    after_scans = metric_value(
        after_metrics.text,
        "securescan_scans_total",
        "status",
        "completed",
    )

    assert after_findings == before_findings + 1
    assert after_scans == before_scans + 1


def test_upload_returns_500_when_scan_cannot_be_persisted():
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("README.md", "# Test project")

    with patch(
        "backend.api.projects.save_scan",
        side_effect=RuntimeError("Database unavailable"),
    ):
        response = client.post(
            "/api/projects/upload",
            files={
                "file": (
                    "persistence-error.zip",
                    archive.getvalue(),
                    "application/zip",
                )
            },
        )

    assert response.status_code == 500
    assert "could not be persisted" in response.json()["detail"]
