# Practical AI Engineering Handbook

## Learn RAG, text-to-SQL, agents, evaluation, observability, and deployment through OpsGraph Copilot

Version: 1.0

Audience: Software engineers preparing for AI Engineer and Senior AI Engineer roles

Companion project: `projects/opsgraph-copilot`

Default cost: zero. The deterministic provider, synthetic data, SQLite, FAISS, and local UI require no paid API.

This is a learning guide, not a claim that reading alone creates production experience. Your goal is to understand each design choice, run it, change it, break it safely, measure it, and then explain it honestly in an interview.

## How to use this handbook

Use three passes.

1. Orientation pass: read Modules 1 to 5 without changing code. Run the application and follow one BankOps request.
2. Builder pass: complete every "Do it yourself" exercise. Commit each useful change on a feature branch.
3. Interview pass: answer each checkpoint aloud without looking at the notes. If an answer is vague, return to the relevant code.

Recommended eight-week pace:

- Week 1: Python, APIs, typed contracts, and LLM fundamentals.
- Week 2: prompting, context engineering, embeddings, vector search, and RAG.
- Week 3: guarded text-to-SQL and deterministic tools.
- Week 4: LangGraph, agents, state, routing, verification, and human review.
- Week 5: AwardLens domain calculations, reliability boundaries, and secure reports.
- Week 6: evaluation, benchmarking, observability, latency, cost, and failure analysis.
- Week 7: Docker, CI/CD, Ollama, Bedrock, Git, and Agile delivery.
- Week 8: extend the project, prepare architecture stories, and practise interviews.

## Project map

The project contains two domains that share one AI platform.

- BankOps Copilot answers questions over fictional bank policies and synthetic operational records. It demonstrates RAG, guarded text-to-SQL, hybrid retrieval, calculators, tools, and specialist agents.
- AwardLens AU audits synthetic payroll shifts against a narrow, versioned ruleset. It demonstrates deterministic calculation, source integrity, manual-review boundaries, RAG, SQL over findings, safe explanations, and report generation.

One request follows this path:

```text
React UI -> FastAPI /chat -> input guard -> supervisor/router
    -> policy specialist (RAG)
    -> data specialist (guarded SQL)
    -> calculation specialist (deterministic function)
    -> evidence join -> synthesis -> verifier -> response + trace
```

The graph selects only the branches needed for a question. A hybrid question can run policy and data specialists in the same graph step. The verifier rejects unsupported citations or changed numeric facts. Out-of-scope work ends in manual review.

Start with these files:

- `backend/src/opsgraph/orchestration/graph.py`: graph topology.
- `backend/src/opsgraph/orchestration/nodes.py`: behavior of each node.
- `backend/src/opsgraph/orchestration/state.py`: shared state contract.
- `backend/src/opsgraph/tools/registry.py`: tool allow-list and invocation.
- `backend/src/opsgraph/api/dependencies.py`: application wiring.
- `frontend/src/features/bankops/BankOpsWorkspace.tsx`: BankOps UI.
- `frontend/src/features/awardlens/AwardLensWorkspace.tsx`: AwardLens UI.
- `evaluation/cases/`: deterministic evaluation datasets.

# Module 1 - Production Python for AI systems

## What strong Python means in an AI engineering role

Strong Python is not knowing every library. It is the ability to turn uncertain model behavior into a system with explicit inputs, outputs, errors, tests, and operational limits. AI code still needs normal software engineering: modules with single responsibilities, typed interfaces, dependency injection, safe I/O, deterministic tests, and readable failure modes.

Important Python skills for this project are:

- Data modeling with Pydantic and immutable objects.
- Protocols to separate interfaces from implementations.
- Async I/O for APIs and provider calls.
- Context managers for tracing.
- `Decimal` or integer cents for money instead of binary floating point.
- Path handling with `pathlib`.
- Dependency injection rather than global mutable clients.
- Unit, integration, property, security, API, and end-to-end tests.

## How OpsGraph executes it

Read `backend/src/opsgraph/contracts/runs.py`. `RouteDecision`, `SynthesisRequest`, `DraftAnswer`, `VerifiedAnswer`, and `RunTrace` are Pydantic models. They validate data at component boundaries. `ConfigDict(frozen=True)` makes them immutable after construction. That reduces accidental mutation while parallel graph branches merge state.

Read `backend/src/opsgraph/providers/base.py`. `AgentModel` is a Python `Protocol`. The graph depends on this behavior, not on Ollama, Bedrock, or the fake model directly. Provider switching therefore does not change graph logic.

Read `backend/src/opsgraph/api/dependencies.py`. `AppServices` creates and owns the retrieval service, model adapter, tool registry, SQL executors, caches, and domain rules. This is dependency injection. Tests can create a fresh service with a test configuration instead of depending on production globals.

AwardLens stores money as integer cents. For example, 22248 means AUD 222.48. Multipliers use `Decimal`, and the result is rounded once with an explicit rule. This avoids values such as `222.479999999` and makes exact evaluation possible.

## A useful code-reading method

When studying an unfamiliar Python system, trace one value:

1. Find its public input schema.
2. Find validation and normalization.
3. Find business logic.
4. Find external I/O.
5. Find the output schema.
6. Find tests for success, failure, and boundaries.

For a payroll shift, trace `PayrollRecord` from `models.py` to `csv_ingestion.py`, `calculate_shift`, `run_audit`, the AwardLens API route, and the React table.

## Do it yourself

1. Add an optional `department` field to a synthetic payroll record.
2. Carry it through CSV parsing and the finding database without using it in pay calculations.
3. Add one unit test and one API test.
4. Explain why an optional descriptive field should not change a deterministic monetary result.

## Interview checkpoints

- Why use a Protocol instead of importing one provider everywhere?
- Why are immutable request and result models useful in agent workflows?
- When should an async function be used, and when is it unnecessary?
- Why should currency use integer cents or Decimal?
- What is the difference between a unit test and an integration test in this repository?

# Module 2 - LLM fundamentals, capabilities, and limits

## The mental model

A large language model consumes tokens and predicts a probability distribution for the next token. Repeating that operation produces text. The model does not query your database, browse internal files, or verify a calculation unless the application explicitly gives it those capabilities and checks the result.

Key terms:

- Token: a model-specific unit of text. It may be a word, part of a word, punctuation, or whitespace.
- Context window: the maximum token budget for instructions, conversation, evidence, tool results, and output.
- Parameters: learned weights that encode statistical patterns.
- Temperature: a sampling control. Lower values usually reduce variation but do not create factual guarantees.
- Hallucination: plausible output unsupported by the supplied evidence or reality.
- Embedding: a vector representation used to compare semantic similarity. It is not the same as a generation model.
- Structured output: model output constrained to a schema and then validated by application code.

## What models do well

