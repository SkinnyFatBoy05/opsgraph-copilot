# OpsGraph backend

FastAPI, LangGraph, retrieval, guarded SQL, tools, providers, observability, deterministic AwardLens logic, and evaluation live in `src/opsgraph`.

```powershell
uv sync
uv run pytest -q
uv run uvicorn opsgraph.api.app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/docs>. Use the repository root README for the full application, optional providers, Docker profiles, and study path.
