"""Public runtime capability description."""

from fastapi import APIRouter, Depends

from opsgraph.api.dependencies import get_settings_from_request
from opsgraph.api.schemas import ConfigResponse
from opsgraph.config import Settings

router = APIRouter(prefix="/api/v1", tags=["config"])


@router.get("/config", response_model=ConfigResponse)
async def config(settings: Settings = Depends(get_settings_from_request)) -> ConfigResponse:
    return ConfigResponse(
        profile=settings.profile,
        model_provider=settings.model_provider,
        domains=("bankops", "awardlens"),
        local_ingestion_enabled=settings.profile == "local",
        max_tool_calls=settings.max_tool_calls,
    )