Models are useful for language transformation, classification, summarization, semantic routing, extracting structure from messy text, and producing explanations from grounded facts. They are especially helpful where rules are difficult to enumerate but errors can be detected and handled.

## What models do poorly

Do not trust an LLM alone for exact arithmetic, authorization, destructive actions, legal conclusions, database mutation, or unsupported citations. Outputs can vary across model versions, prompts, providers, and surrounding context. A fluent answer is not evidence of correctness.

## How OpsGraph handles these limits

The application separates probabilistic and deterministic work:

- Routing and explanation may use a model.
- Retrieval is performed by an embedding service and vector store.
- SQL is generated from a bounded semantic mapping, parsed, allow-listed, and executed read-only.
- Payroll and business-hour calculations are normal Python functions.
- Numeric facts are copied from tool results and verified after synthesis.
- Citation IDs must refer to evidence returned in the current run.
- Unsupported requests become `manual_review` instead of a confident guess.

This separation is one of the most important production AI patterns: let the model interpret language, but let ordinary software own permissions, calculations, and invariants.

## Determinism is a spectrum

The fake provider is fully deterministic and costs nothing. Ollama and Bedrock use temperature zero and structured output, which improves repeatability but does not make outputs mathematically deterministic. Even at temperature zero, changes in infrastructure, model version, quantization, or tie-breaking can change results.

For CI, OpsGraph evaluates the deterministic provider. A live-provider evaluation should be reported separately with multiple repetitions, latency distributions, and model/version metadata.

## Do it yourself

Ask the same question ten times with the fake provider, then with a local Ollama model. Record route, answer wording, citations, latency, and numeric facts. Explain which fields must remain invariant and which may vary safely.

## Interview checkpoints

- Why does temperature zero not guarantee deterministic output?
- What belongs in the model and what belongs in application code?
- What is a context window, and how can an application waste it?
- What is the difference between generation and embeddings?
- How would you prevent an LLM from changing a payroll total?

# Module 3 - Prompt engineering and context engineering

## Prompt engineering

Prompt engineering defines the model's task, role, constraints, output contract, examples, and refusal behavior. A good prompt is specific enough to test. "Be accurate" is vague. "Cite only IDs supplied in the evidence array and preserve every value in numeric_facts exactly" creates observable acceptance criteria.

Useful prompt components are:

1. Objective: what the model must produce.
2. Boundaries: what it must not do.
3. Evidence policy: which sources it may use.
4. Output schema: fields, types, and required values.
5. Failure behavior: abstain or request review when evidence is insufficient.
6. Examples: only when they improve a known failure mode.

## Context engineering

Context engineering is broader. It decides which information enters the context, how it is ordered, how much is included, and how tool state is represented. A perfect prompt with irrelevant or conflicting context still performs poorly.

The basic context budget is:

```text
system instructions + user request + retrieved evidence + tool results
+ conversation state + output allowance <= model context window
```

Good context is relevant, source-labeled, current, non-duplicated, and small enough that important instructions are not buried.

## How OpsGraph executes it

`backend/src/opsgraph/providers/structured.py` contains short provider-neutral instructions for routing and synthesis. It passes typed payloads, not a long free-form transcript. The Pydantic response schema becomes the validation contract.

`backend/src/opsgraph/retrieval/service.py` selects top evidence chunks. `SynthesisRequest` carries only the question, domain, selected evidence, and tool results. The verifier then checks evidence IDs and numeric facts independently of the prompt.

Notice the defense in depth:

- The prompt asks for grounded output.
- The schema rejects malformed structure.
- The verifier rejects invalid citations and modified numbers.
- Evaluation tests measure the observed behavior.

A prompt is never the only safety boundary.

## Common prompt failures

- Too many competing instructions.
- Examples that contradict the written rules.
- Passing entire documents when a few chunks are enough.
- Allowing retrieved text to masquerade as system instructions.
- Asking for prose and JSON simultaneously.
- Hiding business logic inside a prompt where it cannot be reliably tested.
- Changing a prompt without rerunning the evaluation suite.

## Do it yourself

Create a prompt version `prompt-v2` that asks for a one-sentence executive summary plus limitations. Update the cache key, add evaluation expectations, and compare results. Do not overwrite `prompt-v1`; versioning makes changes auditable.

## Interview checkpoints

- What is the difference between prompt engineering and context engineering?
- How do you defend against instructions inside retrieved documents?
- Why validate structured output after the model returns it?
- What should happen when evidence is insufficient?
- How do prompt changes enter CI/CD safely?

# Module 4 - Retrieval-augmented generation (RAG)

## The RAG pipeline

RAG supplies external evidence at request time. A common pipeline is:

```text
documents -> parse -> normalize -> chunk -> embed -> index
question -> embed -> similarity search -> select evidence -> generate -> verify citations
```

RAG is useful when facts change, sources must be cited, private knowledge cannot be placed in model training, or the answer must be traceable. It is not automatically correct: retrieval can miss the right passage, retrieve a misleading passage, or provide too much context.

## Ingestion

`backend/src/opsgraph/retrieval/loaders.py` loads source documents and preserves metadata. `chunking.py` divides text into retrievable units. Good chunks are large enough to contain a complete idea and small enough for precise retrieval. Metadata such as domain, source URI, heading, version, and effective date supports filtering and citations.

Chunking strategies include fixed token windows, sentence-aware chunks, heading-based chunks, and parent-child retrieval. This project deliberately uses a simple, inspectable strategy. In a larger system, evaluate alternatives using real questions rather than selecting a chunk size by intuition.

## Embeddings and search

`embeddings.py` defines an embedding interface and a deterministic hashing provider for free local tests. `faiss_store.py` stores vectors and performs nearest-neighbor search. `pgvector_store.py` demonstrates the same contract for PostgreSQL with pgvector.

The hashing provider is useful for architecture tests, not a claim of state-of-the-art semantic quality. Replace it with a real embedding model when measuring live retrieval quality. The interface remains stable.

Similarity search returns candidates, not truth. Useful improvements include metadata filters, hybrid keyword/vector search, reranking, query rewriting, and diversity selection. Add them only when evaluation demonstrates a retrieval problem.

## Evidence contracts

Every result becomes an `EvidenceRef` with a stable ID, domain, kind, title, text, and metadata. Stable evidence objects allow the UI, verifier, logs, and evaluation code to discuss the same item without parsing prose.

The verifier requires every citation ID to exist in the evidence set for the current domain. This prevents a model from inventing a citation that looks legitimate.

## Measuring retrieval

Important metrics include:

- Recall@k: whether at least one relevant chunk appears in the top k.
- Precision@k: the proportion of retrieved chunks that are relevant.
- Mean reciprocal rank: how early the first relevant result appears.
- Citation correctness: whether the cited passage supports the claim.
- Answer groundedness: whether material claims are supported by evidence.

