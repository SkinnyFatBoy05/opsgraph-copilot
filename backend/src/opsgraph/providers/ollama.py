"""Ollama structured-output adapter using the local HTTP API."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.request import Request, urlopen

from pydantic import BaseModel

from opsgraph.providers.structured import StructuredAgentModel

OllamaTransport = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


class OllamaAgentModel(StructuredAgentModel):
    provider_name = "ollama"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        transport: OllamaTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self._transport = transport or _post_json

    async def _structured_completion(
        self,
        system: str,
        payload: dict[str, Any],
        response_model: type[BaseModel],
    ):
        request = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload, separators=(",", ":"))},
            ],
            "format": response_model.model_json_schema(),
            "stream": False,
            "options": {"temperature": 0},
        }
        response = await self._transport(f"{self.base_url}/api/chat", request)
        content = response["message"]["content"]
        return response_model.model_validate_json(content)


async def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(_post_json_sync, url, payload)


def _post_json_sync(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - configured local endpoint
        return json.loads(response.read().decode("utf-8"))
