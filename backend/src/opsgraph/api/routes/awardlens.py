"""Profile-aware AwardLens demo, local audit, and report endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse

from opsgraph.api.dependencies import AppServices, get_services, get_settings_from_request
from opsgraph.config import Settings
from opsgraph.domains.awardlens.csv_ingestion import PayrollCsvError
from opsgraph.domains.awardlens.models import AuditRun
from opsgraph.domains.awardlens.report import render_audit_report

public_router = APIRouter(prefix="/api/v1/awardlens", tags=["awardlens"])
local_router = APIRouter(prefix="/api/v1/awardlens", tags=["awardlens-local"])


@public_router.get("/demo-audit", response_model=AuditRun)
async def demo_audit(services: AppServices = Depends(get_services)) -> AuditRun:
    return await services.awardlens_demo_audit()


@public_router.get("/demo-report", response_class=HTMLResponse)
async def demo_report(services: AppServices = Depends(get_services)) -> str:
    return render_audit_report(await services.awardlens_demo_audit())


@local_router.post("/audits", response_model=AuditRun, status_code=status.HTTP_201_CREATED)
async def create_audit(
    file: UploadFile,
    x_local_admin_token: str | None = Header(default=None),
    services: AppServices = Depends(get_services),
    settings: Settings = Depends(get_settings_from_request),
) -> AuditRun:
    if x_local_admin_token != settings.local_admin_token:
        raise HTTPException(status_code=401, detail="Invalid local administration token")
    if not (file.filename or "").casefold().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only CSV payroll files are accepted")
    payload = await file.read(settings.max_upload_bytes + 1)
    if len(payload) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Payroll CSV is too large")
    try:
        return await services.create_awardlens_audit(payload)
    except PayrollCsvError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@local_router.get("/audits/{audit_id}", response_model=AuditRun)
async def get_audit(
    audit_id: str,
    services: AppServices = Depends(get_services),
) -> AuditRun:
    audit = services.get_awardlens_audit(audit_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit was not found")
    return audit


@local_router.get("/audits/{audit_id}/report", response_class=HTMLResponse)
async def get_audit_report(
    audit_id: str,
    services: AppServices = Depends(get_services),
) -> str:
    audit = services.get_awardlens_audit(audit_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit was not found")
    return render_audit_report(audit)
