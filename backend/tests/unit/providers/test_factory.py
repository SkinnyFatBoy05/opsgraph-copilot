from opsgraph.config import Settings
from opsgraph.providers.bedrock import BedrockAgentModel
from opsgraph.providers.factory import build_agent_model
from opsgraph.providers.fake import DeterministicFakeModel
from opsgraph.providers.ollama import OllamaAgentModel


def test_provider_factory_selects_the_configured_adapter() -> None:
    assert isinstance(build_agent_model(Settings(model_provider="fake")), DeterministicFakeModel)
    assert isinstance(
        build_agent_model(
            Settings(
                model_provider="ollama",
                ollama_base_url="http://localhost:11434",
                ollama_model="qwen3:4b",
            )
        ),
        OllamaAgentModel,
    )
    assert isinstance(
        build_agent_model(
            Settings(
                model_provider="bedrock",
                bedrock_model_id="amazon.nova-micro-v1:0",
            ),
            bedrock_client=object(),
        ),
        BedrockAgentModel,
    )
