
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.metrics import FINDINGS_TOTAL, SCANS_TOTAL
from backend.security.secure_extraction import extract_archive_safely
from backend.security.secure_upload import (
    MAX_ARCHIVE_SIZE,
    UnsafeArchiveError,
    validate_zip_archive,
)
from backend.services.persistence import save_scan
from backend.services.project_analyzer import analyze_project
from backend.services.scan_executor import execute_scan_plan
from backend.services.scan_planner import create_scan_plan

router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"],
)


def determine_scan_status(scan_results) -> str:
    """
    Determine the overall status based on individual scanner results.

    completed: all scanners completed successfully.
    partial: at least one scanner completed and another failed.
    failed: all executed scanners failed.
    """

    if not scan_results:
        return "completed"

    successful_scans = sum(
        scan.status == "completed"
        for scan in scan_results
    )

    failed_scans = sum(
        scan.status == "failed"
        for scan in scan_results
    )

    if successful_scans == len(scan_results):
        return "completed"

    if failed_scans == len(scan_results):
        return "failed"

    return "partial"


@router.post("/upload")
async def upload_project(file: UploadFile = File(...)):
    """
    Receive a project ZIP, validate it, extract it safely,
    and perform static project analysis and planned security scans.
    """

    filename = file.filename or ""

    if not filename.lower().endswith(".zip"):
        await file.close()
        raise HTTPException(
            status_code=400,
            detail="Only ZIP archives are supported.",
        )

    with TemporaryDirectory(prefix="securescan-") as temp_dir:
        temp_path = Path(temp_dir)

        archive_path = temp_path / "project.zip"
        workspace = temp_path / "workspace"

        total_size = 0

        try:
            # 1. Save the complete upload, enforcing the size limit.
            with archive_path.open("wb") as destination:
                while chunk := await file.read(1024 * 1024):
                    total_size += len(chunk)

                    if total_size > MAX_ARCHIVE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=(
                                "Archive exceeds the maximum allowed size of 100 MB."
                            ),
                        )

                    destination.write(chunk)

            # 2. Validate the ZIP only after the upload is complete.
            members = validate_zip_archive(archive_path)

            # 3. Extract the validated archive into an isolated workspace.
            extracted_files = extract_archive_safely(
                archive_path,
                workspace,
            )

            # 4. Analyze project structure without executing its code.
            analysis = analyze_project(workspace)

            # 5. Determine which scanners are applicable.
            scan_plan = create_scan_plan(analysis)

            # 6. Execute the planned scans.
            scan_results = execute_scan_plan(
                scan_plan,
                workspace,
            )

        except UnsafeArchiveError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        except HTTPException:
            raise

        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Project analysis failed: {exc}",
            ) from exc

        finally:
            await file.close()

        # 7. Determine the overall scan status.
        overall_status = determine_scan_status(scan_results)

        # 8. Record scan and finding metrics.
        SCANS_TOTAL.labels(status=overall_status).inc()

        for scan_result in scan_results:
            for finding in scan_result.findings:
                severity = finding.severity.value.lower()

                FINDINGS_TOTAL.labels(
                    severity=severity,
                ).inc()

        status_messages = {
            "completed": "Project analysis completed successfully.",
            "partial": "Project analysis partially completed.",
            "failed": "All applicable scanners failed.",
        }

        # 9. Assemble the complete scan result.
        result = {
            "status": overall_status,
            "filename": filename,
            "size_bytes": total_size,
            "files_detected": len(members),
            "files_extracted": len(extracted_files),
            "analysis": asdict(analysis),
            "scan_plan": {
                "enabled": scan_plan.enabled_scanners,
                "skipped": scan_plan.skipped_scanners,
            },
            "scans": [
                {
                    "scanner": scan_result.scanner,
                    "status": scan_result.status,
                    "error": scan_result.error,
                    "findings": [
                        asdict(finding)
                        for finding in scan_result.findings
                    ],
                }
                for scan_result in scan_results
            ],
            "message": status_messages[overall_status],
        }

        # 10. Persist the scan before returning its result.
        try:
            persisted = save_scan(result)

        except (OSError, RuntimeError, ValueError) as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Scan completed but could not be persisted: {exc}",
            ) from exc

        return {
            **result,
            "id": persisted["id"],
            "created_at": persisted["created_at"],
        }
