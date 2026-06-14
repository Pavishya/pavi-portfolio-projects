-- ============================================================
-- Data Load: Populate dimension and fact tables
-- Run AFTER 01_schema.sql
-- Source CSV: data/diabetic_readmission.csv (UCI dataset)
-- ============================================================

-- -------------------------------------------------------
-- dim_patient  (distinct patients from source CSV)
-- -------------------------------------------------------
-- PostgreSQL syntax:
-- COPY staging_raw FROM 'data/diabetic_readmission.csv' CSV HEADER;

-- SQLite equivalent via Python loader (see python/01_eda.ipynb):
-- conn.execute("INSERT INTO dim_patient SELECT DISTINCT ...")

INSERT OR IGNORE INTO dim_patient (patient_id, age_group, gender, race, weight_category)
SELECT DISTINCT
    CAST(patient_nbr AS INTEGER),
    age,
    gender,
    race,
    weight
FROM staging_raw;

-- -------------------------------------------------------
-- dim_diagnosis  (unique ICD-9 codes + lookup categories)
-- -------------------------------------------------------
INSERT OR IGNORE INTO dim_diagnosis (diag_code, diag_description, diag_category)
SELECT DISTINCT
    diag_1,
    CASE
        WHEN CAST(diag_1 AS REAL) BETWEEN 390 AND 459  THEN 'Circulatory'
        WHEN CAST(diag_1 AS REAL) BETWEEN 460 AND 519  THEN 'Respiratory'
        WHEN CAST(diag_1 AS REAL) BETWEEN 520 AND 579  THEN 'Digestive'
        WHEN CAST(diag_1 AS REAL) BETWEEN 250 AND 251  THEN 'Diabetes'
        WHEN CAST(diag_1 AS REAL) BETWEEN 800 AND 999  THEN 'Injury/Poisoning'
        WHEN CAST(diag_1 AS REAL) BETWEEN 140 AND 239  THEN 'Neoplasms'
        ELSE 'Other'
    END,
    CASE
        WHEN CAST(diag_1 AS REAL) BETWEEN 390 AND 459  THEN 'Circulatory'
        WHEN CAST(diag_1 AS REAL) BETWEEN 460 AND 519  THEN 'Respiratory'
        WHEN CAST(diag_1 AS REAL) BETWEEN 520 AND 579  THEN 'Digestive'
        WHEN CAST(diag_1 AS REAL) BETWEEN 250 AND 251  THEN 'Diabetes'
        WHEN CAST(diag_1 AS REAL) BETWEEN 800 AND 999  THEN 'Injury/Poisoning'
        WHEN CAST(diag_1 AS REAL) BETWEEN 140 AND 239  THEN 'Neoplasms'
        ELSE 'Other'
    END
FROM staging_raw
WHERE diag_1 IS NOT NULL AND diag_1 != '?';

-- -------------------------------------------------------
-- dim_admission_type
-- -------------------------------------------------------
INSERT OR IGNORE INTO dim_admission_type (admission_type_id, admission_type, discharge_type)
SELECT DISTINCT
    CAST(admission_type_id AS INTEGER),
    CASE admission_type_id
        WHEN '1' THEN 'Emergency'
        WHEN '2' THEN 'Urgent'
        WHEN '3' THEN 'Elective'
        WHEN '4' THEN 'Newborn'
        ELSE 'Other/Unknown'
    END,
    CASE discharge_disposition_id
        WHEN '1' THEN 'Discharged to Home'
        WHEN '3' THEN 'Discharged to SNF'
        WHEN '11' THEN 'Expired'
        ELSE 'Other'
    END
FROM staging_raw;

-- -------------------------------------------------------
-- fact_admissions
-- -------------------------------------------------------
INSERT INTO fact_admissions (
    patient_id, diagnosis_id, admission_type_id,
    num_lab_procedures, num_procedures, num_medications,
    num_outpatient_visits, num_inpatient_visits, num_emergency_visits,
    time_in_hospital, insulin_prescribed, diabetesMed_prescribed,
    a1c_result, readmitted, readmitted_within_30
)
SELECT
    CAST(r.patient_nbr AS INTEGER),
    d.diagnosis_id,
    CAST(r.admission_type_id AS INTEGER),
    CAST(r.num_lab_procedures AS INTEGER),
    CAST(r.num_procedures AS INTEGER),
    CAST(r.num_medications AS INTEGER),
    CAST(r.number_outpatient AS INTEGER),
    CAST(r.number_inpatient AS INTEGER),
    CAST(r.number_emergency AS INTEGER),
    CAST(r.time_in_hospital AS INTEGER),
    r.insulin,
    r.diabetesMed,
    r.A1Cresult,
    r.readmitted,
    CASE WHEN r.readmitted = '<30' THEN 1 ELSE 0 END
FROM staging_raw r
JOIN dim_diagnosis d ON d.diag_code = r.diag_1;
