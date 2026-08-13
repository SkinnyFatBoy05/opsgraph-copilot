# OpsGraph Copilot

[![CI](https://github.com/SkinnyFatBoy05/opsgraph-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/SkinnyFatBoy05/opsgraph-copilot/actions/workflows/ci.yml)

OpsGraph is one deliberately compact AI engineering project with two synthetic domains:

- **BankOps Copilot** answers policy and operational-data questions with RAG, guarded text-to-SQL, deterministic tools, and a bounded LangGraph workflow.
- **AwardLens AU** audits a narrow synthetic payroll dataset with deterministic calculations, manual-review boundaries, grounded explanations, and safe reports.

The default configuration is free: it uses a deterministic fake model, local FAISS, and SQLite. Ollama and Amazon Bedrock are optional adapters. All records are synthetic, and AwardLens is an educational prototype—not legal, payroll, financial, or compliance advice.

## Design previews

The application ships with responsive BankOps and AwardLens workspaces. These are design previews; run the project to exercise the live workflows.

![BankOps desktop workspace](design/concepts/bankops-desktop.png)

![AwardLens desktop workspace](design/concepts/awardlens-desktop.png)

## Fastest way to see everything

With Git and Docker Desktop (or Docker Engine with Compose) running:

```powershell
git clone https://github.com/SkinnyFatBoy05/opsgraph-copilot.git
cd opsgraph-copilot
docker compose up --build api web
```

Open <http://localhost:8080>. Try these requests:

1. BankOps: `Which open complaint cases are late and what policy applies?`
2. AwardLens: load the demo audit, then ask `How many findings need manual review and what policy applies?`
3. Evaluation: open the Evaluation workspace to inspect the SHA-256-checksummed 40-case report.

When finished, stop the demo with `docker compose down`.

The complete click-by-click walkthrough is in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md). The architecture and capability map links each production-AI concept to its code and tests in [docs/CONCEPT_MAP.md](docs/CONCEPT_MAP.md).

## Local development

Requirements: Python 3.12+, [`uv`](https://docs.astral.sh/uv/), Node.js 22+, and npm. Copy the example configuration to the backend working directory before starting it:

```powershell
Copy-Item .env.example backend/.env
```

On macOS or Linux, use `cp .env.example backend/.env` and replace `npm.cmd` with `npm` in the commands below.

Terminal 1:

```powershell
cd backend
uv sync
uv run uvicorn opsgraph.api.app:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Open <http://127.0.0.1:5173>. FastAPI documentation is at <http://127.0.0.1:8000/docs>.

## How the concepts execute

```text
React UI -> FastAPI /chat -> input guard -> supervisor/router
    -> policy specialist -> RAG over source-labeled chunks
    -> data specialist   -> allow-listed, AST-validated read-only SQL
    -> calculation       -> deterministic Python function
    -> synthesis         -> grounded structured output
    -> verifier          -> citation and numeric-fact checks
    -> response + evidence + SQL + trace + latency + cost
```

LangGraph owns the typed state and conditional branches. The model may interpret language, but application code owns permissions, SQL execution, exact calculations, tool budgets, evidence IDs, and release gates. Unsupported or unsafe work becomes a visible manual-review outcome.

See [Architecture](docs/ARCHITECTURE.md) for component boundaries, runtime profiles, and the end-to-end request sequence.

## Verification

Backend and deterministic evaluation:

```powershell
cd backend
uv run pytest -q
uv run python -m opsgraph.evaluation.runner --provider fake --output ..\evaluation\reports\local
cd ..
python scripts\verify_artifacts.py --report evaluation\reports\local\latest.json
```

Frontend:

```powershell
cd frontend
npm.cmd test -- --run
npm.cmd run build
npm.cmd exec playwright install chromium
npm.cmd run test:e2e
```

Delivery configuration:

```powershell
docker compose config --quiet
```

GitHub Actions repeats backend tests, the pgvector integration test, evaluation gates, checksum verification, frontend tests/build, browser E2E flows, and container smoke tests on every change.

## Optional model providers

Fake (default, deterministic, zero API cost):

```powershell
$env:OPSGRAPH_MODEL_PROVIDER="fake"
```

Local Ollama:

```powershell
$env:OPSGRAPH_MODEL_PROVIDER="ollama"
$env:OPSGRAPH_OLLAMA_BASE_URL="http://localhost:11434"
$env:OPSGRAPH_OLLAMA_MODEL="qwen3:4b"
```

Amazon Bedrock uses the normal AWS credential chain—never hard-coded keys:

```powershell
cd backend
uv sync --extra aws
$env:OPSGRAPH_MODEL_PROVIDER="bedrock"
$env:OPSGRAPH_AWS_REGION="ap-southeast-2"
$env:OPSGRAPH_BEDROCK_MODEL_ID="your-enabled-model-or-inference-profile"
```

Provider selection does not change the graph, tools, SQL guard, verifier, or API contract.

## Optional infrastructure

The base Compose profile runs only the API and web application. PostgreSQL/pgvector and OpenTelemetry/Jaeger are optional so the learning path stays inexpensive. The live demo remains on SQLite and FAISS unless you explicitly integrate another store; the `data` profile starts pgvector for the included adapter integration test.

```powershell
docker compose --profile data up -d postgres
cd backend
$env:OPSGRAPH_TEST_POSTGRES_URL="postgresql://opsgraph:local-synthetic-only@localhost:55432/opsgraph"
uv run pytest tests/integration/test_pgvector_retrieval.py -q
```

To export application traces to the optional OpenTelemetry Collector and inspect them in Jaeger at <http://localhost:16686>:

```powershell
$env:OPSGRAPH_TELEMETRY_ENABLED="true"
docker compose --profile observability up --build
```

## Study path

Start with [learning/AI_ENGINEERING_HANDBOOK.md](learning/AI_ENGINEERING_HANDBOOK.md). It teaches Python, LLM fundamentals, prompting, context engineering, RAG, vectors, text-to-SQL, tool calling, LangGraph, production APIs, providers, observability, evaluation, security, CI/CD, Git/Agile practice, and both complete request walkthroughs.

Suggested order:

1. Run the UI and the two demo questions.
2. Read handbook Modules 1–8 and trace the referenced code.
3. Repeat the BankOps and AwardLens walkthroughs in Modules 17–18.
4. Complete one “Do it yourself” exercise at a time on a feature branch.
5. Use Module 19 to practise explaining architecture and trade-offs aloud.

## Repository map

- `backend/src/opsgraph/orchestration/`: graph, nodes, state, tool budget, service.
- `backend/src/opsgraph/retrieval/`: loaders, chunking, embeddings, FAISS, pgvector.
- `backend/src/opsgraph/analytics_sql/`: semantic schema, SQLGlot guard, read-only executors.
- `backend/src/opsgraph/tools/`: schemas, registry, authorization, domain tools.
- `backend/src/opsgraph/domains/awardlens/`: strict CSV ingestion, rules, calculations, audit, report.
- `backend/src/opsgraph/providers/`: fake, Ollama, Bedrock, provider factory.
- `backend/src/opsgraph/observability/`: tracing, redaction, cost estimation, bounded run records.
- `backend/src/opsgraph/evaluation/` and `evaluation/cases/`: dataset, judges, metrics, checksummed reports.
- `frontend/src/features/`: BankOps, AwardLens, and Evaluation workspaces.
- `.github/workflows/ci.yml`, `docker-compose.yml`, and Dockerfiles: repeatable delivery.

## Honest scope

This repository demonstrates production architecture patterns, but it is not a deployed regulated service. A real deployment still needs enterprise identity and tenant isolation, managed secrets, reviewed data-retention controls, provider quotas, incident response, legal/domain approval, live-model repeated evaluation, and operational ownership.

All included operational and payroll records are synthetic. Read [Data provenance and safe use](docs/DATA_AND_SAFETY.md) before modifying the datasets or rules. Do not upload real customer, employee, payroll, or confidential data to this portfolio demo.

## License

Released under the [MIT License](LICENSE).

For vulnerability reporting and deployment warnings, read the [Security Policy](SECURITY.md).
