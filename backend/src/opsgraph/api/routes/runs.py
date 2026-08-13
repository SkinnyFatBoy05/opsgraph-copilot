"""Bounded local run lookup; not registered in the AWS profile."""

from fastapi import APIRouter, Depends, HTTPException

from opsgraph.api.dependencies import AppServices, get_services
from opsgraph.api.schemas import ChatResponse

router = APIRouter(prefix="/api/v1", tags=["runs"])


@router.get("/runs/{run_id}", response_model=ChatResponse)
async def get_run(
    run_id: str,
    services: AppServices = Depends(get_services),
) -> ChatResponse:
    response = services.run_store.get(run_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return response
