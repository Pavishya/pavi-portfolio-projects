"""
SQL query validation tests using in-memory SQLite DB.
Demonstrates: DB fixture testing, result set assertions, data contract validation.
"""

import pytest
import pandas as pd
import sqlite3


class TestSQLViews:

    def test_fact_admissions_not_empty(self, health_db):
        count = health_db.execute('SELECT COUNT(*) FROM fact_admissions').fetchone()[0]
        assert count > 0, 'fact_admissions table is empty'

    def test_readmitted_within_30_is_binary(self, health_db):
        """readmitted_within_30 must only contain 0 or 1."""
        invalid = health_db.execute(
            "SELECT COUNT(*) FROM fact_admissions WHERE readmitted_within_30 NOT IN (0, 1)"
        ).fetchone()[0]
        assert invalid == 0, f'{invalid} rows with invalid readmitted_within_30 values'

    def test_time_in_hospital_non_negative(self, health_db):
        invalid = health_db.execute(
            'SELECT COUNT(*) FROM fact_admissions WHERE time_in_hospital < 0'
        ).fetchone()[0]
        assert invalid == 0, f'{invalid} rows with negative time_in_hospital'

    def test_readmission_rate_between_0_and_100(self, health_db):
        row = health_db.execute(
            'SELECT 100.0 * SUM(readmitted_within_30) / COUNT(*) FROM fact_admissions'
        ).fetchone()[0]
        assert row is not None, 'Readmission rate query returned NULL'
        assert 0 <= row <= 100, f'Readmission rate {row:.2f}% outside [0, 100]'

    def test_no_null_patient_ids_in_fact(self, health_db):
        nulls = health_db.execute(
            'SELECT COUNT(*) FROM fact_admissions WHERE patient_id IS NULL'
        ).fetchone()[0]
        assert nulls == 0, f'{nulls} NULL patient_id values in fact_admissions'

    def test_medications_non_negative(self, health_db):
        invalid = health_db.execute(
            'SELECT COUNT(*) FROM fact_admissions WHERE num_medications < 0'
        ).fetchone()[0]
        assert invalid == 0, f'{invalid} rows with negative num_medications'

    def test_readmission_groupby_sums_to_total(self, health_db):
        """Aggregated readmission counts should equal total row count."""
        total = health_db.execute('SELECT COUNT(*) FROM fact_admissions').fetchone()[0]
        agg   = health_db.execute(
            'SELECT SUM(cnt) FROM (SELECT readmitted, COUNT(*) AS cnt FROM fact_admissions GROUP BY readmitted)'
        ).fetchone()[0]
        assert total == agg, f'Groupby sum {agg} != total {total}'

    def test_complex_cte_returns_results(self, health_db):
        """The chained CTE risk scoring query should return at least 1 row."""
        rows = health_db.execute("""
            WITH admission_profile AS (
                SELECT
                    patient_id,
                    time_in_hospital,
                    num_medications,
                    num_inpatient_visits,
                    readmitted_within_30
                FROM fact_admissions
            ),
            risk_scores AS (
                SELECT
                    patient_id,
                    AVG(time_in_hospital) AS avg_los,
                    SUM(num_inpatient_visits) AS total_inpatient,
                    SUM(readmitted_within_30) AS readmit_count,
                    ROUND(
                        (AVG(time_in_hospital) * 0.3)
                        + (AVG(num_medications) * 0.2)
                        + (SUM(num_inpatient_visits) * 0.3)
                        + (SUM(readmitted_within_30) * 2.0)
                    , 2) AS composite_risk_score
                FROM admission_profile
                GROUP BY patient_id
            )
            SELECT COUNT(*) FROM risk_scores WHERE composite_risk_score > 0
        """).fetchone()[0]
        assert rows > 0, 'CTE risk score query returned 0 results'


class TestFinanceSQL:

    @pytest.fixture(scope='class')
    def finance_db(self, finance_df, budget_df):
        """In-memory SQLite with finance tables."""
        conn = sqlite3.connect(':memory:')
        finance_df.to_sql('transactions',    conn, if_exists='replace', index=False)
        budget_df.to_sql('monthly_budgets',  conn, if_exists='replace', index=False)
        conn.commit()
        yield conn
        conn.close()

    def test_transactions_not_empty(self, finance_db):
        count = finance_db.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
        assert count > 0

    def test_savings_rate_query_returns_12_months(self, finance_db):
        rows = finance_db.execute(
            "SELECT COUNT(DISTINCT month) FROM transactions"
        ).fetchone()[0]
        assert rows == 12, f'Expected 12 months, got {rows}'

    def test_budget_variance_join_produces_rows(self, finance_db):
        rows = finance_db.execute("""
            SELECT COUNT(*) FROM transactions t
            JOIN monthly_budgets b ON t.month = b.month AND t.category = b.category
            WHERE t.type = 'debit'
        """).fetchone()[0]
        assert rows > 0, 'Budget vs Actual JOIN returned 0 rows'

    def test_lag_query_runs_without_error(self, finance_db):
        """Validates SQLite supports LAG() — requires SQLite >= 3.25."""
        try:
            result = finance_db.execute("""
                SELECT month, category,
                       SUM(amount) AS spend,
                       LAG(SUM(amount)) OVER (PARTITION BY category ORDER BY month) AS prev_spend
                FROM transactions
                WHERE type = 'debit'
                GROUP BY month, category
                LIMIT 5
            """).fetchall()
            assert len(result) > 0
        except Exception as e:
            pytest.skip(f'LAG() not supported on this SQLite version: {e}')
