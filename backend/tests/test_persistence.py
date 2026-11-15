import importlib

import pytest


@pytest.fixture
def persistence(tmp_path, monkeypatch):
    """Load persistence with an isolated SQLite database."""
    database_path = tmp_path / "securescan-test.db"

    monkeypatch.setenv(
        "SECURESCAN_DATABASE_PATH",
        str(database_path),
    )

    import backend.services.persistence as persistence_module

    persistence_module = importlib.reload(persistence_module)

    yield persistence_module



def test_initialize_database_creates_tables_and_indexes(persistence):
    persistence.initialize_database()

    with persistence._connect() as db:
        tables = {
            row["name"]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        indexes = {
            row["name"]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }

    assert {"scans", "findings"} <= tables
    assert "idx_scans_created_at" in indexes
    assert "idx_findings_scan_id" in indexes
    assert "idx_findings_severity" in indexes


def test_initialize_database_is_idempotent(persistence):
    persistence.initialize_database()
    persistence.initialize_database()

    with persistence._connect() as db:
        tables = db.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type = 'table' AND name IN ('scans', 'findings')"
        ).fetchone()[0]

    assert tables == 2


def test_initialize_database_migrates_legacy_confidence_column(
    persistence,
    tmp_path,
):
    import sqlite3

    database_path = tmp_path / "legacy.db"
    persistence.DATABASE_PATH = database_path

    with sqlite3.connect(database_path) as db:
        db.executescript(
            """
            CREATE TABLE scans (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                files_detected INTEGER NOT NULL,
                files_extracted INTEGER NOT NULL,
                result_json TEXT NOT NULL
            );

            CREATE TABLE findings (
                id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL,
                scanner TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                file TEXT NOT NULL,
                line INTEGER,
                status TEXT NOT NULL,
                remediation TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                fingerprint TEXT NOT NULL
            );

            INSERT INTO scans VALUES (
                'legacy-scan',
                'legacy.zip',
                '2026-01-01T00:00:00+00:00',
                'completed',
                100,
                1,
                1,
                '{}'
            );

            INSERT INTO findings VALUES (
                'legacy-finding',
                'legacy-scan',
                'semgrep',
                'Source Code',
                'High',
                0.95,
                'Potential command injection',
                'Legacy finding',
                'app.py',
                10,
                'open',
                'Review the subprocess call',
                'test-rule',
                'legacy-fingerprint'
            );
            """
        )

    persistence.initialize_database()

    with persistence._connect() as db:
        confidence_column = next(
            row
            for row in db.execute(
                "PRAGMA table_info(findings)"
            ).fetchall()
            if row["name"] == "confidence"
        )

        migrated_finding = db.execute(
            "SELECT * FROM findings WHERE id = ?",
            ("legacy-finding",),
        ).fetchone()

    assert confidence_column["notnull"] == 0
    assert migrated_finding is not None
    assert migrated_finding["confidence"] == 0.95
    assert migrated_finding["title"] == "Potential command injection"

def test_save_scan_and_retrieve_scan(persistence):
    persistence.initialize_database()

    result = {
        "filename": "sample.zip",
        "size_bytes": 123,
        "files_detected": 2,
        "files_extracted": 2,
        "status": "completed",
        "analysis": {"languages": ["python"]},
        "scan_plan": {"enabled": ["semgrep"]},
        "scans": [
            {
                "scanner": "semgrep",
                "status": "completed",
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
                        "remediation": "Review subprocess usage.",
                        "rule_id": "test-command-injection",
                        "fingerprint": "sample-fingerprint",
                    }
                ],
            }
        ],
    }

    saved = persistence.save_scan(result)

    retrieved = persistence.get_scan(saved["id"])

    assert retrieved is not None
    assert retrieved["id"] == saved["id"]
    assert retrieved["filename"] == "sample.zip"
    assert retrieved["status"] == "completed"
    assert retrieved["findings_count"] == 1

    findings = persistence.list_findings(saved["id"])

    assert len(findings) == 1
    assert findings[0]["title"] == "Potential command injection"
    assert findings[0]["confidence"] == 0.95


def _make_scan_result(filename="sample.zip", fingerprint="sample-fingerprint"):
    return {
        "filename": filename,
        "size_bytes": 123,
        "files_detected": 2,
        "files_extracted": 2,
        "status": "completed",
        "analysis": {"languages": ["python"]},
        "scan_plan": {"enabled": ["semgrep"]},
        "scans": [
            {
                "scanner": "semgrep",
                "status": "completed",
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
                        "remediation": "Review subprocess usage.",
                        "rule_id": "test-command-injection",
                        "fingerprint": fingerprint,
                    }
                ],
            }
        ],
    }


def test_list_scans_returns_saved_scans(persistence):
    persistence.initialize_database()

    first = persistence.save_scan(
        _make_scan_result("first.zip", "fingerprint-1")
    )
    second = persistence.save_scan(
        _make_scan_result("second.zip", "fingerprint-2")
    )

    scans = persistence.list_scans()
    scan_ids = {scan["id"] for scan in scans}

    assert len(scans) == 2
    assert first["id"] in scan_ids
    assert second["id"] in scan_ids


