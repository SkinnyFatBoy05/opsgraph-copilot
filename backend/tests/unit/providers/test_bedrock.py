import json

from opsgraph.providers.bedrock import BedrockAgentModel


class FakeBedrockClient:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def converse(self, **request) -> dict:
        self.requests.append(request)
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps(
                                {"route": "sql", "reason": "Needs structured records."}
                            )
                        }
                    ]
                }
            }
        }


async def test_bedrock_uses_converse_with_zero_temperature() -> None:
    client = FakeBedrockClient()
    model = BedrockAgentModel(
        model_id="amazon.nova-micro-v1:0",
        region="ap-southeast-2",
        client=client,
    )

    decision = await model.route("How many cases are overdue?", "bankops")

    assert decision.route == "sql"
    assert client.requests[0]["modelId"] == "amazon.nova-micro-v1:0"
    assert client.requests[0]["inferenceConfig"]["temperature"] == 0
    assert client.requests[0]["outputConfig"]["textFormat"]["type"] == "json_schema"
    assert model.provider_name == "bedrock"
