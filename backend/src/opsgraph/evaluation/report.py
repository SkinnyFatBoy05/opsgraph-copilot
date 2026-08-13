"""Hash-verified JSON and human-readable Markdown evaluation reports."""

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from opsgraph.evaluation.cases import EvaluationSummary


@dataclass(frozen=True)
class ReportArtifacts:
    json_path: Path
    markdown_path: Path
    hash_path: Path


def write_reports(summary: EvaluationSummary, output_dir: Path) -> ReportArtifacts:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "latest.json"
    markdown_path = output_dir / "latest.md"
    hash_path = output_dir / "latest.json.sha256"
    payload = json.dumps(
        summary.model_dump(mode="json"),
        indent=2,
        sort_keys=True,
    ) + "\n"
    json_path.write_bytes(payload.encode("utf-8"))
    hash_path.write_bytes(
        (sha256(payload.encode("utf-8")).hexdigest() + "\n").encode("utf-8")
    )
    markdown_path.write_text(_markdown(summary), encoding="utf-8")
    return ReportArtifacts(json_path, markdown_path, hash_path)


def verify_report(path: Path) -> EvaluationSummary:
    payload = path.read_text(encoding="utf-8")
    expected_hash = path.with_name(f"{path.name}.sha256").read_text(encoding="utf-8").strip()
    if sha256(payload.encode("utf-8")).hexdigest() != expected_hash:
        raise ValueError("evaluation report hash mismatch")
    return EvaluationSummary.model_validate_json(payload)


def _markdown(summary: EvaluationSummary) -> str:
    lines = [
        "# OpsGraph deterministic evaluation",
        "",
        f"- Provider: `{summary.provider}`",
        f"- Deterministic: `{str(summary.deterministic).lower()}`",
        f"- Generated: `{summary.generated_at}`",
        f"- Cases: `{summary.passed_cases}/{summary.total_cases}` passed",
        f"- Estimated model cost: `${summary.estimated_cost_usd}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {name.replace('_', ' ').title()} | {value:.4f} |"
        for name, value in sorted(summary.metrics.items())
    )
    lines.extend(["", "## Release failures", ""])
    if summary.release_failures:
        lines.extend(f"- `{failure}`" for failure in summary.release_failures)
    else:
        lines.append("None.")
    lines.extend(["", "This report uses synthetic data and the deterministic fake provider.", ""])
    return "\n".join(lines)