def test_list_findings_without_scan_id_returns_all_findings(persistence):
    persistence.initialize_database()

    first = persistence.save_scan(
        _make_scan_result("first.zip", "fingerprint-1")
    )
    second = persistence.save_scan(
        _make_scan_result("second.zip", "fingerprint-2")
    )

    findings = persistence.list_findings()

    assert len(findings) == 2
    assert {finding["scan_id"] for finding in findings} == {
        first["id"],
        second["id"],
    }


def test_list_findings_filters_by_scan_id(persistence):
    persistence.initialize_database()

    first = persistence.save_scan(
        _make_scan_result("first.zip", "fingerprint-1")
    )
    persistence.save_scan(
        _make_scan_result("second.zip", "fingerprint-2")
    )

    findings = persistence.list_findings(first["id"])

    assert len(findings) == 1
    assert findings[0]["scan_id"] == first["id"]


def test_list_findings_returns_empty_list_for_unknown_scan(persistence):
    persistence.initialize_database()

    assert persistence.list_findings("unknown-scan") == []


def test_get_scan_returns_none_for_unknown_scan(persistence):
    persistence.initialize_database()

    assert persistence.get_scan("unknown-scan") is None


def test_save_scan_rejects_invalid_status(persistence):
    persistence.initialize_database()

    result = _make_scan_result()
    result["status"] = "invalid"

    with pytest.raises(ValueError):
        persistence.save_scan(result)


@pytest.mark.parametrize(
    "status",
    ["open", "resolved", "ignored"],
)
def test_update_finding_status_accepts_allowed_values(
    persistence,
    status,
):
    persistence.initialize_database()

    saved = persistence.save_scan(_make_scan_result())
    finding_id = f"{saved['id']}:sample-fingerprint"

    updated = persistence.update_finding_status(
        finding_id,
        status,
    )

    assert updated is not None
    assert updated["status"] == status


def test_update_finding_status_normalizes_case_and_whitespace(
    persistence,
):
    persistence.initialize_database()

    saved = persistence.save_scan(_make_scan_result())
    finding_id = f"{saved['id']}:sample-fingerprint"

    updated = persistence.update_finding_status(
        finding_id,
        " RESOLVED ",
    )

    assert updated["status"] == "resolved"


def test_update_finding_status_rejects_invalid_status(persistence):
    persistence.initialize_database()

    saved = persistence.save_scan(_make_scan_result())
    finding_id = f"{saved['id']}:sample-fingerprint"

    with pytest.raises(ValueError, match="Invalid status"):
        persistence.update_finding_status(
            finding_id,
            "invalid",
        )


def test_update_finding_status_returns_none_for_unknown_finding(
    persistence,
):
    persistence.initialize_database()

    result = persistence.update_finding_status(
        "unknown-scan:unknown-finding",
        "resolved",
    )

    assert result is None


def test_failed_legacy_migration_rolls_back_without_losing_data(
    persistence,
    tmp_path,
):
    import sqlite3

    database_path = tmp_path / "broken-legacy.db"
    persistence.DATABASE_PATH = database_path

    with sqlite3.connect(database_path) as db:
        db.executescript(
            """
            CREATE TABLE scans (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                files_detected INTEGER NOT NULL,
                files_extracted INTEGER NOT NULL,
                result_json TEXT NOT NULL
            );

            CREATE TABLE findings (
                id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL,
                scanner TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                file TEXT NOT NULL,
                line INTEGER,
                status TEXT NOT NULL,
                remediation TEXT NOT NULL,
                rule_id TEXT NOT NULL
            );

            INSERT INTO scans VALUES (
                'legacy-scan',
                'legacy.zip',
                '2026-01-01T00:00:00+00:00',
                'completed',
                100,
                1,
                1,
                '{}'
            );

            INSERT INTO findings VALUES (
                'legacy-finding',
                'legacy-scan',
                'semgrep',
                'Source Code',
                'High',
                0.95,
                'Legacy finding',
                'Legacy description',
                'app.py',
                10,
                'open',
                'Review the code',
                'legacy-rule'
            );
            """
        )

    with pytest.raises(sqlite3.OperationalError):
        persistence.initialize_database()

    with persistence._connect() as db:
        confidence_column = next(
            row
            for row in db.execute(
                "PRAGMA table_info(findings)"
            ).fetchall()
            if row["name"] == "confidence"
        )

        finding = db.execute(
            "SELECT * FROM findings WHERE id = ?",
            ("legacy-finding",),
        ).fetchone()

        foreign_keys_enabled = db.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

    assert confidence_column["notnull"] == 1
    assert finding is not None
    assert finding["title"] == "Legacy finding"
    assert foreign_keys_enabled == 1
