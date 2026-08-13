"""Portable SQLite schema for the synthetic BankOps dataset."""

BANKOPS_SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('retail', 'small_business')),
    risk_rating TEXT NOT NULL CHECK (risk_rating IN ('standard', 'high')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    product TEXT NOT NULL CHECK (product IN ('transaction', 'savings')),
    status TEXT NOT NULL CHECK (status IN ('active', 'restricted', 'closed')),
    opened_at TEXT NOT NULL,
    balance_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    occurred_at TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('credit', 'debit')),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    category TEXT NOT NULL,
    flagged INTEGER NOT NULL CHECK (flagged IN (0, 1))
);

CREATE TABLE IF NOT EXISTS loan_applications (
    application_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    submitted_at TEXT NOT NULL,
    product TEXT NOT NULL CHECK (product IN ('personal', 'home')),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'declined')),
    exception_reason TEXT
);

CREATE TABLE IF NOT EXISTS service_cases (
    case_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    case_type TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('standard', 'priority')),
    status TEXT NOT NULL CHECK (status IN ('open', 'closed')),
    opened_at TEXT NOT NULL,
    due_at TEXT NOT NULL,
    closed_at TEXT,
    assigned_team TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS case_events (
    event_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES service_cases(case_id),
    occurred_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    note TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account_time ON transactions(account_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_loans_customer ON loan_applications(customer_id);
CREATE INDEX IF NOT EXISTS idx_cases_customer_status ON service_cases(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_case_events_case_time ON case_events(case_id, occurred_at);
"""

TABLE_NAMES = (
    "customers",
    "accounts",
    "transactions",
    "loan_applications",
    "service_cases",
    "case_events",
)
