from fastapi.testclient import TestClient

from opsgraph.api.app import create_app
from opsgraph.config import Settings


def test_test_profile_requires_no_credentials(monkeypatch):
    """Catches a regression that makes deterministic local tests need paid credentials."""
    monkeypatch.setenv("OPSGRAPH_PROFILE", "test")
    monkeypatch.delenv("OPSGRAPH_MODEL_PROVIDER", raising=False)

    settings = Settings()

    assert settings.profile == "test"
    assert settings.model_provider == "fake"


def test_optional_provider_settings_have_safe_local_defaults() -> None:
    settings = Settings()

    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "qwen3:4b"
    assert settings.aws_region == "ap-southeast-2"
    assert settings.bedrock_model_id == ""


def test_liveness_contract_is_stable():
    """Catches removal or accidental renaming of the process liveness route."""
    client = TestClient(create_app(Settings(profile="test")))

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
