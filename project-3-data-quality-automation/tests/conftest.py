"""
Shared fixtures for all test modules.
Loads CSVs and sets up SQLite DB from Project 1 + 2 data.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import pytest

# Paths relative to this conftest.py (tests/ dir)
ROOT        = os.path.dirname(os.path.dirname(__file__))
HEALTH_CSV  = os.path.join(ROOT, '..', 'project-1-healthcare-readmission', 'data', 'diabetic_readmission.csv')
FINANCE_CSV = os.path.join(ROOT, '..', 'project-2-finance-dashboard', 'data', 'expenses_synthetic.csv')
BUDGET_CSV  = os.path.join(ROOT, '..', 'project-2-finance-dashboard', 'data', 'monthly_budgets.csv')
HEALTH_SQL_DIR = os.path.join(ROOT, '..', 'project-1-healthcare-readmission', 'sql')


@pytest.fixture(scope='session')
def health_df():
    """Load healthcare CSV, replace '?' sentinels with NaN."""
    if not os.path.exists(HEALTH_CSV):
        pytest.skip(f'Healthcare dataset not found at {HEALTH_CSV}. '
                    'Download from UCI and place as project-1-healthcare-readmission/data/diabetic_readmission.csv')
    df = pd.read_csv(HEALTH_CSV, low_memory=False)
    df.replace('?', np.nan, inplace=True)
    return df


@pytest.fixture(scope='session')
def finance_df():
    """Load synthetic finance CSV. Run 00_generate_data.ipynb first."""
    if not os.path.exists(FINANCE_CSV):
        pytest.skip(f'Finance dataset not found at {FINANCE_CSV}. '
                    'Run project-2-finance-dashboard/python/00_generate_data.ipynb first.')
    return pd.read_csv(FINANCE_CSV, parse_dates=['date'])


@pytest.fixture(scope='session')
def budget_df():
    """Load monthly budget reference."""
    if not os.path.exists(BUDGET_CSV):
        pytest.skip('Budget CSV not found. Run 00_generate_data.ipynb first.')
    return pd.read_csv(BUDGET_CSV)


@pytest.fixture(scope='session')
def health_db(health_df):
    """
    In-memory SQLite DB with star schema + views loaded from Project 1 SQL files.
    Falls back gracefully if SQL files are missing.
    """
    conn = sqlite3.connect(':memory:')

    schema_path = os.path.join(HEALTH_SQL_DIR, '01_schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path) as f:
            conn.executescript(f.read())

    # Load raw data as staging table for views
    health_df.to_sql('staging_raw', conn, if_exists='replace', index=False)

    # Create a minimal fact table for view testing
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fact_admissions AS
        SELECT
            rowid AS admission_id,
            CAST(patient_nbr AS INTEGER) AS patient_id,
            CASE
                WHEN CAST(diag_1 AS REAL) BETWEEN 390 AND 459 THEN 1
                WHEN CAST(diag_1 AS REAL) BETWEEN 250 AND 251 THEN 2
                ELSE 3
            END AS diagnosis_id,
            CAST(num_lab_procedures AS INTEGER) AS num_lab_procedures,
            CAST(num_procedures AS INTEGER) AS num_procedures,
            CAST(num_medications AS INTEGER) AS num_medications,
            CAST(number_outpatient AS INTEGER) AS num_outpatient_visits,
            CAST(number_inpatient AS INTEGER) AS num_inpatient_visits,
            CAST(number_emergency AS INTEGER) AS num_emergency_visits,
            CAST(time_in_hospital AS INTEGER) AS time_in_hospital,
            insulin AS insulin_prescribed,
            diabetesMed AS diabetesMed_prescribed,
            A1Cresult AS a1c_result,
            readmitted,
            CASE WHEN readmitted = '<30' THEN 1 ELSE 0 END AS readmitted_within_30
        FROM staging_raw
        LIMIT 10000
    """)

    views_path = os.path.join(HEALTH_SQL_DIR, '04_views.sql')
    if os.path.exists(views_path):
        try:
            with open(views_path) as f:
                conn.executescript(f.read())
        except Exception:
            pass  # views may fail if dims are missing; tests skip gracefully

    conn.commit()
    yield conn
    conn.close()
