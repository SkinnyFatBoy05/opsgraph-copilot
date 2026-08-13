import sqlite3
from pathlib import Path

from opsgraph.domains.bankops.seed import build_seed_rows, seed_bankops


def test_seed_is_reproducible() -> None:
    first = build_seed_rows(seed=20260807)
    second = build_seed_rows(seed=20260807)

    assert first == second
    assert len(first.customers) == 120
    assert len(first.accounts) == 160
    assert len(first.transactions) == 900
    assert len(first.loan_applications) == 80
    assert len(first.service_cases) == 70
    assert len(first.case_events) == 210


def test_seed_preserves_foreign_keys_and_operational_variety() -> None:
    rows = build_seed_rows(seed=20260807)
    customer_ids = {row.customer_id for row in rows.customers}
    account_ids = {row.account_id for row in rows.accounts}
    case_ids = {row.case_id for row in rows.service_cases}

    assert {row.customer_id for row in rows.accounts} <= customer_ids
    assert {row.account_id for row in rows.transactions} <= account_ids
    assert {row.customer_id for row in rows.loan_applications} <= customer_ids
    assert {row.customer_id for row in rows.service_cases} <= customer_ids
    assert {row.case_id for row in rows.case_events} <= case_ids
    assert {row.risk_rating for row in rows.customers} == {"standard", "high"}
    assert {row.status for row in rows.service_cases} >= {"open", "closed"}
    assert any(row.status == "open" and row.due_at < rows.as_of for row in rows.service_cases)
    assert any(row.status == "open" and row.due_at >= rows.as_of for row in rows.service_cases)


def test_seeded_sqlite_contains_exact_counts() -> None:
    connection = sqlite3.connect(":memory:")
    counts = seed_bankops(connection, seed=20260807)

    assert counts == {
        "customers": 120,
        "accounts": 160,
        "transactions": 900,
        "loan_applications": 80,
        "service_cases": 70,
        "case_events": 210,
    }
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_policy_documents_are_explicitly_synthetic_and_versioned() -> None:
    documents_dir = (
        Path(__file__).parents[5] / "data" / "bankops" / "documents"
    )
    policies = sorted(documents_dir.glob("*.md"))

    assert len(policies) == 4
    for policy in policies:
        text = policy.read_text(encoding="utf-8")
        for required_field in (
            "document_id:",
            "version:",
            "effective_date:",
            "owner:",
            "status:",
            "synthetic: true",
        ):
            assert required_field in text
