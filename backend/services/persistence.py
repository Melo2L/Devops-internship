import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATABASE_PATH = Path(
    os.getenv("SECURESCAN_DATABASE_PATH", "/data/securescan.db")
)


def _connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with _connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                files_detected INTEGER NOT NULL,
                files_extracted INTEGER NOT NULL,
                result_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL REFERENCES scans(id)
                    ON DELETE CASCADE,
                scanner TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                file TEXT NOT NULL,
                line INTEGER,
                status TEXT NOT NULL,
                remediation TEXT,
                rule_id TEXT,
                fingerprint TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_scans_created_at
                ON scans(created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_findings_scan_id
                ON findings(scan_id);

            CREATE INDEX IF NOT EXISTS idx_findings_severity
                ON findings(severity);
            """
        )


def save_scan(result: dict[str, Any]) -> dict[str, Any]:
    scan_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    with _connect() as db:
        db.execute(
            """
            INSERT INTO scans (
                id, filename, created_at, status, size_bytes,
                files_detected, files_extracted, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_id,
                result["filename"],
                created_at,
                "completed",
                result["size_bytes"],
                result["files_detected"],
                result["files_extracted"],
                json.dumps(result, ensure_ascii=False),
            ),
        )

        for scan in result.get("scans", []):
            for finding in scan.get("findings", []):
                fingerprint = finding.get("fingerprint")
                finding_id = fingerprint or str(uuid.uuid4())

                # A fingerprint may recur in separate scans. Scope its
                # database identity to this scan to preserve scan history.
                finding_id = f"{scan_id}:{finding_id}"

                db.execute(
                    """
                    INSERT INTO findings (
                        id, scan_id, scanner, category, severity,
                        confidence, title, description, file, line,
                        status, remediation, rule_id, fingerprint
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        finding_id,
                        scan_id,
                        scan.get("scanner", finding.get("scanner", "unknown")),
                        _enum_value(finding.get("category", "Configuration")),
                        _enum_value(finding.get("severity", "Informational")),
                        float(finding.get("confidence") or 0),
                        finding.get("title", "Untitled finding"),
                        finding.get("description", ""),
                        finding.get("file", ""),
                        finding.get("line"),
                        _enum_value(finding.get("status", "Open")),
                        finding.get("remediation"),
                        finding.get("rule_id"),
                        fingerprint,
                    ),
                )

    return {
        "id": scan_id,
        "filename": result["filename"],
        "created_at": created_at,
        "status": "completed",
        "size_bytes": result["size_bytes"],
        "files_detected": result["files_detected"],
        "files_extracted": result["files_extracted"],
        "findings_count": sum(
            len(scan.get("findings", []))
            for scan in result.get("scans", [])
        ),
        "analysis": result.get("analysis", {}),
        "scan_plan": result.get("scan_plan", {}),
        "scans": result.get("scans", []),
        "message": result.get("message", "Project analyzed successfully."),
    }


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def list_scans() -> list[dict[str, Any]]:
    with _connect() as db:
        rows = db.execute(
            """
            SELECT id, filename, created_at, status, size_bytes,
                   files_detected, files_extracted
            FROM scans
            ORDER BY created_at DESC
            """
        ).fetchall()

        results = []
        for row in rows:
            item = dict(row)
            item["findings_count"] = db.execute(
                "SELECT COUNT(*) FROM findings WHERE scan_id = ?",
                (item["id"],),
            ).fetchone()[0]
            results.append(item)

        return results


def get_scan(scan_id: str) -> dict[str, Any] | None:
    with _connect() as db:
        row = db.execute(
            "SELECT * FROM scans WHERE id = ?", (scan_id,)
        ).fetchone()

        if row is None:
            return None

        scan = dict(row)
        result = json.loads(scan.pop("result_json"))
        scan.update(result)
        scan["id"] = row["id"]
        scan["created_at"] = row["created_at"]
        scan["status"] = row["status"]
        scan["findings_count"] = db.execute(
            "SELECT COUNT(*) FROM findings WHERE scan_id = ?",
            (scan_id,),
        ).fetchone()[0]
        return scan


def list_findings(scan_id: str | None = None) -> list[dict[str, Any]]:
    with _connect() as db:
        if scan_id:
            rows = db.execute(
                """
                SELECT * FROM findings
                WHERE scan_id = ?
                ORDER BY
                    CASE lower(severity)
                        WHEN 'critical' THEN 0
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END,
                    file, line
                """,
                (scan_id,),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT * FROM findings
                ORDER BY rowid DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]



ALLOWED_FINDING_STATUSES = {"open", "resolved", "ignored"}


def update_finding_status(
    finding_id: str,
    status: str,
) -> dict[str, Any] | None:
    """Update a finding status and return the updated record."""
    normalized_status = status.strip().lower()

    if normalized_status not in ALLOWED_FINDING_STATUSES:
        raise ValueError(
            "Invalid status. Allowed values: open, resolved, ignored."
        )

    with _connect() as db:
        cursor = db.execute(
            """
            UPDATE findings
            SET status = ?
            WHERE id = ?
            """,
            (normalized_status, finding_id),
        )

        if cursor.rowcount == 0:
            return None

        row = db.execute(
            "SELECT * FROM findings WHERE id = ?",
            (finding_id,),
        ).fetchone()

        return dict(row) if row else None