OpsGraph's deterministic suite measures a simple retrieval hit rate and citation validity. A mature dataset should also label which evidence items are relevant for each question.

## Do it yourself

1. Add a fictional BankOps policy document with overlapping vocabulary.
2. Add five questions and label the expected source.
3. Measure top-1 and top-3 retrieval accuracy.
4. Change chunk size or add a metadata filter.
5. Keep the change only if the dataset improves without breaking other domains.

## Interview checkpoints

- Walk through ingestion and query-time RAG.
- How do chunk size and overlap affect retrieval?
- When would you use FAISS versus pgvector or a managed vector database?
- What is the difference between retrieval quality and answer quality?
- How do you prevent cross-tenant or cross-domain retrieval?

# Module 5 - Vector databases and retrieval architecture

## What a vector store does

A vector store holds embeddings plus identifiers and metadata, then returns nearby vectors under a distance function. It does not understand business permissions automatically. Authorization and metadata filters remain application responsibilities.

Common choices:

- FAISS: excellent for local experiments, batch jobs, and in-process search. It is a library rather than a managed multi-tenant database.
- pgvector: good when PostgreSQL already owns transactional data and operational simplicity matters.
- Pinecone or Weaviate: managed or specialized options that reduce operational burden and add scaling/search features.
- Chroma: convenient for prototypes and local workflows.

Choose based on dataset size, query volume, latency, filtering, tenancy, durability, backups, operational skills, and cost. Do not choose solely from benchmark headlines.

## Distance and normalization

Cosine similarity compares direction, while Euclidean distance compares geometric distance. Dot product is related to cosine similarity when vectors are normalized. The embedding model and index configuration must agree. A mismatch can silently degrade ranking.

Approximate nearest-neighbor indexes trade some recall for speed and memory efficiency. Exact flat indexes are valuable baselines. Measure a proposed approximate index against exact search on representative queries before accepting the trade-off.

## How OpsGraph abstracts storage

The retrieval layer uses a store contract. FAISS and pgvector implementations can be exchanged without changing orchestration. This is a deliberate architecture pattern: keep provider or database specifics at the edge and keep domain workflows stable.

The checked-in application uses FAISS and a deterministic embedding provider so a reviewer can run it without accounts. The pgvector implementation and Docker Compose service show how the architecture grows without making the default experience expensive.

## Production concerns

- Persist the mapping between vector IDs and document metadata.
- Treat embedding model upgrades as data migrations.
- Version documents, chunks, and embeddings.
- Delete or update vectors when source permissions change.
- Encrypt sensitive data and apply tenant filters before search.
- Monitor index size, query latency, empty-result rate, and recall on a labeled set.
- Rebuild indexes reproducibly from source data.

## Do it yourself

Run the pgvector integration test with Docker available. Compare the results with FAISS for the same documents. Record operational differences, not just query output.

## Interview checkpoints

- What is stored in a vector database?
- Why is an embedding-model change a migration?
- When is exact search a better choice than approximate search?
- How would you enforce tenant isolation?
- Why might PostgreSQL plus pgvector be a better business choice than a specialized service?

# Module 6 - Guarded text-to-SQL

## Why text-to-SQL is risky

Text-to-SQL converts a natural-language question into a query. The dangerous version sends a database schema to a model and executes whatever returns. Failure modes include mutation, data exfiltration, expensive scans, unsupported joins, hidden prompt injection, dialect errors, and confident explanations of incorrect results.

A production design needs several independent controls:

1. Use a read-only database identity or read-only database.
2. Expose only approved tables and columns through a semantic schema.
3. Parse the SQL into an abstract syntax tree.
4. Allow-list statement type, functions, tables, columns, and joins.
5. Reject comments, stacked statements, DDL, DML, and dangerous functions.
6. Add a row limit and timeout.
7. Execute through a bounded adapter.
8. Return query evidence and normalized SQL.
9. Evaluate malicious and ambiguous cases.

No single regex can safely validate SQL.

## How OpsGraph executes it

`backend/src/opsgraph/analytics_sql/schemas.py` defines the semantic surface. `guard.py` uses SQLGlot to parse and validate. `executors.py` applies validation, adds a limit, and executes against a read-only connection.

BankOps maps supported intents to known query shapes in `tools/bankops.py`. AwardLens does the same in `tools/awardlens.py`. This is deliberately narrower than arbitrary text-to-SQL. It still demonstrates the architecture while keeping the result easy to reason about.

The normalized SQL and result rows become an evidence object. The answer can state a count only after the tool returns it. The verifier compares the answer's numeric facts with the tool's numeric facts.

Security cases in `evaluation/cases/security.json` and `backend/tests/security/test_sql_attacks.py` attempt mutations and unsafe constructions. A release gate fails if rejected SQL is ever executed.

## What to log

Log the route, normalized query shape, execution duration, result row count, and rejection reason. Do not log raw secrets or unrestricted personal data. In regulated environments, even query text may need redaction or hashing.

## Do it yourself

Add a supported question: "How many complaint cases are still open?" Write the test first. Add the smallest query mapping needed, ensure `LIMIT 200` is present, expose the result as a numeric fact, and add an injection test using the same phrasing.

## Interview checkpoints

- Why is read-only access necessary even with SQL validation?
- Why parse an AST instead of using regexes?
- What belongs in a semantic layer?
- How do you prevent costly but read-only queries?
- How do you prove that a number in the final answer came from the query result?

# Module 7 - Function calling and tool use

## The core pattern

A tool is an application function described to a model or orchestrator through a name, description, and input schema. A model may request a tool call, but application code decides whether the tool is allowed, validates arguments, executes it, and returns structured results.

The secure flow is:

```text
model proposes call -> validate identity/domain/schema/budget -> execute adapter
-> capture result/evidence/error -> model explains -> verifier checks
```

Function calling is not permission. A valid JSON call can still be unauthorized or unsafe.

## How OpsGraph executes it

`backend/src/opsgraph/contracts/tools.py` defines `ToolDefinition`, `ToolCall`, and `ToolResult`. `tools/registry.py` stores handlers with allowed specialist agents and domains. A BankOps data analyst cannot invoke an AwardLens calculator because registry lookup includes tool name, domain, and agent authorization.

`orchestration/budget.py` caps each run at six tool calls. The graph reserves budget before invocation. This prevents accidental loops and makes cost/latency bounded.

Tools return structured data plus evidence. A rejected tool returns a typed status and error code rather than leaking an internal exception into the model context.

Examples:

- `search_policy`: retrieval over source documents.
- `query_cases`: guarded BankOps SQL.
- `query_award_findings`: guarded AwardLens SQL.
- `calculate_bankops_metrics`: deterministic operational calculation.
- `award_calculator`: immutable totals from the deterministic audit.
- `verify_evidence`: evidence verification support.

