"""Allowlisted semantic schemas exposed to text-to-SQL."""

from opsgraph.analytics_sql.contracts import SemanticSchema

BANKOPS_SEMANTIC_SCHEMA = SemanticSchema(
    name="bankops",
    tables={
        "customers": (
            "customer_id",
            "full_name",
            "segment",
            "risk_rating",
            "created_at",
        ),
        "accounts": (
            "account_id",
            "customer_id",
            "product",
            "status",
            "opened_at",
            "balance_cents",
        ),
        "transactions": (
            "transaction_id",
            "account_id",
            "occurred_at",
            "direction",
            "amount_cents",
            "category",
            "flagged",
        ),
        "loan_applications": (
            "application_id",
            "customer_id",
            "submitted_at",
            "product",
            "amount_cents",
            "status",
            "exception_reason",
        ),
        "service_cases": (
            "case_id",
            "customer_id",
            "case_type",
            "priority",
            "status",
            "opened_at",
            "due_at",
            "closed_at",
            "assigned_team",
        ),
        "case_events": (
            "event_id",
            "case_id",
            "occurred_at",
            "event_type",
            "note",
        ),
    },
    descriptions={
        "service_cases": "Synthetic operational cases and their SLA due timestamps.",
        "case_events": "Immutable synthetic events associated with a service case.",
        "transactions": "Synthetic account transactions; flagged is 0 or 1.",
    },
)
