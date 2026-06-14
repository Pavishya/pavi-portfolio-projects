# Project 3 — Data Quality Automation Suite

**Domain:** QA / Test Automation  
**Tools:** Python · pytest · pytest-html  
**Tests cover:** Project 1 (Healthcare) + Project 2 (Finance) datasets and transformations

---

## Narrative

> *"I don't just analyse data — I write automated tests to ensure the pipeline is trustworthy before insights reach stakeholders."*

This project bridges Pavishya's QA background (TCS) with her data analytics work. It demonstrates that analytical pipelines should be tested just like software — with clear assertions, parameterization, and automated reporting.

---

## Test Structure

```
project-3-data-quality-automation/
├── src/
│   └── validators.py          ← Reusable validation functions
├── tests/
│   ├── conftest.py            ← Session-scoped fixtures (CSV loads, SQLite DB)
│   ├── test_data_quality.py   ← Dataset quality checks (nulls, ranges, allowed values)
│   ├── test_transformations.py← Unit tests for feature engineering functions
│   └── test_sql_queries.py    ← SQL view and query result validation
├── reports/                   ← pytest-html output (generated on run)
└── requirements.txt
```

---

## Test Coverage

### `test_data_quality.py` — 20 tests

| Test Group | What's Validated |
|---|---|
| Healthcare: schema | All 12 required columns present |
| Healthcare: nulls | No nulls in patient_nbr, time_in_hospital, readmitted, num_medications |
| Healthcare: ranges | 7 numeric columns parameterized against UCI documented bounds |
| Healthcare: values | readmitted ∈ {`<30`, `>30`, `NO`}; gender ∈ known values |
| Healthcare: business | Readmission rate 5–25%; dataset ≥ 50,000 rows |
| Finance: schema | All 6 required columns present |
| Finance: amounts | All transaction amounts > 0 |
| Finance: coverage | 12 months covered; 8 categories each have transactions (parameterized) |
| Finance: types | type ∈ {`debit`, `credit`}; dates parse cleanly |

### `test_transformations.py` — 14 tests

| Function | Tests |
|---|---|
| `compute_risk_score()` | Always in (0,1), increases with age and utilisation, handles zero inputs |
| `bucket_age()` | 7 parameterized age groups, null/empty/invalid edge cases |
| `bucket_expense_category()` | 8 parameterized categories, unknown/empty/null edge cases |

### `test_sql_queries.py` — 12 tests

| Test | What's Validated |
|---|---|
| fact_admissions row count | Non-empty after load |
| Binary flag integrity | `readmitted_within_30` ∈ {0, 1} |
| Rate calculation | Readmission rate query returns value in [0, 100] |
| Aggregation correctness | GROUP BY sums match total row count |
| CTE risk scoring | Complex 2-level CTE executes and returns rows |
| Finance JOIN | Budget vs Actual join produces results |
| Window function | LAG() query executes without error |

---

## Key pytest Features Demonstrated

```python
# Parameterized tests — one test definition, multiple inputs
@pytest.mark.parametrize('col,min_val,max_val', [
    ('time_in_hospital',  1, 14),
    ('num_medications',   0, 81),
    ...
])
def test_numeric_column_within_range(self, health_df, col, min_val, max_val):
    ...

# Session-scoped fixtures — CSV loaded once, shared across all tests
@pytest.fixture(scope='session')
def health_df():
    return pd.read_csv(HEALTH_CSV)

# Graceful skip when data isn't available
if not os.path.exists(HEALTH_CSV):
    pytest.skip('Dataset not found — download from UCI first')
```

---

## How to Run

```bash
# 1. Navigate to this project
cd project-3-data-quality-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ensure data exists
#    - project-1-healthcare-readmission/data/diabetic_readmission.csv (UCI download)
#    - project-2-finance-dashboard/data/expenses_synthetic.csv (run 00_generate_data.ipynb)

# 4. Run all tests with HTML report
pytest tests/ --html=reports/test_report.html --self-contained-html -v

# 5. Open report
open reports/test_report.html
```

---

## Sample Output

```
tests/test_transformations.py::TestRiskScoring::test_risk_score_within_bounds PASSED
tests/test_transformations.py::TestAgeBucketing::test_age_bucket_mapping[<30-40>-Young] PASSED
tests/test_data_quality.py::TestHealthcareDataQuality::test_numeric_column_within_range[time_in_hospital-1-14] PASSED
tests/test_data_quality.py::TestFinanceDataQuality::test_each_category_has_transactions[Groceries] PASSED
tests/test_sql_queries.py::TestSQLViews::test_complex_cte_returns_results PASSED

===== 46 passed in 4.32s =====
```

---

## Skills Demonstrated

`pytest` `conftest.py` `Session Fixtures` `Parameterized Tests` `pytest-html` `Data Quality Testing` `SQL Testing` `Unit Testing` `Edge Cases` `SQLite` `pandas` `QA Automation` `Pipeline Validation`
