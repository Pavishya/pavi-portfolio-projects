-- ============================================================
-- Project 2: Personal Finance Dashboard
-- Schema: Transaction-based finance data model
-- ============================================================

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id  INTEGER PRIMARY KEY,
    date            TEXT NOT NULL,
    category        TEXT NOT NULL,
    merchant        TEXT,
    amount          REAL NOT NULL,
    type            TEXT NOT NULL CHECK(type IN ('debit', 'credit')),
    month           TEXT,
    year            INTEGER
);

CREATE TABLE IF NOT EXISTS monthly_budgets (
    budget_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    month           TEXT NOT NULL,
    category        TEXT NOT NULL,
    budget_amount   REAL NOT NULL,
    UNIQUE(month, category)
);

CREATE INDEX IF NOT EXISTS idx_txn_date     ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_txn_month    ON transactions(month);