## Tool design rules

- Make names verb-oriented and specific.
- Use small schemas with constraints.
- Keep side effects explicit.
- Return stable machine-readable fields.
- Include evidence IDs and provenance.
- Use idempotency keys for retried writes.
- Separate read and write tools.
- Require human approval for high-impact actions.
- Apply timeouts, retries, circuit breakers, and rate limits at the adapter boundary.

## Do it yourself

Add a read-only tool that returns audit findings for one record ID. It must validate the ID, use a parameterized query, return at most one row, produce an evidence object, and have agent/domain allow-list tests.

## Interview checkpoints

- What is the difference between a tool schema and authorization?
- How should tool errors be represented to an agent?
- Why should tool results be structured?
- How do you make a write tool safe to retry?
- What stops an agent from calling tools forever?

# Module 8 - Agents, multi-agent systems, and LangGraph

## What an agent is

An agent combines a model with state, tools, and a control loop. Not every LLM application needs an agent. If the steps are known, a deterministic workflow is usually easier to test and operate. Use agentic decisions only where language interpretation or dynamic routing creates real value.

"Multi-agent" should not mean several chatbots talking indefinitely. A practical interpretation is bounded specialists with distinct responsibilities and tools, coordinated through typed state.

## OpsGraph specialists

- Supervisor: chooses RAG, SQL, hybrid, calculator, or unsupported.
- Policy research: uses document retrieval tools.
- Data analyst: uses guarded query tools.
- Domain calculation: uses deterministic calculators.
- Evidence verifier: checks citations and numeric facts.

These are roles in one graph, not independent services. That keeps the implementation simple while demonstrating separation of responsibility.

## LangGraph concepts in the code

`orchestration/state.py` defines shared state. Reducers append agents, evidence, calls, and results when parallel branches return.

`orchestration/graph.py` defines nodes and edges. `START` leads to the input guard and supervisor. Conditional edges route to a specialist. Hybrid routing returns both policy and data nodes, which LangGraph can execute in the next graph step. Results join before synthesis. Verification either ends, attempts one correction, or sends the request to manual review.

`orchestration/nodes.py` keeps one bounded responsibility per node. `service.py` creates the initial state and converts final graph state into the public `RunResult`.

## Why explicit graphs help

- You can see all valid transitions.
- Each node can be tested separately.
- Budgets and human-review points are visible.
- Parallel work is explicit.
- Trace events map to business steps.
- A failure does not require reading a long autonomous-agent transcript.

## When to use one agent instead

Prefer a single tool-using agent or fixed pipeline when all tasks share permissions, the workflow is short, and specialist separation adds no operational value. Multi-agent labels do not improve quality by themselves; they add coordination cost and more failure surfaces.

## Do it yourself

Draw the graph without looking at code. Then add a `risk_review` node after synthesis for answers with more than a configurable number of rows. Write tests for both branches and ensure the node cannot call additional tools.

## Interview checkpoints

- When is a graph better than a free-running agent loop?
- How does shared state merge after parallel branches?
- What are the failure modes of multi-agent systems?
- Where should human review enter this graph?
- How would you make a long-running graph resumable?

# Module 9 - End-to-end production AI application design

## The request boundary

FastAPI is the public boundary. `api/schemas.py` defines stable request/response objects. `api/routes/chat.py` converts a graph result into UI-facing evidence, SQL, trace, cost, and answer fields. The UI should not need to understand internal LangGraph state.

Production APIs need:

- Input size limits and validation.
- Authentication and authorization.
- Request IDs and trace IDs.
- Timeouts and cancellation.
- Stable error codes.
- Rate limits and abuse controls.
- Caching rules that include tenant, model, prompt, and data versions.
- Health endpoints for process and dependency readiness.
- Safe logging and redaction.

OpsGraph implements a compact subset suitable for a portfolio: bounded input, domain validation, a local admin token for ingestion/audits, TTL response caching, bounded run storage, structured errors, and live/ready health endpoints.

## UI integration

The React application has three workspaces: BankOps, AwardLens, and Evaluation. It calls typed API helpers in `frontend/src/api/client.ts`. TypeScript interfaces in `api/types.ts` mirror backend responses.

The UI exposes evidence, SQL, trace, cost, verification status, and limitations. This is intentional. An AI product should make uncertainty and provenance visible rather than displaying only polished prose.

Local-only upload controls are driven by runtime configuration. The public demo profile cannot create arbitrary audits. This is a simple example of feature exposure based on environment and risk.

## Caching AI responses

A safe cache key must include every input that can change the result: domain, normalized question, provider/model, prompt version, retrieval corpus version, relevant authorization scope, and tool/data version. OpsGraph's key demonstrates the pattern but is intentionally simpler than a multi-tenant production cache.

Never share a cached private answer across users merely because the question text is identical.

## Do it yourself

Add a response header containing the run ID. Show it in the UI's trace panel. Write an API test and a component test. Explain how a support engineer would use the ID during incident investigation.

## Interview checkpoints

- Where should API schemas differ from internal graph state?
- What belongs in an AI response cache key?
- Why expose evidence and limitations in the UI?
- What is the difference between liveness and readiness?
- How would you add authentication without coupling it to every graph node?

# Module 10 - Deterministic domain logic and human-review boundaries

## Why AwardLens is designed narrowly

Payroll calculations are high impact. A demo that pretends to support an entire industrial award would be misleading. AwardLens supports a declared subset: specified classifications, employment types, dates, day types, and ordinary shifts. Unsupported records receive no liability amount and are sent to manual review.

This is a general AI engineering principle: define the supported decision envelope and fail closed outside it.

## Rule integrity

`data/awardlens/rules/retail-level-1-2026.json` is a machine-readable ruleset. `source-manifest.json` records source IDs, review status, and a SHA-256 hash. `domains/awardlens/rules.py` verifies canonical text before loading the model. Canonical newline handling keeps integrity stable across Windows and Linux checkouts.

The hash proves the file matches the reviewed artifact; it does not prove the rule is legally correct. Human source review, effective dates, approvals, and change management remain necessary.

## Calculation

`calculator.py` validates scope before calculating. It rejects unknown classifications, unsupported employment types, overnight shifts, shifts crossing multiplier boundaries, non-positive durations, and potential overtime. Supported shifts use integer minutes, integer base-rate cents, `Decimal` multipliers, and explicit half-up rounding.

`audit.py` aggregates only supported findings. A manual-review record has `expected_gross_cents`, `variance_cents`, and `liability_cents` set to null. That prevents an uncertain result from contributing to a total.

## Explanation and report safety

The explanation service requires the model to preserve deterministic facts. Reports escape all user-controlled values and contain no active scripts or remote resources. CSV parsing rejects spreadsheet-formula prefixes and enforces a strict schema and size limits.

