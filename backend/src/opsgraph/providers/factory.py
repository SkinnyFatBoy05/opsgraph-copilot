"""Provider selection from validated settings."""

from typing import Any

from opsgraph.config import Settings
from opsgraph.providers.base import AgentModel
from opsgraph.providers.bedrock import BedrockAgentModel
from opsgraph.providers.fake import DeterministicFakeModel
from opsgraph.providers.ollama import OllamaAgentModel


def build_agent_model(
    settings: Settings,
    *,
    bedrock_client: Any | None = None,
) -> AgentModel:
    if settings.model_provider == "ollama":
        return OllamaAgentModel(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    if settings.model_provider == "bedrock":
        return BedrockAgentModel(
            model_id=settings.bedrock_model_id,
            region=settings.aws_region,
            client=bedrock_client,
        )
    return DeterministicFakeModel()
