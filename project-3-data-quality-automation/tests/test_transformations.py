"""
Unit tests for transformation and feature engineering functions in validators.py.
Demonstrates: edge case testing, boundary conditions, parameterization.
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from validators import compute_risk_score, bucket_age, bucket_expense_category


class TestRiskScoring:

    def test_risk_score_within_bounds(self):
        """Score must always be in (0, 1) regardless of input."""
        score = compute_risk_score(age_num=5, time_in_hospital=7, num_medications=20, total_utilisation=3)
        assert 0 < score < 1, f'Risk score {score} is outside (0, 1)'

    def test_risk_score_zero_inputs(self):
        score = compute_risk_score(0, 0, 0, 0)
        assert 0 < score < 1

    def test_risk_score_extreme_high_inputs(self):
        """Very high-risk patient should still return a valid bounded score."""
        score = compute_risk_score(age_num=9, time_in_hospital=14, num_medications=80, total_utilisation=50)
        assert 0 < score < 1

    def test_risk_score_increases_with_utilisation(self):
        """Higher utilisation should increase risk score."""
        low  = compute_risk_score(5, 5, 10, total_utilisation=1)
        high = compute_risk_score(5, 5, 10, total_utilisation=20)
        assert high > low, 'Higher utilisation should produce higher risk score'

    def test_risk_score_increases_with_age(self):
        young  = compute_risk_score(age_num=1, time_in_hospital=3, num_medications=5, total_utilisation=2)
        senior = compute_risk_score(age_num=8, time_in_hospital=3, num_medications=5, total_utilisation=2)
        assert senior > young, 'Older patients should have higher risk score'

    def test_risk_score_is_float(self):
        score = compute_risk_score(4, 5, 10, 3)
        assert isinstance(score, float)


class TestAgeBucketing:

    @pytest.mark.parametrize('age_group,expected', [
        ('[0-10)',   'Young'),
        ('[10-20)',  'Young'),
        ('[30-40)',  'Young'),
        ('[40-50)',  'Middle-Aged'),
        ('[60-70)',  'Middle-Aged'),
        ('[70-80)',  'Senior'),
        ('[90-100)', 'Senior'),
    ])
    def test_age_bucket_mapping(self, age_group, expected):
        assert bucket_age(age_group) == expected, \
            f'{age_group} should map to {expected}, got {bucket_age(age_group)}'

    def test_null_age_returns_unknown(self):
        assert bucket_age(None) == 'Unknown'

    def test_empty_string_returns_unknown(self):
        assert bucket_age('') == 'Unknown'

    def test_invalid_age_returns_unknown(self):
        assert bucket_age('[200-210)') == 'Unknown'


class TestExpenseCategoryBucketing:

    @pytest.mark.parametrize('category,expected_bucket', [
        ('Housing',      'Fixed'),
        ('Utilities',    'Fixed'),
        ('Healthcare',   'Fixed'),
        ('Groceries',    'Variable'),
        ('Dining Out',   'Variable'),
        ('Entertainment','Variable'),
        ('Shopping',     'Variable'),
        ('Transport',    'Variable'),
    ])
    def test_category_bucketing(self, category, expected_bucket):
        assert bucket_expense_category(category) == expected_bucket, \
            f'{category} should be {expected_bucket}'

    def test_unknown_category_returns_other(self):
        assert bucket_expense_category('Gambling') == 'Other'

    def test_empty_string_returns_other(self):
        assert bucket_expense_category('') == 'Other'

    def test_none_returns_other(self):
        assert bucket_expense_category(None) == 'Other'
