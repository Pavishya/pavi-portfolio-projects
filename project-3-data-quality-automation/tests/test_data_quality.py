"""
Data quality tests for both datasets.
Demonstrates: parameterization, fixtures, boundary testing, sentinel handling.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from validators import check_no_nulls, check_value_range, check_allowed_values, check_positive_amounts, check_date_parseable


# ──────────────────────────────────────────────
# Healthcare Dataset Tests
# ──────────────────────────────────────────────

class TestHealthcareDataQuality:

    def test_required_columns_exist(self, health_df):
        required = [
            'patient_nbr', 'race', 'gender', 'age', 'time_in_hospital',
            'num_lab_procedures', 'num_procedures', 'num_medications',
            'number_outpatient', 'number_inpatient', 'number_emergency',
            'readmitted'
        ]
        missing_cols = [c for c in required if c not in health_df.columns]
        assert not missing_cols, f'Missing required columns: {missing_cols}'

    def test_no_nulls_in_key_columns(self, health_df):
        key_cols = ['patient_nbr', 'time_in_hospital', 'readmitted', 'num_medications']
        null_counts = check_no_nulls(health_df, key_cols)
        violations = {col: cnt for col, cnt in null_counts.items() if cnt > 0}
        assert not violations, f'Null values found in key columns: {violations}'

    @pytest.mark.parametrize('col,min_val,max_val', [
        ('time_in_hospital',    1,   14),
        ('num_lab_procedures',  0,  132),
        ('num_procedures',      0,    6),
        ('num_medications',     0,   81),
        ('number_inpatient',    0,   21),
        ('number_outpatient',   0,   42),
        ('number_emergency',    0,   76),
    ])
    def test_numeric_column_within_range(self, health_df, col, min_val, max_val):
        """Validates that numeric columns stay within documented UCI dataset bounds."""
        violations = check_value_range(health_df[col], min_val, max_val)
        violation_count = violations.sum()
        assert violation_count == 0, \
            f'{col}: {violation_count} rows outside [{min_val}, {max_val}]'

    def test_readmitted_values_are_valid(self, health_df):
        allowed = {'<30', '>30', 'NO'}
        invalid = check_allowed_values(health_df['readmitted'], list(allowed))
        assert invalid.sum() == 0, \
            f'Invalid readmitted values: {health_df.loc[invalid, "readmitted"].unique()}'

    def test_gender_values_are_valid(self, health_df):
        allowed = ['Male', 'Female', 'Unknown/Invalid']
        invalid = check_allowed_values(health_df['gender'], allowed)
        assert invalid.sum() == 0, \
            f'Unexpected gender values: {health_df.loc[invalid, "gender"].unique()}'

    def test_dataset_has_minimum_rows(self, health_df):
        assert len(health_df) >= 50_000, \
            f'Expected at least 50,000 rows, got {len(health_df):,}'

    def test_readmission_rate_is_realistic(self, health_df):
        """30-day readmission rate should be between 5% and 25% for this cohort."""
        rate = (health_df['readmitted'] == '<30').mean()
        assert 0.05 <= rate <= 0.25, \
            f'30-day readmission rate {rate:.2%} is outside expected range [5%, 25%]'

    def test_no_duplicate_admissions(self, health_df):
        """encounter_id should be unique per admission."""
        if 'encounter_id' in health_df.columns:
            dupes = health_df['encounter_id'].duplicated().sum()
            assert dupes == 0, f'{dupes} duplicate encounter_id values found'


# ──────────────────────────────────────────────
# Finance Dataset Tests
# ──────────────────────────────────────────────

class TestFinanceDataQuality:

    def test_required_columns_exist(self, finance_df):
        required = ['transaction_id', 'date', 'category', 'merchant', 'amount', 'type']
        missing_cols = [c for c in required if c not in finance_df.columns]
        assert not missing_cols, f'Missing columns: {missing_cols}'

    def test_transaction_amounts_are_positive(self, finance_df):
        violations = check_positive_amounts(finance_df['amount'])
        assert violations.sum() == 0, \
            f'{violations.sum()} transactions with non-positive amounts'

    def test_type_values_are_valid(self, finance_df):
        allowed = ['debit', 'credit']
        invalid = check_allowed_values(finance_df['type'], allowed)
        assert invalid.sum() == 0, \
            f'Invalid type values: {finance_df.loc[invalid, "type"].unique()}'

    def test_category_values_are_known(self, finance_df):
        known_categories = {
            'Housing', 'Groceries', 'Dining Out', 'Transport',
            'Healthcare', 'Entertainment', 'Shopping', 'Utilities', 'Income'
        }
        expenses = finance_df[finance_df['type'] == 'debit']
        unknown = set(expenses['category'].unique()) - known_categories
        assert not unknown, f'Unknown expense categories: {unknown}'

    def test_dates_are_parseable(self, finance_df):
        failed = pd.to_datetime(finance_df['date'], errors='coerce').isnull().sum()
        assert failed == 0, f'{failed} rows with unparseable dates'

    def test_dates_within_expected_year(self, finance_df):
        years = pd.to_datetime(finance_df['date']).dt.year.unique()
        assert set(years) == {2024}, f'Unexpected years in data: {set(years)}'

    def test_no_duplicate_transaction_ids(self, finance_df):
        dupes = finance_df['transaction_id'].duplicated().sum()
        assert dupes == 0, f'{dupes} duplicate transaction_ids'

    def test_income_transactions_exist(self, finance_df):
        income_rows = (finance_df['type'] == 'credit').sum()
        assert income_rows >= 12, \
            f'Expected at least 12 income entries (one/month), found {income_rows}'

    def test_twelve_months_covered(self, finance_df):
        months = pd.to_datetime(finance_df['date']).dt.to_period('M').nunique()
        assert months == 12, f'Expected 12 months, found {months}'

    @pytest.mark.parametrize('category', [
        'Housing', 'Groceries', 'Dining Out', 'Transport',
        'Healthcare', 'Entertainment', 'Shopping', 'Utilities'
    ])
    def test_each_category_has_transactions(self, finance_df, category):
        count = ((finance_df['category'] == category) & (finance_df['type'] == 'debit')).sum()
        assert count > 0, f'No transactions found for category: {category}'
