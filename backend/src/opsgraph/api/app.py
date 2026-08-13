"""FastAPI application factory."""

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from opsgraph import __version__
from opsgraph.api.dependencies import AppServices
from opsgraph.api.routes.chat import router as chat_router
from opsgraph.api.routes.awardlens import local_router as awardlens_local_router
from opsgraph.api.routes.awardlens import public_router as awardlens_public_router
from opsgraph.api.routes.config import router as config_router
from opsgraph.api.routes.evaluations import router as evaluations_router
from opsgraph.api.routes.ingest import router as ingest_router
from opsgraph.api.routes.runs import router as runs_router
from opsgraph.config import Settings, get_settings
from opsgraph.contracts.errors import OpsGraphError
from opsgraph.observability.tracing import configure_telemetry, traced


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application with explicit dependencies for test isolation."""

    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="OpsGraph API",
        version=__version__,
        docs_url=None if resolved_settings.profile == "aws-demo" else "/docs",
    )
    app.state.settings = resolved_settings
    app.state.services = AppServices(resolved_settings)
    tracer_provider = configure_telemetry(resolved_settings)
    if tracer_provider is not None:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=tracer_provider,
            excluded_urls="health/live,health/ready",
        )

    @app.middleware("http")
    async def correlation_id(request: Request, call_next):
        value = f"corr-{uuid4().hex}"
        request.state.correlation_id = value
        with traced(
            "opsgraph.request",
            {
                "correlation_id": value,
                "http_method": request.method,
                "http_route": request.url.path,
                "authorization": request.headers.get("authorization"),
                "cookie": request.headers.get("cookie"),
            },
        ):
            response = await call_next(request)
        response.headers["X-Correlation-ID"] = value
        return response

    @app.exception_handler(OpsGraphError)
    async def domain_error(request: Request, error: OpsGraphError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": error.as_dict(),
                "correlation_id": request.state.correlation_id,
            },
        )

    @app.get("/health/live", tags=["health"])
    async def liveness() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready", tags=["health"])
    async def readiness() -> dict[str, str]:
        return {"status": "ready"}

    app.include_router(config_router)
    app.include_router(chat_router)
    app.include_router(awardlens_public_router)
    app.include_router(evaluations_router)
    if resolved_settings.profile == "local":
        app.include_router(awardlens_local_router)
        app.include_router(ingest_router)
        app.include_router(runs_router)

    return app


app = create_app()
