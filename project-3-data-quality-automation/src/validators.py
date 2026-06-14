"""
Reusable data validation functions.
Used by pytest fixtures and can be imported standalone for pipeline validation.
"""

import pandas as pd
import numpy as np
from typing import List, Optional


def check_no_nulls(df: pd.DataFrame, columns: List[str]) -> dict:
    """Return dict of column -> null count for specified columns."""
    return {col: int(df[col].isnull().sum()) for col in columns if col in df.columns}


def check_value_range(series: pd.Series, min_val: float, max_val: float) -> pd.Series:
    """Return boolean mask of rows outside [min_val, max_val]."""
    numeric = pd.to_numeric(series, errors='coerce')
    return (numeric < min_val) | (numeric > max_val)


def check_allowed_values(series: pd.Series, allowed: List[str]) -> pd.Series:
    """Return boolean mask of rows with values not in allowed set."""
    return ~series.isin(allowed)


def check_positive_amounts(series: pd.Series) -> pd.Series:
    """Return boolean mask of rows where amount is not positive."""
    numeric = pd.to_numeric(series, errors='coerce')
    return numeric <= 0


def check_date_parseable(series: pd.Series, fmt: Optional[str] = None) -> int:
    """Return count of rows where date cannot be parsed."""
    try:
        pd.to_datetime(series, format=fmt, errors='raise')
        return 0
    except Exception:
        failed = pd.to_datetime(series, format=fmt, errors='coerce').isnull().sum()
        return int(failed)


def check_no_duplicates(df: pd.DataFrame, subset: List[str]) -> int:
    """Return number of duplicate rows based on subset of columns."""
    return int(df.duplicated(subset=subset).sum())


def compute_risk_score(
    age_num: float,
    time_in_hospital: float,
    num_medications: float,
    total_utilisation: float,
) -> float:
    """
    Simplified logistic-style risk score in [0, 1].
    Used in test_transformations to validate bounded output.
    """
    raw = (
        0.05 * float(age_num)
        + 0.1  * float(time_in_hospital)
        + 0.02 * float(num_medications)
        + 0.15 * float(total_utilisation)
    )
    # Sigmoid to bound to (0, 1)
    return float(1 / (1 + np.exp(-raw + 3)))


def bucket_age(age_group: str) -> str:
    """Map raw UCI age bracket to simplified 3-tier bucket."""
    young    = {'[0-10)', '[10-20)', '[20-30)', '[30-40)'}
    middle   = {'[40-50)', '[50-60)', '[60-70)'}
    senior   = {'[70-80)', '[80-90)', '[90-100)'}
    if age_group in young:
        return 'Young'
    if age_group in middle:
        return 'Middle-Aged'
    if age_group in senior:
        return 'Senior'
    return 'Unknown'


def bucket_expense_category(category: str) -> str:
    """Map granular expense category to fixed/variable bucket."""
    fixed    = {'Housing', 'Utilities', 'Healthcare'}
    variable = {'Groceries', 'Dining Out', 'Transport', 'Entertainment', 'Shopping'}
    if category in fixed:
        return 'Fixed'
    if category in variable:
        return 'Variable'
    return 'Other'