The system calls differences "potential" and states that the demo is not legal or payroll advice. Language is part of the safety design.

## Generalize the pattern

Use the same structure for tax estimates, insurance eligibility, credit operations, medical triage, or regulatory checks:

1. Declare supported inputs.
2. Version rules and sources.
3. Validate before calculation.
4. Make the calculation deterministic.
5. Preserve exact facts through explanation.
6. Produce no automated conclusion outside scope.
7. Audit every rule and code change.

## Do it yourself

Add one supported Sunday casual shift and one unsupported overnight shift. Prove with property tests that liability is never negative and unsupported findings never contain a liability.

## Interview checkpoints

- What does a file hash prove, and what does it not prove?
- Why return null rather than zero for unsupported liability?
- Where should rounding happen?
- How would you manage effective-dated rule changes?
- How do you communicate the boundary between an explanation and legal advice?

# Module 11 - Cloud model providers: Ollama and Amazon Bedrock

## Provider abstraction

The graph depends on `AgentModel`, which exposes routing, tool selection, and synthesis. `providers/factory.py` selects the implementation from validated settings.

The default fake provider is deterministic and free. `providers/ollama.py` calls the local `/api/chat` endpoint with streaming disabled, temperature zero, and the Pydantic JSON schema as the requested output format. `providers/bedrock.py` uses the Bedrock Runtime Converse API and the normal AWS identity chain.

The adapters inherit `StructuredAgentModel`. Tool selection remains deterministic and allow-listed; the provider handles semantic routing and grounded synthesis. This keeps the security boundary in application code.

## Running Ollama

After installing Ollama and a suitable local model:

```powershell
$env:OPSGRAPH_MODEL_PROVIDER="ollama"
$env:OPSGRAPH_OLLAMA_BASE_URL="http://localhost:11434"
$env:OPSGRAPH_OLLAMA_MODEL="qwen3:4b"
uv run uvicorn opsgraph.api.app:app --host 127.0.0.1 --port 8000
```

Local models avoid per-token charges and can keep data on the machine, but require RAM/VRAM, may be slower, and may have weaker structured-output reliability. Measure them rather than assuming "local" means better.

## Running Bedrock

Install the AWS extra, configure a normal AWS profile or workload identity, request model access where required, and set a model ID:

```powershell
uv sync --extra aws
$env:OPSGRAPH_MODEL_PROVIDER="bedrock"
$env:OPSGRAPH_AWS_REGION="ap-southeast-2"
$env:OPSGRAPH_BEDROCK_MODEL_ID="your-enabled-model-or-inference-profile"
uv run uvicorn opsgraph.api.app:app --host 0.0.0.0 --port 8000
```

Never place long-lived AWS keys in source control. Use the SDK credential chain, IAM roles, least privilege, secret managers, private networking where required, and model invocation logs that comply with data policy.

## Production provider concerns

- Timeouts and bounded retries with jitter.
- Rate and concurrency limits.
- Model/version pinning where possible.
- Regional availability and data residency.
- Provider-specific structured-output support.
- Token usage and price-table versioning.
- Circuit breakers and fallback policy.
- Evaluation before changing a model.
- Explicit behavior when the provider is unavailable.

OpsGraph does not silently fall back from a paid model to a different model because that could change behavior without the caller knowing. A production fallback should be explicit in the response and trace.

## Do it yourself

Run the same 40 cases with a local model adapter. Repeat the suite five times. Report pass rate by category, p50/p95 latency, invalid-schema rate, and any changed numeric fact. Keep live-provider reports separate from the deterministic baseline.

## Interview checkpoints

- How does the provider abstraction reduce lock-in?
- What remains provider-specific even behind an interface?
- How should AWS credentials be supplied in production?
- When is local inference a good choice?
- What must be evaluated before a model migration?

# Module 12 - Observability, cost, and reliability

## Observability for AI systems

Traditional monitoring still matters: request rate, errors, latency, CPU, memory, queue depth, and dependency health. AI systems add model, retrieval, tool, evidence, safety, and cost dimensions.

Useful trace spans include:

- Request and workflow.
- Route decision.
- Retrieval and number of hits.
- SQL validation and execution.
- Each tool call.
- Model synthesis.
- Verification and correction.
- Human-review transition.

`observability/tracing.py` configures OpenTelemetry and creates named spans. The API can export through an OpenTelemetry Collector to Jaeger. Docker Compose keeps this under an optional profile so the application remains cheap to run.

## What to measure

- End-to-end latency and per-node latency.
- Route distribution and route accuracy on labeled data.
- Retrieval hit rate and empty retrievals.
- SQL rejection rate and execution time.
- Tool error and timeout rate.
- Model input/output tokens.
- Estimated cost by provider, model, domain, and customer.
- Verification failures and corrections.
- Manual-review rate.
- Cache hit rate.
- Evaluation regressions by release.

## Cost engineering

`observability/costs.py` uses `Decimal` and a versioned price table. Unknown prices do not masquerade as free when usage exists. The deterministic and local providers have zero marginal API cost. Live Bedrock pricing should be configured from a reviewed source and tied to model/version.

Cost reduction should preserve quality. Common levers are better retrieval, smaller context, caching, smaller routing models, request batching, shorter outputs, and deterministic code for calculations. Measure cost per successful task, not only cost per token.

## Privacy and trace safety

`redaction.py` removes secret-like values before export. Security tests verify that credentials do not enter span attributes. Prefer stable hashes or IDs when correlation is necessary. Do not store raw prompts indefinitely without a retention and access policy.

## Reliability patterns

- Timeouts for every external call.
- Bounded retries only for transient failures.
- Idempotency for repeatable writes.
- Bulkheads between providers or tenants.
- Circuit breakers for unhealthy dependencies.
- Backpressure when queues grow.
- Manual review when safety invariants fail.
- Run IDs that connect user reports with traces.

## Do it yourself

Add a histogram or recorded summary for retrieval latency and a counter for manual-review outcomes. Generate a small load test and explain what you would alert on. Avoid alerting on every single rejected unsupported request; alert on unexpected changes in rate.

## Interview checkpoints

- What makes AI observability different from normal API monitoring?
- Which fields should never enter traces?
- How do you estimate cost when prices change?
- What is the difference between a retry and a fallback?
- Which signals would reveal a retrieval regression?

# Module 13 - Evaluation, benchmarking, and model documentation

## Evaluation is a dataset plus a judge

An evaluation case needs an input, expected behavior, and measurable result. The judge can be deterministic code, a human rubric, a model, or a combination. Use deterministic checks whenever possible.

OpsGraph has 40 checked-in cases:

- 20 BankOps cases across RAG, SQL, hybrid, calculation, and abstention.
- 8 adversarial SQL/safety cases.
- 12 AwardLens cases across RAG, SQL, hybrid, calculation, and abstention.

