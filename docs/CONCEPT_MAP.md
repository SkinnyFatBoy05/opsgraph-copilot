# Architecture and capability map

Use this page to connect each concept to a concrete implementation and verification step. Open the implementation, run the named test, and explain the boundary in your own words.

| Concept | Where it executes | Proof to run | What to explain |
|---|---|---|---|
| Production Python | `backend/src/opsgraph/contracts/`, `api/dependencies.py` | `uv run pytest tests/unit/contracts -q` | Typed Pydantic boundaries, dependency injection, async I/O, immutable state, and exact money representation. |
| LLM abstraction | `providers/base.py`, `structured.py`, `factory.py` | `uv run pytest tests/unit/providers -q` | The graph depends on a protocol; provider-specific transport and parsing stay behind adapters. |
| Prompt and context engineering | `providers/structured.py`, `retrieval/service.py` | Provider and retrieval unit tests | Prompts define the task and output contract; context code decides which evidence and tool facts enter the request. |
| RAG | `retrieval/loaders.py`, `chunking.py`, `embeddings.py`, `faiss_store.py`, `service.py` | `uv run pytest tests/unit/retrieval -q` | Ingestion, chunking, embedding, top-k search, metadata, evidence IDs, and citation verification. |
| Vector stores | `retrieval/faiss_store.py`, `pgvector_store.py` | Unit tests; pgvector test with its service available | FAISS is the free local default; pgvector demonstrates a durable service behind the same contract. |
| Guarded text-to-SQL | `analytics_sql/schemas.py`, `guard.py`, `executors.py`; `tools/bankops.py`, `tools/awardlens.py` | `uv run pytest tests/unit/analytics_sql tests/security/test_sql_attacks.py -q` | Narrow semantic schema, SQLGlot AST validation, allow-lists, one read-only statement, row limits, parameterized values, and evidence capture. |
| Function calling and tools | `contracts/tools.py`, `tools/registry.py` | Tool-related graph and security tests | A tool schema is not authorization. The registry checks tool, specialist, and domain before invocation and returns typed results. |
| Agentic workflow | `orchestration/state.py`, `graph.py`, `nodes.py`, `budget.py` | `uv run pytest tests/unit/orchestration tests/integration/test_bankops_graph.py -q` | Supervisor, policy, data, calculation, synthesis, verification, one correction attempt, and manual-review exits in a bounded graph. |
| Multi-agent pattern | `orchestration/graph.py` and `nodes.py` | BankOps and AwardLens graph tests | Specialists are roles within one graph, not autonomous chatbots; each receives only its authorized tools. |
| Production API integration | `api/app.py`, `api/schemas.py`, `api/routes/`; `frontend/src/api/` | `uv run pytest tests/api -q`; frontend component/e2e tests | Stable request/response schemas, validation, health endpoints, typed client code, visible evidence, SQL, trace, cost, and limitations. |
| Deterministic AwardLens rules | `domains/awardlens/` and `data/awardlens/rules/` | `uv run pytest tests/unit/domains/awardlens tests/property -q` | Versioned source manifest and hash, supported envelope, Decimal/integer money math, explicit rounding, null liability outside scope, and manual review. |
| Safe reports and ingestion | `domains/awardlens/report.py`, `csv_ingestion.py`, `api/routes/awardlens.py` | API and security tests | Strict schema/size checks, formula-prefix rejection, escaped HTML, no scripts/remote resources, authenticated local mutations. |
| Ollama | `providers/ollama.py` | `uv run pytest tests/unit/providers/test_ollama.py -q` | Local `/api/chat`, structured JSON schema, timeout/error handling, provider metadata, and no per-token bill. |
| Amazon Bedrock | `providers/bedrock.py` | `uv run pytest tests/unit/providers/test_bedrock.py -q` | Converse API, normal AWS identity chain, region/model configuration, structured parsing, and explicit failures. |
| Observability | `observability/tracing.py`, `run_recorder.py`, `redaction.py` | `uv run pytest tests/unit/observability tests/security/test_trace_secrets.py -q` | Named spans, route/tool/provider metadata, bounded run history, secret redaction, latency, and manual-review signals. |
| Cost controls | `observability/costs.py`, `orchestration/budget.py`, response cache | Cost and budget unit tests | Versioned pricing inputs, zero-cost local/fake providers, maximum tool calls, caching, and cost per successful task. |
| Evaluation and benchmarking | `evaluation/cases/`, `backend/src/opsgraph/evaluation/` | Run the evaluation command; inspect `evaluation/reports/deterministic/latest.md` | Forty cases measure routes, retrieval, citations, SQL, numbers, abstention, latency, and cost. Hard safety failures block release. |
| Security testing | `backend/tests/security/`, `tests/property/` | Run those suites directly | Prompt/SQL attacks, secret leakage, output escaping, unsupported conclusions, and invariants over generated inputs. |
| CI/CD | `.github/workflows/ci.yml`, Dockerfiles, `docker-compose.yml` | `docker compose config --quiet`; inspect CI | Locked installs, test/evaluation gates, checksum verification, frontend type-check/build, image builds, and optional profiles. |
| Git and Agile delivery | Commit history plus handbook Module 16 | `git log --oneline` | Small reviewed commits, observable acceptance criteria, spikes for uncertainty, definition of done, and rollback notes. |
| AI-assisted development | Tests, evaluation artifacts, and handbook exercises | Reproduce a change from a failing test | AI tools can accelerate implementation, but the engineer reviews diffs, protects data, validates primary docs, and owns correctness. |

## The key design sentence

“I kept language interpretation probabilistic, but permissions, SQL execution, calculations, evidence IDs, budgets, and release gates deterministic and testable.”

## Evidence standard

Run backend commands from `backend/` unless the command explicitly starts at the repository root.

Do not memorize the table. You are ready to use a claim when you can:

1. Open the exact file.
2. Trace one input to one output.
3. Run the relevant test.
4. Name a failure mode and the control that handles it.
5. State what the prototype still does not provide.
