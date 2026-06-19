# Project 2 — Maternal Fat Ultrasound Measurements & Impact on Gestational Outcomes

**Status:** Complete — [Live Dashboard Gallery](https://pavishya.netlify.app/maternal-health-gallery.html)
**Domain:** Maternal & Perinatal Health
**Tools:** PostgreSQL · Power BI · DAX
**Dataset:** [PhysioNet — Maternal fat ultrasound measurement and nutritional assessment during pregnancy (v1.0.0)](https://physionet.org/content/maternal-ultrasound-nutrition/1.0.0/)
**Power BI File:** [Maternalhealth_Projectdashboard_Final.pbix](./Maternalhealth_Projectdashboard_Final.pbix)

---

## Business Question

> *Can early-pregnancy maternal abdominal fat measurements (visceral and subcutaneous adipose tissue, taken by ultrasound) predict gestational complications — gestational diabetes, preeclampsia, and preterm birth — and how do they relate to neonatal outcomes?*

---

## About the Dataset

A prospective cohort study conducted in Porto Alegre, Brazil (Oct 2016–Dec 2017), tracking 211 pregnant participants (of 272 originally enrolled; ~22% lost to follow-up) across 116 variables. Each case combines:

- **Epigastric measurements** (preperitoneal m-VAT / m-SAT) — captured for every participant
- **Periumbilical measurements** — captured for pregnancies under 20 weeks
- Demographic, dietary, lab, ultrasound, delivery, and neonatal data

**Citation:** Rocha, A. d. S., et al. (2020). *Maternal fat ultrasound measurement and nutritional assessment during pregnancy.* PhysioNet. DOI: [10.13026/hfks-3d71](https://doi.org/10.13026/hfks-3d71)

---

## ETL Pipeline

This project follows a 5-stage pipeline:

```
Extract              Stage                Transform              Load                 Analyze
(profile columns,    (raw CSVs into        (clean & reshape       (final tables into   (DAX measures,
 propose schema)      Postgres, .sql)       into report-ready      Power BI, verify      EDA, dashboard
                                             state, documented      relationships)        build)
                                             transformations)
```

**Extract** — Profile every column across the two source CSVs, document data types and nulls, and propose a relational data model.

**Stage** — Load the raw CSVs into PostgreSQL as-is (`sql/01_staging_schema.sql`), preserving the original data for lineage/auditability.

**Transform** — Clean and reshape staged data into report-ready tables, with every transformation documented (rationale, not just the SQL).

**Load** — Load the final tables into Power BI, define relationships, and validate the model before building DAX measures.

**Analyze** — Build the Power BI dashboard surfacing the strongest insights on fat measurements vs. gestational/neonatal outcomes.

---

## Data Model

Every source table shares a single grain — **one row per `case_id`** — so the model is a hub-and-spoke design centered on `Demographics`, with each clinical domain split into its own table for clarity and query performance rather than one extremely wide table:

| Table | Captures |
|---|---|
| `Demographics` | Age, color/ethnicity — the central hub |
| `Diet` | Meal frequency and food group intake |
| `Past_Pregnancies` | Prior newborn weights, gestational ages, miscarriage history |
| `Medical_History` | Hypertension, diabetes, substance use, chronic disease history |
| `Lab_Values` | Hematocrit, hemoglobin, glucose/OGTT, infectious disease screens by trimester |
| `maternal_biometrics` | Blood pressure, periumbilical/preperitoneal fat measurements, circumferences, skinfolds |
| `ultrasound_details` | Gestational age at inclusion/birth, fetal weight & percentile, prenatal visit count |
| `BMI` | Pre-pregnancy through prepartum weight and BMI by trimester |
| `Delivery_and_hospitalization` | Delivery mode, hypertension/preeclampsia/GDM at delivery, hospital stay |
| `Neonatal_records` | Newborn weight/height/circumference, Apgar scores, resuscitation events |

All tables relate 1:1 on `case_id`, so in Power BI they're modeled as a single-direction star around `Demographics`, with `maternal_biometrics`, `ultrasound_details`, and `BMI` as the primary measure tables for the fat/outcome analysis, and the rest as supporting dimensions for filtering and segmentation.

---

## Dashboards

The final Power BI workbook (`Maternalhealth_Projectdashboard_Final.pbix`) ships 7 dashboards covering 272 pregnancy cases:

| Dashboard | Focus |
|---|---|
| Demographics Analysis | Patient/follow-up counts, BMI status shift, ethnicity distribution, birth weight by maternal age |
| Dietary Habits and Hospital Outcomes | Meal/diet habits vs. GDM rate, delivery mode, hospital stay |
| Medical History and Lifestyle | Hypertension, tobacco, alcohol, and diabetes treatment patterns by ethnicity and age |
| Anthropometry and Pregnancy History | Trimester-by-trimester weight gain, miscarriage rate, first-born status by age group |
| Lab Test and Vitals | Infectious disease screening rates, glucose by trimester/test type, GDM vs. non-GDM comparison |
| Predictive Drivers of Newborn Weight | Decomposition tree ranking inputs (systolic BP, visceral/subcutaneous fat, glucose) by impact on birth weight |
| Newborn and Ultrasound | Newborn weight/health status, gestational age, fetal weight percentile distribution |

See the [live dashboard gallery](https://pavishya.netlify.app/maternal-health-gallery.html) for full screenshots and key insights per dashboard.

---

## Sprint Roadmap

| Sprint | Deliverables | Status |
|---|---|---|
| **Sprint 1** | Data definition, data staging, proposed schema, transformation specs for 2 tables | Complete |
| **Sprint 2** | Transformation spec document, staging `.sql` file, finalized model | Complete |
| **Sprint 3** | Consolidated cleaning steps (SQL) for the selected schema, final `.sql` file, final `.bak` file | Complete |
| **Sprint 4** | Load data into Power BI, build DAX measures, complete EDA, build and consolidate dashboards | Complete |

---

## Skills Demonstrated

`PostgreSQL` `Data Modeling` `ETL` `Data Cleaning` `Power BI` `DAX` `EDA` `Maternal Health Analytics`
