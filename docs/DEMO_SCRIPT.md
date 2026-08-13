# Ten-minute demo script

This is the shortest path through every major concept. Use the free fake provider first so the result is repeatable.

## 1. Start the application

```powershell
docker compose up --build api web
```

Open <http://localhost:8080>. If Docker is unavailable, use the two-terminal local commands in the root README.

## 2. Demonstrate BankOps RAG plus SQL

Select **BankOps** and ask:

> Which open complaint cases are late and what policy applies?

Show these panels in order:

1. **Answer:** combines operational data with policy language.
2. **Evidence:** contains source-labeled policy chunks and SQL-result evidence.
3. **SQL:** shows the normalized, read-only, bounded query.
4. **Trace:** shows hybrid routing, policy and data specialists, tool calls, synthesis, and verification.
5. **Cost:** shows provider/model, latency, tokens when known, and estimated cost.

Explain: the model interprets the request and writes grounded prose. FAISS retrieves evidence. SQLGlot and allow-lists protect query execution. The verifier rejects invented citation IDs or changed numbers.

## 3. Demonstrate AwardLens deterministic boundaries

Select **AwardLens**, click **Load demo audit**, and inspect the findings. Then ask:

> How many audit findings need manual review and what policy applies?

Show:

1. Supported records have deterministic calculation lines and exact totals.
2. Unsupported records have null expected/variance/liability values and `manual_review` status.
3. The SQL panel counts findings but never calculates pay.
4. Policy evidence explains the versioned, intentionally narrow rule scope.
5. The report opens as escaped HTML with limitations and source metadata.

Explain: calculation belongs to ordinary Python, not the LLM. The source hash detects unexpected rule-file changes, but human review is still required for legal correctness.

## 4. Demonstrate evaluation

Open **Evaluation**. The checked-in, SHA-256-checksummed deterministic report contains 40 cases across BankOps, adversarial security, and AwardLens.

Explain the hard gates: unknown citations, unsafe SQL execution, changed numeric facts, unsupported AwardLens liability, or secret leakage blocks release even if the average score looks good.

Regenerate it with:

```powershell
cd backend
uv run python -m opsgraph.evaluation.runner --provider fake --output ..\evaluation\reports\local
cd ..
python scripts\verify_artifacts.py --report evaluation\reports\local\latest.json
```

## 5. Demonstrate provider switching

Open `backend/src/opsgraph/providers/factory.py`, `ollama.py`, and `bedrock.py`.

Explain: all providers implement the same typed contract, and the API response records provider/model metadata. Switching providers does not grant new tools or weaken the verifier. The fake provider makes CI free and deterministic; Ollama provides a local live-model path; Bedrock provides a cloud adapter using the AWS identity chain.

## 6. Demonstrate delivery and observability

Open `.github/workflows/ci.yml` and `docker-compose.yml`.

Explain: CI performs locked installs, backend tests, evaluation and checksum gates, frontend tests/build, and image builds. OpenTelemetry/Jaeger and pgvector are optional Compose profiles so the default demo stays small and cheap.

## 7. Finish honestly

Say:

> This is a fully runnable synthetic portfolio system that executes the architecture patterns end to end. It is not a deployed regulated product. Production work would add enterprise authentication, tenancy, managed secrets and storage, reviewed retention, live-model repeated evaluation, provider quotas, incident response, and formal domain approval.

Then use `learning/AI_ENGINEERING_HANDBOOK.md` to answer deeper questions or choose a hands-on extension.
