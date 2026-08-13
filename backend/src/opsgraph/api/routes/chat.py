"""Grounded chat endpoint."""

from uuid import uuid4

from fastapi import APIRouter, Depends, Request

from opsgraph.api.dependencies import AppServices, get_services
from opsgraph.api.schemas import (
    ChatRequest,
    ChatResponse,
    EvidenceResponse,
    SqlResponse,
    ToolTraceResponse,
    TraceResponse,
)
from opsgraph.contracts.runs import RunResult

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    services: AppServices = Depends(get_services),
) -> ChatResponse:
    key = services.cache_key(payload.domain, payload.question)
    result = services.response_cache.get(key)
    cached = result is not None
    if result is None:
        service = await services.graph_service()
        result = await service.run(payload.domain, payload.question)
        services.response_cache.set(key, result)

    correlation_id = getattr(request.state, "correlation_id", f"corr-{uuid4().hex}")
    response = to_chat_response(result, correlation_id=correlation_id, cached=cached)
    services.run_recorder.record(
        result,
        correlation_id=correlation_id,
        cached=cached,
    )
    services.run_store.set(result.trace.run_id, response)
    return response


def to_chat_response(
    result: RunResult,
    *,
    correlation_id: str,
    cached: bool,
) -> ChatResponse:
    sql_result = next(
        (
            tool.data
            for tool in result.tool_results
            if tool.name in {"query_cases", "query_award_findings"}
        ),
        None,
    )
    sql = SqlResponse.model_validate(sql_result) if sql_result else None
    tool_status = {tool.call_id: tool.status for tool in result.tool_results}
    return ChatResponse(
        status=result.trace.status,
        correlation_id=correlation_id,
        answer=result.answer.text,
        limitations=result.answer.limitations,
        evidence=tuple(
            EvidenceResponse(
                id=item.id,
                kind=item.kind,
                title=item.title,
                text=item.text,
                source_uri=item.source_uri,
                section=item.section,
                effective_date=item.effective_date,
                score=item.score,
            )
            for item in result.evidence
        ),
        sql=sql,
        trace=TraceResponse(
            run_id=result.trace.run_id,
            route=result.trace.route,
            agents=result.trace.agents,
            tool_call_count=len(result.trace.tool_calls),
            tool_calls=tuple(
                ToolTraceResponse(
                    name=call.name,
                    status=tool_status.get(call.id, "failed"),
                )
                for call in result.trace.tool_calls
            ),
            provider=result.trace.provider,
            model=result.trace.model,
            started_at=result.trace.started_at,
            completed_at=result.trace.completed_at,
            estimated_cost_usd=result.trace.estimated_cost_usd,
            cached=cached,
        ),
        error_code=result.error_code,
    )
