import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def isolated_api(tmp_path, monkeypatch):
    """Use an isolated SQLite database for every test."""
    database_path = tmp_path / "securescan-test.db"
    monkeypatch.setenv("SECURESCAN_DATABASE_PATH", str(database_path))

    import backend.services.persistence as persistence

    persistence = importlib.reload(persistence)
    persistence.initialize_database()

    # The API modules import persistence functions directly, so reload them
    # after configuring the temporary database.
    import backend.api.projects as projects_api
    import backend.api.scans as scans_api
    import backend.main as main

    importlib.reload(scans_api)
    importlib.reload(projects_api)
    main = importlib.reload(main)

    with TestClient(main.app) as client:
        yield client, persistence

    monkeypatch.undo()


def save_sample_scan(persistence):
    result = {
        "filename": "sample.zip",
        "size_bytes": 123,
        "files_detected": 1,
        "files_extracted": 1,
        "analysis": {"languages": ["python"]},
        "scan_plan": {"enabled": ["semgrep"]},
        "scans": [
            {
                "scanner": "semgrep",
                "findings": [
                    {
                        "category": "Source Code",
                        "severity": "High",
                        "confidence": 0.95,
                        "title": "Potential command injection",
                        "description": "Unsafe command execution.",
                        "file": "app.py",
                        "line": 10,
                        "status": "open",
                        "rule_id": "test-command-injection",
                        "fingerprint": "sample-fingerprint",
                    }
                ],
            }
        ],
    }
    saved = persistence.save_scan(result)
    finding_id = f"{saved['id']}:sample-fingerprint"
    return saved, finding_id


def test_scan_and_findings_can_be_retrieved(isolated_api):
    client, persistence = isolated_api
    saved, finding_id = save_sample_scan(persistence)

    scans_response = client.get("/api/scans")
    detail_response = client.get(f"/api/scans/{saved['id']}")
    findings_response = client.get(f"/api/scans/{saved['id']}/findings")
    filtered_response = client.get(
        "/api/findings",
        params={"scan_id": saved["id"]},
    )

    assert scans_response.status_code == 200
    assert any(scan["id"] == saved["id"] for scan in scans_response.json())

    assert detail_response.status_code == 200
    assert detail_response.json()["findings_count"] == 1

    assert findings_response.status_code == 200
    assert findings_response.json()[0]["id"] == finding_id

    assert filtered_response.status_code == 200
    assert filtered_response.json()[0]["id"] == finding_id


@pytest.mark.parametrize("status", ["open", "resolved", "ignored"])
def test_finding_status_accepts_allowed_values(isolated_api, status):
    client, persistence = isolated_api
    saved, finding_id = save_sample_scan(persistence)

    response = client.patch(
        f"/api/findings/{finding_id}/status",
        json={"status": status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == status

    stored = persistence.list_findings(saved["id"])
    assert stored[0]["status"] == status


def test_finding_status_rejects_invalid_value(isolated_api):
    client, _ = isolated_api
    _, finding_id = save_sample_scan(isolated_api[1])

    response = client.patch(
        f"/api/findings/{finding_id}/status",
        json={"status": "invalid-status"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Invalid status. Allowed values: open, resolved, ignored."
    )


def test_finding_status_returns_404_for_unknown_finding(isolated_api):
    client, _ = isolated_api

    response = client.patch(
        "/api/findings/unknown-scan:unknown-finding/status",
        json={"status": "resolved"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Finding not found."


def test_scan_endpoints_return_404_for_unknown_scan(isolated_api):
    client, _ = isolated_api
    unknown_scan_id = "scan-does-not-exist"

    detail_response = client.get(f"/api/scans/{unknown_scan_id}")
    scan_findings_response = client.get(
        f"/api/scans/{unknown_scan_id}/findings"
    )
    filtered_findings_response = client.get(
        "/api/findings",
        params={"scan_id": unknown_scan_id},
    )

    assert detail_response.status_code == 404
    assert scan_findings_response.status_code == 404
    assert filtered_findings_response.status_code == 404
