"""AwardLens domain adapter, demo data, and source-bound explanation service."""

import json
import sqlite3
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from opsgraph.analytics_sql.contracts import SemanticSchema
from opsgraph.contracts.evidence import EvidenceRef
from opsgraph.contracts.runs import DraftAnswer, SynthesisRequest
from opsgraph.contracts.tools import ToolResult
from opsgraph.domains.awardlens.audit import run_audit
from opsgraph.domains.awardlens.csv_ingestion import parse_payroll_csv
from opsgraph.domains.awardlens.models import AuditFinding, AuditRun, AwardRuleSet
from opsgraph.domains.awardlens.rules import load_rule_set
from opsgraph.providers.base import AgentModel

AWARDLENS_FINDINGS_SCHEMA = SemanticSchema(
    name="awardlens",
    tables={
        "audit_findings": (
            "record_id",
            "status",
            "expected_gross_cents",
            "paid_gross_cents",
            "variance_cents",
            "liability_cents",
            "rule_version",
        )
    },
    descriptions={
        "audit_findings": "Synthetic deterministic AwardLens results; null amounts require manual review."
    },
)


@dataclass(frozen=True)
class AwardLensDomain:
    name: str = "awardlens"

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[5]

    @property
    def documents_path(self) -> Path:
        return self.project_root / "data" / "awardlens" / "documents"

    @property
    def rules_path(self) -> Path:
        return self.project_root / "data" / "awardlens" / "rules"

    @property
    def demo_csv_path(self) -> Path:
        return self.project_root / "data" / "awardlens" / "seed" / "demo-payroll.csv"

    @property
    def schema(self) -> str:
        return "award_findings read-only semantic schema"

    def load_rules(self) -> AwardRuleSet:
        return load_rule_set(
            self.rules_path / "retail-level-1-2026.json",
            self.rules_path / "source-manifest.json",
        )

    def demo_audit(self) -> AuditRun:
        return run_audit(parse_payroll_csv(self.demo_csv_path.read_bytes()), self.load_rules())


class AwardLensExplanationService:
    """Let the model explain an immutable finding without changing its numbers."""

    def __init__(self, model: AgentModel) -> None:
        self.model = model

    async def explain(self, finding: AuditFinding) -> DraftAnswer:
        numeric_facts = {
            "expected_gross_cents": finding.expected_gross_cents,
            "paid_gross_cents": finding.paid_gross_cents,
            "liability_cents": finding.liability_cents,
        }
        numeric_facts = {key: value for key, value in numeric_facts.items() if value is not None}
        text = json.dumps(finding.model_dump(mode="json"), sort_keys=True)
        evidence = EvidenceRef(
            id=f"award-finding-{sha256(text.encode()).hexdigest()[:20]}",
            domain="awardlens",
            kind="calculation",
            title=f"Deterministic finding {finding.record_id}",
            text=text,
            metadata={"rule_version": finding.rule_version},
        )
        tool_result = ToolResult(
            call_id="explain-finding",
            name="award_calculator",
            status="succeeded",
            data={"numeric_facts": numeric_facts},
            evidence=(evidence,),
        )
        draft = await self.model.synthesize(
            SynthesisRequest(
                question="Explain this deterministic AwardLens finding without changing amounts.",
                domain="awardlens",
                evidence=(evidence,),
                tool_results=(tool_result,),
            )
        )
        if draft.numeric_facts != numeric_facts:
            raise ValueError("model explanation changed deterministic numeric facts")
        return draft


def create_findings_database(audit: AuditRun, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE audit_findings (
                record_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                expected_gross_cents INTEGER,
                paid_gross_cents INTEGER NOT NULL,
                variance_cents INTEGER,
                liability_cents INTEGER,
                rule_version TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO audit_findings VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.record_id,
                    item.status,
                    item.expected_gross_cents,
                    item.paid_gross_cents,
                    item.variance_cents,
                    item.liability_cents,
                    item.rule_version,
                )
                for item in audit.findings
            ],
        )
    return path