`evaluation/cases.py` validates each case. `runner.py` executes the graph and records observed route, status, evidence, SQL behavior, numeric preservation, latency, and cost. `metrics.py` calculates aggregate metrics and release-blocking failures. `report.py` writes JSON and Markdown plus a SHA-256 checksum.

## Metrics in the project

- Route accuracy.
- Status accuracy.
- Retrieval hit rate.
- Citation validity.
- SQL safety.
- SQL execution accuracy.
- Numeric preservation.
- Abstention accuracy.
- Mean latency.
- Estimated cost.

Release gates block unknown citations, unsafe SQL execution, changed numeric values, unsupported AwardLens liability, and leaked secrets.

## Building a good dataset

Start from actual tasks and failures. Include straightforward examples, paraphrases, ambiguous inputs, boundary values, attacks, empty data, provider failures, and out-of-domain requests. Keep a held-out set so prompt tuning does not overfit every visible case.

Version cases, prompts, models, corpora, and judge logic. A score without those versions is difficult to reproduce.

## Model-based judging

An LLM judge can assess qualities that deterministic code cannot easily capture, such as completeness or tone. It also introduces bias and variance. Use a clear rubric, blind comparisons where possible, repeated samples, calibration against human labels, and deterministic release gates for hard safety invariants.

## Benchmarking correctly

Report distributions, not only averages. Latency needs p50, p95, and p99. Live model quality needs repeated trials and confidence intervals. Separate cold starts from warm requests. Compare systems on the same dataset and environment.

## Documentation

A model or system card should record intended use, unsupported use, data sources, providers/models, prompts, evaluation dataset, metrics, safety controls, privacy, cost assumptions, known limitations, and change history.

## Do it yourself

Create ten new cases from failures you cause deliberately. Add one retrieval miss, one malformed provider output, one SQL ambiguity, one prompt-injection document, one timeout, and one unsupported AwardLens boundary. Explain why each judge is deterministic or probabilistic.

## Interview checkpoints

- What makes an evaluation case useful?
- When is an LLM judge appropriate?
- Why keep a held-out set?
- What should block a release regardless of aggregate score?
- How do you compare two models fairly?

# Module 14 - Testing and security for AI applications

## Test layers in OpsGraph

- Unit tests: pure route logic, chunking, calculations, SQL guards, cost math, and provider parsing.
- Property tests: invariants over many generated AwardLens inputs.
- Integration tests: retrieval plus SQL plus graph behavior.
- API tests: profiles, authentication, upload limits, and response contracts.
- Security tests: SQL attacks, trace secret leakage, report escaping, and unsupported conclusions.
- Component tests: React behavior with mocked API responses.
- End-to-end tests: browser interaction across React and FastAPI on desktop and mobile.
- Evaluation tests: task-level quality and release gates.

These layers answer different questions. A passing unit test does not prove the browser works; a passing end-to-end test does not precisely identify which calculation broke.

## AI-specific threats

- Prompt injection from user input or retrieved documents.
- Tool misuse and excessive agency.
- Sensitive data leakage in prompts, outputs, or traces.
- Cross-tenant retrieval.
- Insecure output rendering.
- Model denial of service through huge contexts or loops.
- Poisoned documents or evaluation data.
- Supply-chain risk in models and dependencies.
- Overreliance on generated explanations.

## Defenses in the project

Input size limits, tool/domain allow-lists, a six-call budget, guarded read-only SQL, strict CSV parsing, HTML escaping, synthetic data, local-only mutation routes, secret redaction, verified citations, numeric preservation, and manual-review outcomes.

This remains an educational prototype. Production would also require real identity, authorization, tenant isolation, secrets management, network controls, dependency scanning, incident response, data retention, and independent review.

## Do it yourself

Threat-model the upload-to-report flow. Identify trust boundaries, assets, attackers, abuse cases, and mitigations. Add one failing security test before implementing each mitigation.

## Interview checkpoints

- How is prompt injection different from SQL injection?
- Why is output escaping still necessary when data is synthetic?
- What does a tool-call budget protect?
- Why are property tests useful for financial calculations?
- Which security controls belong outside the model?

# Module 15 - CI/CD, containers, and release automation

## Continuous integration

`.github/workflows/ci.yml` runs three jobs:

1. Backend: install locked dependencies, run all Python tests, generate the deterministic evaluation report, verify its checksum and release gates, and upload it as an artifact.
2. Frontend: install from the lockfile, run component tests, type-check, and build the production bundle.
3. Containers: build separate API and web images.

CI answers: "Can this exact commit pass automated quality gates in a clean environment?"

## Continuous delivery and deployment

Continuous delivery means every accepted change is deployable. Continuous deployment means successful changes are automatically released. Regulated or high-impact AI systems often use continuous delivery with an approval gate for production.

A safe pipeline promotes the same immutable artifact through environments. It does not rebuild different code for production. Configuration and secrets enter at runtime.

## Containers

`backend/Dockerfile` installs locked Python dependencies and runs Uvicorn. `frontend/Dockerfile` builds the React bundle and serves it through Nginx, which proxies API requests. `docker-compose.yml` runs the free fake-provider application. PostgreSQL and observability services are optional profiles.

Useful commands:

```powershell
docker compose config
docker compose up --build api web
# Open http://localhost:8080

docker compose --profile observability up --build
# Jaeger UI: http://localhost:16686
```

## Release strategy

For a real service, use environment-specific configuration, database migrations, canary or blue/green deployment, health checks, automatic rollback, audit logs, and a model/prompt evaluation gate. Monitor quality and cost after release because offline tests cannot represent every production input.

## Do it yourself

Create a feature branch, intentionally break numeric preservation, and observe the evaluation test fail. Fix it, build both containers, and write a short release note containing changed behavior, evaluation result, known risk, and rollback plan.

## Interview checkpoints

- What does a lockfile provide?
- What is the difference between CI, continuous delivery, and continuous deployment?
- Why promote the same image across environments?
- Where should secrets enter a deployment?
- What AI-specific gates belong before production?

# Module 16 - Git, Agile delivery, and AI-assisted development

## Git workflow

A professional change is small enough to review and includes code, tests, documentation, and migration or operational notes where needed.

Typical flow:

```text
issue -> feature branch -> failing test -> implementation -> local verification
-> focused commit -> pull request -> CI -> review -> merge -> deploy -> monitor
```

Useful practices:

- Write meaningful commit messages that describe behavior.
- Do not mix unrelated changes.
- Rebase or merge according to team policy; understand both.
- Never commit credentials, generated secrets, or private data.
- Review the diff before committing.
- Keep main releasable.

## Agile/Scrum in an AI project

A user story needs observable acceptance criteria. "Improve the chatbot" is not testable. "For the 20 labeled policy questions, retrieval recall@3 is at least 0.90 and no answer cites an unknown evidence ID" is testable.

