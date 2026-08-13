"""Reproducible synthetic data generator for BankOps."""

import argparse
import json
import random
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from opsgraph.domains.bankops.schema import BANKOPS_SCHEMA, TABLE_NAMES

DEFAULT_SEED = 20260807
DEFAULT_AS_OF = datetime(2026, 8, 7, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class CustomerRow:
    customer_id: str
    full_name: str
    segment: str
    risk_rating: str
    created_at: datetime


@dataclass(frozen=True)
class AccountRow:
    account_id: str
    customer_id: str
    product: str
    status: str
    opened_at: datetime
    balance_cents: int


@dataclass(frozen=True)
class TransactionRow:
    transaction_id: str
    account_id: str
    occurred_at: datetime
    direction: str
    amount_cents: int
    category: str
    flagged: int


@dataclass(frozen=True)
class LoanApplicationRow:
    application_id: str
    customer_id: str
    submitted_at: datetime
    product: str
    amount_cents: int
    status: str
    exception_reason: str | None


@dataclass(frozen=True)
class ServiceCaseRow:
    case_id: str
    customer_id: str
    case_type: str
    priority: str
    status: str
    opened_at: datetime
    due_at: datetime
    closed_at: datetime | None
    assigned_team: str


@dataclass(frozen=True)
class CaseEventRow:
    event_id: str
    case_id: str
    occurred_at: datetime
    event_type: str
    note: str


@dataclass(frozen=True)
class BankOpsSeedRows:
    as_of: datetime
    customers: tuple[CustomerRow, ...]
    accounts: tuple[AccountRow, ...]
    transactions: tuple[TransactionRow, ...]
    loan_applications: tuple[LoanApplicationRow, ...]
    service_cases: tuple[ServiceCaseRow, ...]
    case_events: tuple[CaseEventRow, ...]


def build_seed_rows(
    seed: int = DEFAULT_SEED,
    *,
    as_of: datetime = DEFAULT_AS_OF,
) -> BankOpsSeedRows:
    rng = random.Random(seed)

    customers = tuple(
        CustomerRow(
            customer_id=f"CUST-{index:04d}",
            full_name=f"Synthetic Customer {index:04d}",
            segment="small_business" if index % 4 == 0 else "retail",
            risk_rating="high" if index % 5 == 0 else "standard",
            created_at=as_of - timedelta(days=500 + index * 3),
        )
        for index in range(1, 121)
    )

    accounts = tuple(
        AccountRow(
            account_id=f"ACC-{index:04d}",
            customer_id=customers[(index - 1) % len(customers)].customer_id,
            product="savings" if index % 3 == 0 else "transaction",
            status=("restricted" if index % 19 == 0 else "closed" if index % 37 == 0 else "active"),
            opened_at=as_of - timedelta(days=200 + index * 2),
            balance_cents=rng.randint(25_000, 8_000_000),
        )
        for index in range(1, 161)
    )

    categories = ("salary", "groceries", "utilities", "transfer", "cash", "merchant")
    transactions = tuple(
        TransactionRow(
            transaction_id=f"TXN-{index:05d}",
            account_id=accounts[rng.randrange(len(accounts))].account_id,
            occurred_at=as_of - timedelta(hours=rng.randint(1, 24 * 120)),
            direction="credit" if index % 4 == 0 else "debit",
            amount_cents=rng.randint(500, 750_000),
            category=categories[index % len(categories)],
            flagged=1 if index % 31 == 0 else 0,
        )
        for index in range(1, 901)
    )

    loan_statuses = ("pending", "approved", "declined")
    loan_applications = tuple(
        LoanApplicationRow(
            application_id=f"LOAN-{index:04d}",
            customer_id=customers[(index * 7) % len(customers)].customer_id,
            submitted_at=as_of - timedelta(days=1 + index),
            product="home" if index % 4 == 0 else "personal",
            amount_cents=rng.randint(500_000, 90_000_000),
            status=loan_statuses[index % len(loan_statuses)],
            exception_reason=(
                "Manual income verification required" if index % 9 == 0 else None
            ),
        )
        for index in range(1, 81)
    )

    case_types = ("complaint", "onboarding", "lending_exception", "transaction_review")
    teams = ("Customer Care", "KYC Operations", "Lending Operations", "Financial Crime")
    service_cases_list: list[ServiceCaseRow] = []
    for index in range(1, 71):
        priority = "priority" if index % 4 == 0 else "standard"
        status = "closed" if index % 3 == 0 else "open"
        opened_at = as_of - timedelta(days=(index % 12) + 1, hours=index % 7)
        sla_hours = 4 if priority == "priority" else 24
        due_at = opened_at + timedelta(hours=sla_hours)
        if status == "open" and index % 5 == 1:
            due_at = as_of + timedelta(hours=(index % 8) + 1)
        closed_at = (
            min(due_at, opened_at + timedelta(hours=max(1, sla_hours - 1)))
            if status == "closed"
            else None
        )
        service_cases_list.append(
            ServiceCaseRow(
                case_id=f"CASE-{index:04d}",
                customer_id=customers[(index * 11) % len(customers)].customer_id,
                case_type=case_types[(index - 1) % len(case_types)],
                priority=priority,
                status=status,
                opened_at=opened_at,
                due_at=due_at,
                closed_at=closed_at,
                assigned_team=teams[(index - 1) % len(teams)],
            )
        )
    service_cases = tuple(service_cases_list)

    case_events_list: list[CaseEventRow] = []
    for case in service_cases:
        opened = case.opened_at
        for event_number in range(1, 4):
            event_type = (
                "opened"
                if event_number == 1
                else "closed"
                if event_number == 3 and case.status == "closed"
                else "reviewed"
            )
            case_events_list.append(
                CaseEventRow(
                    event_id=f"EVT-{case.case_id[5:]}-{event_number}",
                    case_id=case.case_id,
                    occurred_at=opened + timedelta(hours=event_number - 1),
                    event_type=event_type,
                    note=f"Synthetic {event_type} event for {case.case_id}",
                )
            )

    return BankOpsSeedRows(
        as_of=as_of,
        customers=customers,
        accounts=accounts,
        transactions=transactions,
        loan_applications=loan_applications,
        service_cases=service_cases,
        case_events=tuple(case_events_list),
    )


def seed_bankops(
    connection: sqlite3.Connection,
    seed: int = DEFAULT_SEED,
) -> dict[str, int]:
    rows = build_seed_rows(seed)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(BANKOPS_SCHEMA)

    with connection:
        for table in reversed(TABLE_NAMES):
            connection.execute(f"DELETE FROM {table}")
        for table in TABLE_NAMES:
            records = getattr(rows, table)
            if not records:
                continue
            values = [asdict(record) for record in records]
            columns = tuple(values[0])
            placeholders = ", ".join("?" for _ in columns)
            connection.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                [
                    tuple(_sqlite_value(record[column]) for column in columns)
                    for record in values
                ],
            )

    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in TABLE_NAMES
    }


def _sqlite_value(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(args.output) as connection:
        counts = seed_bankops(connection, seed=args.seed)
    print(json.dumps({"database": str(args.output.resolve()), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
