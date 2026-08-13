import json

from opsgraph.contracts.evidence import EvidenceRef
from opsgraph.contracts.runs import SynthesisRequest
from opsgraph.providers.ollama import OllamaAgentModel


async def test_ollama_uses_structured_json_for_routing_and_synthesis() -> None:
    requests: list[tuple[str, dict]] = []
    responses = iter(
        (
            {"message": {"content": json.dumps({"route": "rag", "reason": "Needs policy evidence."})}},
            {
                "message": {
                    "content": json.dumps(
                        {
                            "text": "The policy evidence answers the question.",
                            "citation_ids": ["doc-1"],
                            "numeric_facts": {},
                            "limitations": [],
                        }
                    )
                }
            },
        )
    )

    async def transport(url: str, payload: dict) -> dict:
        requests.append((url, payload))
        return next(responses)

    model = OllamaAgentModel(
        base_url="http://localhost:11434",
        model="qwen3:4b",
        transport=transport,
    )
    decision = await model.route("What policy applies?", "bankops")
    draft = await model.synthesize(
        SynthesisRequest(
            question="What policy applies?",
            domain="bankops",
            evidence=(
                EvidenceRef(
                    id="doc-1",
                    domain="bankops",
                    kind="document",
                    title="Policy",
                    text="Synthetic policy text.",
                ),
            ),
        )
    )

    assert decision.route == "rag"
    assert draft.citation_ids == ("doc-1",)
    assert all(url.endswith("/api/chat") for url, _ in requests)
    assert all(request["stream"] is False for _, request in requests)
    assert isinstance(requests[0][1]["format"], dict)
    assert model.provider_name == "ollama"