AI spikes are appropriate when uncertainty is high. A spike should have a timebox, experiment, dataset, result, and decision. It should not become unreviewed production code.

Definition of done can include:

- Code and tests reviewed.
- Evaluation dataset updated.
- Safety gates pass.
- Observability added.
- Cost impact measured.
- Documentation and runbook updated.
- Product owner accepts behavior.

## AI-assisted coding tools

Copilot, Codex, Claude Code, Cursor, and similar tools can accelerate exploration, tests, refactors, and documentation. The engineer still owns correctness.

Safe usage:

- Give the tool the smallest necessary context.
- Do not paste secrets or restricted customer data.
- Ask for tests and failure analysis, not only code generation.
- Review every diff and dependency.
- Verify API details against primary documentation.
- Run the actual tests and application.
- Preserve attribution and license requirements.
- State honestly which work was assisted.

## Do it yourself

Write a Jira-style story for adding a new BankOps intent. Include business value, non-goals, acceptance criteria, security considerations, evaluation cases, observability, and rollback. Then implement it in a branch with three focused commits.

## Interview checkpoints

- What makes an AI user story testable?
- How do you manage exploratory model work inside a sprint?
- How do you review AI-generated code?
- What belongs in a pull request description for an AI behavior change?
- How do you keep experiments reproducible?

# Module 17 - Complete BankOps request walkthrough

Use this question:

```text
Which open complaint cases are late and what policy applies?
```

1. `BankOpsWorkspace.tsx` sends `{domain: "bankops", question: ...}` to `/api/v1/chat`.
2. FastAPI validates the request and calls `OpsGraphService.run`.
3. The input guard checks length and prohibited mutation/decision language.
4. The supervisor sees both data language ("which", "late") and policy language ("policy") and chooses `hybrid`.
5. LangGraph routes to policy research and data analyst branches.
6. Policy research receives only the BankOps `search_policy` tool. Retrieval embeds the question, searches FAISS, and returns document evidence.
7. Data analyst receives only `query_cases`. The tool selects a bounded query shape for complaint cases.
8. SQLGlot validates statement type, tables, columns, functions, and syntax. The executor adds `LIMIT 200` and runs read-only SQLite.
9. Both branches append calls, results, and evidence into graph state.
10. Synthesis receives the question, document chunks, SQL evidence, and structured results.
11. The draft names returned cases and policy evidence, cites supplied IDs, and preserves numeric facts.
12. The verifier ensures citations exist in this run/domain and numeric facts equal tool outputs.
13. The service builds a trace with route, agents, tool calls, status, provider, model, latency context, and estimated cost.
14. The API returns answer, table data, SQL, evidence, limitations, and trace.
15. React renders the answer and makes evidence and SQL inspectable.

What is probabilistic? With a live provider, route wording and synthesis. What is deterministic? Tool authorization, SQL validation/execution, data, evidence IDs, numeric checks, budgets, and response schema.

## Debugging order

If the answer is wrong, inspect in this order:

1. Was the route correct?
2. Were the expected specialists called?
3. Were the right tools available?
4. Was retrieval relevant?
5. Was SQL normalized and safe?
6. Did tool results contain the correct facts?
7. Did synthesis cite and copy those facts?
8. Did verification accept something it should reject?
9. Did the UI render the response correctly?

This order localizes the failure instead of blaming "the model."

# Module 18 - Complete AwardLens request walkthrough

Use the demo flow and question:

```text
How many audit findings need manual review and what policy applies?
```

1. AwardLens loads `demo-payroll.csv` through a strict parser.
2. The rule loader verifies the reviewed ruleset hash and metadata.
3. Each shift is checked against the supported envelope.
4. Supported shifts receive deterministic calculation lines.
5. Unsupported shifts receive `manual_review` with null expected, variance, and liability values.
6. The audit aggregates supported totals and records limitations.
7. Findings are copied into a temporary read-only SQLite database for analytical questions.
8. The question routes to hybrid because it combines a count with policy.
9. The data specialist runs a guarded count query filtered to manual review.
10. The policy specialist retrieves the source-bound AwardLens summary.
11. Synthesis explains the count and policy evidence.
12. Verification checks `finding_count` and citations.
13. The UI shows totals, findings, manual-review boundaries, the generated SQL, evidence, trace, and a sanitized HTML report.

The important distinction is that RAG explains the rule and SQL analyzes findings, but neither calculates pay. Calculation remains in `calculator.py`.

## Debugging order

1. Confirm rule version and verification status.
2. Confirm the record is inside the supported envelope.
3. Inspect calculation lines and rounding.
4. Confirm unsupported findings have no liability.
5. Inspect the findings database row.
6. Inspect route, SQL, retrieved evidence, and numeric facts.
7. Confirm report escaping and limitations.

# Module 19 - System design and interview preparation

## A strong architecture explanation

Use problem, constraints, design, trade-offs, and evidence.

Example:

"I built an evidence-first operations copilot with two domains. The main constraint was that language models could interpret questions but could not own exact calculations, database permissions, or citations. I used a typed LangGraph workflow with a supervisor and bounded specialists. Policy questions use RAG over source-labeled chunks; data questions use AST-validated read-only SQL; payroll and SLA arithmetic use deterministic Python tools. A verifier checks citation IDs and numeric facts. The free fake provider makes CI deterministic, while Ollama and Bedrock adapters demonstrate provider switching. The suite currently executes 40 cases with release gates for unsafe SQL, unknown citations, changed numbers, unsupported liability, and secret leakage. The main limitation is that the domain and datasets are deliberately narrow and synthetic."

## Common senior-level questions

### Why not let the model do everything?

Because exact rules, permissions, and side effects are easier to test and control in ordinary code. The model is used where language interpretation adds value.

### Why LangGraph?

The workflow has conditional and parallel branches, shared typed state, one correction attempt, and human-review exits. An explicit graph makes these transitions testable and observable. A simple fixed pipeline would also be valid for a smaller scope.

### How would this scale?

Move durable data to managed PostgreSQL/pgvector, use a queue for long work, persist graph checkpoints, isolate tenants, scale stateless API containers, use provider concurrency controls, and build retrieval/evaluation datasets from real authorized usage. Scale the bottleneck demonstrated by telemetry, not every component in advance.

### How would you deploy safely?

Build immutable containers in CI, run tests and evaluation gates, scan dependencies/images, deploy to staging, run smoke/live-provider evaluations, use an approval gate, release canary traffic, monitor quality/latency/cost, and roll back the image or provider configuration if thresholds regress.

### What would you improve next?

Real authentication and tenancy, durable run storage, labeled retrieval relevance, live-provider repeated evaluation, token accounting, provider timeouts/retries, checkpointed graphs, and a reviewed process for rule updates.

## Honesty checklist for your resume and interview

