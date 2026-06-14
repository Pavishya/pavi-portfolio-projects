# Project 1 — Hospital Readmission Risk Analytics

**Domain:** Healthcare  
**Tools:** SQL (SQLite/PostgreSQL) · Python (pandas, scipy, sklearn) · Power BI  
**Dataset:** [UCI Diabetes 130-US Hospitals](https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008) (~101,766 admissions)

---

## Business Question

> *"Which patient and clinical factors most strongly predict 30-day hospital readmission — and how can we segment patients into risk tiers for proactive intervention?"*

---

## Architecture

```
Raw CSV (UCI Dataset)
      │
      ▼
[SQL] Star Schema (SQLite)
  dim_patient · dim_diagnosis · dim_time · fact_admissions
      │
      ├──▶ [Python] EDA → Statistical Analysis → Risk Model
      │         └── risk_scores_output.csv
      │
      └──▶ [Power BI] Executive Dashboard
                ├── Page 1: Executive Summary
                ├── Page 2: Patient Risk Heatmap
                └── Page 3: Clinical Trends
```

---

## SQL Highlights (`sql/`)

| File | What it showcases |
|---|---|
| `01_schema.sql` | Star schema design, indexed foreign keys |
| `02_data_load.sql` | ICD-9 bucketing with CASE, INSERT...SELECT |
| `03_analytical_queries.sql` | CTEs, RANK(), LAG(), NTILE(), subqueries |
| `04_views.sql` | Reusable views for BI + Python consumption |

**Standout query:** Q4 in `03_analytical_queries.sql` — chained CTEs computing a composite risk score from LOS, medications, and inpatient history.

---

## Python Highlights (`python/`)

| Notebook | Key techniques |
|---|---|
| `01_eda.ipynb` | Missing value analysis, distribution plots, SQLite load |
| `02_statistical_analysis.ipynb` | Chi-square test, Mann-Whitney U, correlation matrix |
| `03_risk_modeling.ipynb` | Feature engineering, sklearn pipeline, ROC-AUC, feature importance |

**Model performance:** ROC-AUC ~0.64 (logistic regression baseline; interpretability prioritised over raw accuracy for clinical explainability)

---

## Power BI Dashboard (`powerbi/`)

**Data model:** Star schema — `fact_admissions` connected to 3 dimension tables

**DAX measures used:**
```
Readmission Rate % = DIVIDE(CALCULATE(COUNTROWS(fact_admissions), fact_admissions[readmitted_within_30] = 1), COUNTROWS(fact_admissions))

Avg LOS = AVERAGE(fact_admissions[time_in_hospital])

High Risk Patients = CALCULATE(COUNTROWS(vw_patient_risk_summary), vw_patient_risk_summary[risk_tier] = "High")
```

**Dashboard pages:**
1. **Executive Summary** — KPI cards (readmission rate, avg LOS, high-risk count), trend line, diagnosis breakdown
2. **Patient Risk Heatmap** — risk scores by age × diagnosis, drill-through to patient detail
3. **Clinical Trends** — A1C impact, insulin analysis, medication count vs readmission

> Screenshots in `powerbi/screenshots/` — add your `.pbix` file here

---

## Key Findings

- **30-day readmission rate:** ~11% across all admissions
- **Highest risk group:** Age 70–80, circulatory diagnosis, 3+ prior inpatient visits
- **A1C > 8:** 2.3pp higher readmission rate vs normal A1C
- **Top predictive features:** Total service utilisation, length of stay, age group
- **Insulin prescribing:** Patients with "Up" insulin dose had highest readmission rate

---

## How to Run

```bash
# 1. Install dependencies
pip install pandas numpy matplotlib seaborn scipy scikit-learn jupyter

# 2. Download dataset
# https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for-years+1999-2008
# Place as: data/diabetic_readmission.csv

# 3. Run notebooks in order
jupyter notebook python/01_eda.ipynb        # Also loads SQLite DB
jupyter notebook python/02_statistical_analysis.ipynb
jupyter notebook python/03_risk_modeling.ipynb

# 4. Open Power BI
# File > Open > powerbi/readmission_dashboard.pbix
# Update data source path to data/healthcare.db or risk_scores_output.csv
```

---

## Skills Demonstrated

`SQL` `CTEs` `Window Functions` `Star Schema` `Data Modeling` `Python` `pandas` `scipy` `scikit-learn` `Logistic Regression` `ROC-AUC` `Feature Engineering` `Power BI` `DAX` `Drill-through` `Healthcare Analytics`
