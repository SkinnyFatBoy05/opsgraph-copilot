from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_minimal_delivery_artifacts_cover_build_test_and_evaluation() -> None:
    required = (
        "backend/Dockerfile",
        "frontend/Dockerfile",
        "frontend/nginx.conf",
        ".github/workflows/ci.yml",
        "scripts/verify_artifacts.py",
    )
    assert all((PROJECT_ROOT / relative).is_file() for relative in required)

    workflow = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "uv run pytest" in workflow
    assert "npm run build" in workflow
    assert "opsgraph.evaluation.runner" in workflow
    assert "playwright install" in workflow
    assert "OPSGRAPH_TEST_POSTGRES_URL" in workflow
    assert "docker compose up -d --wait api web" in workflow
    assert "docker compose build api web" in workflow


def test_compose_runs_the_api_and_web_without_paid_services() -> None:
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "api:" in compose
    assert "web:" in compose
    assert "OPSGRAPH_MODEL_PROVIDER: fake" in compose
    assert "8080:80" in compose


def test_backend_image_packages_the_demo_evaluation_report() -> None:
    dockerfile = (PROJECT_ROOT / "backend/Dockerfile").read_text(encoding="utf-8")
    expected_copy = (
        "COPY evaluation/reports/deterministic "
        "/app/evaluation/reports/deterministic"
    )

    assert expected_copy in dockerfile
    assert (
        PROJECT_ROOT / "evaluation/reports/deterministic/latest.json"
    ).is_file()


def test_optional_compose_profiles_are_separate_and_documented() -> None:
    compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert 'profiles: ["data"]' in compose
    assert 'profiles: ["observability"]' in compose
    assert "OPSGRAPH_POSTGRES_PORT:-55432" in compose
    assert "docker compose --profile data up -d postgres" in readme
    assert "docker compose --profile observability up --build" in readme
