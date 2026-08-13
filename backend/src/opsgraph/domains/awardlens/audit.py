"""Deterministic AwardLens batch auditing."""

import json
from datetime import UTC, datetime
from hashlib import sha256

from opsgraph.domains.awardlens.calculator import calculate_shift
from opsgraph.domains.awardlens.models import AuditRun, AwardRuleSet, PayrollRecord
from opsgraph.observability.tracing import traced


def run_audit(records: tuple[PayrollRecord, ...], rules: AwardRuleSet) -> AuditRun:
    canonical = json.dumps(
        [record.model_dump(mode="json") for record in records],
        sort_keys=True,
        separators=(",", ":"),
    )
    input_hash = sha256(canonical.encode("utf-8")).hexdigest()
    with traced(
        "opsgraph.audit",
        {"domain": "awardlens", "record_count": len(records), "input_hash": input_hash},
    ):
        findings = tuple(calculate_shift(record, rules) for record in records)
    calculated = tuple(item for item in findings if item.status == "calculated")
    return AuditRun(
        audit_id=f"audit-{input_hash[:16]}",
        created_at=datetime.now(UTC),
        rule_version=rules.version,
        verification_status=rules.verification_status,
        source_ids=rules.source_ids,
        record_count=len(records),
        calculated_count=len(calculated),
        manual_review_count=len(findings) - len(calculated),
        total_expected_gross_cents=sum(item.expected_gross_cents or 0 for item in calculated),
        total_paid_gross_cents=sum(item.paid_gross_cents for item in calculated),
        total_liability_cents=sum(item.liability_cents or 0 for item in calculated),
        input_sha256=input_hash,
        findings=findings,
        limitations=(
            "Synthetic demonstration only; not legal or payroll advice.",
            "Only adult full-time, part-time, and casual Retail Employee Level 1 ordinary shifts are calculated.",
            "Excluded or ambiguous records are sent to manual review without a liability amount.",
        ),
    )
