from fastapi import APIRouter, Body, HTTPException, Query

from backend.services.persistence import (
    get_scan,
    list_findings,
    list_scans,
    update_finding_status,
)

router = APIRouter(prefix="/api", tags=["Scans"])


@router.get("/scans")
def scans_list():
    return list_scans()


@router.get("/scans/{scan_id}")
def scan_detail(scan_id: str):
    result = get_scan(scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return result


@router.get("/scans/{scan_id}/findings")
def scan_findings(scan_id: str):
    if get_scan(scan_id) is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return list_findings(scan_id)


@router.get("/findings")
def findings_list(scan_id: str | None = Query(default=None)):
    if scan_id and get_scan(scan_id) is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return list_findings(scan_id)



@router.patch("/findings/{finding_id}/status")
def finding_status_update(
    finding_id: str,
    status: str = Body(embed=True),
):
    try:
        finding = update_finding_status(finding_id, status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found.")

    return finding