- Say "built" only for code you can run and explain.
- Say "integrated" when the adapter and end-to-end path work.
- Say "evaluated" only with a defined dataset and metrics.
- Distinguish synthetic demonstrations from production customer data.
- Do not claim legal coverage beyond the supported AwardLens subset.
- Do not claim a cloud deployment if you only created a deployable adapter and container. Say "implemented Bedrock integration and container-ready deployment" until you actually deploy it.
- Be ready to open the exact file for every resume bullet.

# Module 20 - Hands-on capstone plan

Complete these labs in order. Keep notes and commits as evidence of learning.

## Lab 1 - Run and trace

Run backend, frontend, and the deterministic evaluation. Use the UI to inspect one RAG, SQL, hybrid, calculator, and unsupported request. Write a one-page explanation of each trace.

## Lab 2 - Retrieval experiment

Add a document and labeled questions. Measure retrieval before and after one change. Report both improvement and regressions.

## Lab 3 - SQL intent

Add one bounded analytical intent with semantic-schema, guard, tool, API, and adversarial tests.

## Lab 4 - Tool and agent boundary

Add one read-only tool, authorize it for exactly one specialist and domain, enforce a budget, and display its trace.

## Lab 5 - AwardLens rule extension

Extend one clearly sourced and supported case. Version the rule, update its hash, add boundary/property tests, and document limitations.

## Lab 6 - Live local model

Use Ollama. Run repeated evaluations, record invalid outputs, and improve only the prompt/provider adapter. Do not weaken deterministic safety checks to make the model pass.

## Lab 7 - Observability

Start the optional OpenTelemetry profile. Trace a successful hybrid request and a manual-review request. Identify the slowest span and explain what an alert would look like.

## Lab 8 - Delivery

Push a branch to GitHub, observe CI, review the evaluation artifact, build containers, and write a rollback plan. If you choose Bedrock, set a strict personal budget and invoke only a small test set.

# Quick-reference checklists

## RAG checklist

- Sources are authorized, versioned, and metadata-rich.
- Chunking is evaluated on real questions.
- Embedding and distance configuration agree.
- Tenant/domain filters run before search.
- Retrieved text is treated as untrusted data.
- Citations refer to current-run evidence.
- Retrieval and answer quality are measured separately.

## Text-to-SQL checklist

- Read-only identity/database.
- Narrow semantic schema.
- AST parse and allow-list.
- One statement; no DDL/DML/comments.
- Bounded rows, time, functions, and joins.
- Parameterized values where applicable.
- Query/result included as evidence.
- Adversarial evaluation blocks release.

## Agent checklist

- Agentic routing solves a real uncertainty.
- State is typed.
- Tools are allow-listed by role and domain.
- Calls, loops, time, and cost are bounded.
- Side effects require explicit authorization.
- Human review is a first-class outcome.
- Every transition is observable and tested.

## Production checklist

- Authentication, authorization, and tenant isolation.
- Secrets from managed runtime identity/secret storage.
- Timeouts, retries, backpressure, and circuit breakers.
- Safe logs, traces, and retention.
- Versioned prompts, models, rules, data, and evaluations.
- CI quality and safety gates.
- Immutable artifacts and rollback.
- Post-release quality, latency, and cost monitoring.

# Command reference

Backend:

```powershell
cd projects\opsgraph-copilot\backend
uv sync --extra aws
uv run pytest -q
uv run python -m opsgraph.evaluation.runner --provider fake --output ..\evaluation\reports\local
uv run uvicorn opsgraph.api.app:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd projects\opsgraph-copilot\frontend
npm.cmd ci
npm.cmd test -- --run
npm.cmd run build
npm.cmd run test:e2e
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Containers:

```powershell
cd projects\opsgraph-copilot
docker compose config
docker compose up --build api web
docker compose --profile observability up --build
```

Artifact verification:

```powershell
python scripts\verify_artifacts.py --report evaluation\reports\deterministic\latest.json
```

# Glossary

- Agent: a model-guided process with state and tools.
- Abstention: declining to automate when the request or evidence is unsupported.
- AST: parsed tree representation of code such as SQL.
- Chunk: retrievable segment of a source document.
- Citation grounding: linking a claim to evidence that supports it.
- Context engineering: selection and organization of information supplied to a model.
- Embedding: vector representation used for similarity comparison.
- Evaluation: systematic measurement on defined cases and metrics.
- Function calling: structured model request to invoke an application tool.
- Hallucination: unsupported generated content.
- Human in the loop: an explicit point where a person reviews or decides.
- Idempotency: repeated execution has the same intended effect as one execution.
- LLM: large language model.
- Multi-agent: coordinated specialist roles, usually with separate tools or responsibilities.
- Prompt injection: untrusted text attempting to alter model instructions or tool behavior.
- RAG: retrieval-augmented generation.
- Reranker: model or algorithm that reorders retrieved candidates.
- Structured output: model output constrained and validated against a schema.
- Tool: application function an agent can request under explicit controls.
- Trace: timed record of operations within a request.
- Vector database: system that stores and searches embeddings plus metadata.

# Further reading - primary sources

- LangGraph overview and Graph API: https://docs.langchain.com/oss/python/langgraph/overview and https://docs.langchain.com/oss/python/langgraph/graph-api
- FAISS project and wiki: https://github.com/facebookresearch/faiss and https://github.com/facebookresearch/faiss/wiki
- OpenTelemetry documentation: https://opentelemetry.io/docs/
- Amazon Bedrock Converse API: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
- Ollama chat API and structured outputs: https://docs.ollama.com/api/chat and https://docs.ollama.com/capabilities/structured-outputs
- GitHub Actions build and test documentation: https://docs.github.com/en/actions/tutorials/build-and-test-code
- Fair Work Commission, General Retail Industry Award 2020: https://awards.fairwork.gov.au/MA000004.html
- Fair Work Ombudsman pay guide entry point: https://calculate.fairwork.gov.au/Download/AwardSummary?awardCode=ma000004&fileType=pdf

# Final self-assessment

You are ready to discuss this project when you can do all of the following without memorized buzzwords:

- Draw the request flow and explain every trust boundary.
- Explain which parts are probabilistic and deterministic.
- Trace a number and citation from source to UI.
- Show how SQL is prevented from mutating data.
- Explain why unsupported AwardLens records have null liability.
- Add a tool without bypassing authorization or budget controls.
- Define an evaluation case and a release gate.
- Find a failed request in traces without exposing secrets.
- Compare FAISS, pgvector, and a managed vector store using requirements.
- Explain provider switching, cloud credentials, cost, and fallback policy.
- Build and test the containers through CI.
- State the project's limitations honestly and propose the next production improvements.

The final test is not whether you can repeat the architecture. It is whether you can change it safely, measure the result, and defend the trade-offs.
