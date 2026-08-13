"""Amazon Bedrock Converse adapter with structured JSON output."""

import asyncio
import json
from typing import Any

from pydantic import BaseModel

from opsgraph.providers.structured import StructuredAgentModel


class BedrockAgentModel(StructuredAgentModel):
    provider_name = "bedrock"

    def __init__(
        self,
        *,
        model_id: str,
        region: str,
        client: Any | None = None,
    ) -> None:
        if not model_id.strip():
            raise ValueError("a Bedrock model ID is required")
        self.model_name = model_id
        self.region = region
        self._client = client or _create_client(region)

    async def _structured_completion(
        self,
        system: str,
        payload: dict[str, Any],
        response_model: type[BaseModel],
    ):
        schema = response_model.model_json_schema()
        request = {
            "modelId": self.model_name,
            "system": [{"text": system}],
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": json.dumps(payload, separators=(",", ":"))}],
                }
            ],
            "inferenceConfig": {"maxTokens": 1_500, "temperature": 0},
            "outputConfig": {
                "textFormat": {
                    "type": "json_schema",
                    "structure": {
                        "jsonSchema": {
                            "name": response_model.__name__.lower(),
                            "description": response_model.__doc__ or "Validated response",
                            "schema": json.dumps(schema, separators=(",", ":")),
                        }
                    },
                }
            },
        }
        response = await asyncio.to_thread(self._client.converse, **request)
        content = response["output"]["message"]["content"][0]["text"]
        return response_model.model_validate_json(content)


def _create_client(region: str):
    try:
        import boto3
    except ImportError as error:  # pragma: no cover - only optional cloud setup
        raise RuntimeError("Install the 'aws' dependency group to use Bedrock.") from error
    return boto3.client("bedrock-runtime", region_name=region)
