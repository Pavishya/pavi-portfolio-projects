-- ============================================================
-- Project 1: Hospital Readmission Risk Analytics
-- Schema: Star schema optimised for BI and analytical queries
-- Database: SQLite-compatible (also runs on PostgreSQL)
-- ============================================================

-- Dimension: Patient demographics
CREATE TABLE IF NOT EXISTS dim_patient (
    patient_id          INTEGER PRIMARY KEY,
    age_group           TEXT NOT NULL,          -- e.g. '[50-60)'
    gender              TEXT,
    race                TEXT,
    weight_category     TEXT
);

-- Dimension: Primary diagnosis codes
CREATE TABLE IF NOT EXISTS dim_diagnosis (
    diagnosis_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    diag_code           TEXT NOT NULL UNIQUE,   -- ICD-9 code
    diag_description    TEXT,
    diag_category       TEXT                    -- e.g. 'Circulatory', 'Diabetes'
);

-- Dimension: Calendar for time-intelligence in Power BI
CREATE TABLE IF NOT EXISTS dim_time (
    time_id             INTEGER PRIMARY KEY,    -- YYYYMMDD
    full_date           TEXT NOT NULL,
    year                INTEGER,
    quarter             INTEGER,
    month               INTEGER,
    month_name          TEXT,
    week_of_year        INTEGER
);

-- Dimension: Admitting hospital / specialty
CREATE TABLE IF NOT EXISTS dim_admission_type (
    admission_type_id   INTEGER PRIMARY KEY,
    admission_type      TEXT,                   -- Emergency, Elective, Urgent
    discharge_type      TEXT
);

-- Fact: One row per hospital admission
CREATE TABLE IF NOT EXISTS fact_admissions (
    admission_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id              INTEGER NOT NULL,
    diagnosis_id            INTEGER NOT NULL,
    admission_type_id       INTEGER,
    time_id                 INTEGER,

    -- Clinical measurements
    num_lab_procedures      INTEGER,
    num_procedures          INTEGER,
    num_medications         INTEGER,
    num_outpatient_visits   INTEGER,
    num_inpatient_visits    INTEGER,
    num_emergency_visits    INTEGER,
    time_in_hospital        INTEGER,            -- days

    -- Medication flags
    insulin_prescribed      TEXT,               -- 'Yes' / 'No' / 'Steady' / 'Up' / 'Down'
    diabetesMed_prescribed  TEXT,               -- 'Yes' / 'No'
    a1c_result              TEXT,               -- '>8', '>7', 'Norm', 'None'

    -- Target variable
    readmitted              TEXT NOT NULL,      -- '<30', '>30', 'NO'
    readmitted_within_30    INTEGER             -- 1 if <30, else 0 (derived)
);

-- Foreign key indexes for join performance
CREATE INDEX IF NOT EXISTS idx_fact_patient    ON fact_admissions(patient_id);
CREATE INDEX IF NOT EXISTS idx_fact_diagnosis  ON fact_admissions(diagnosis_id);
CREATE INDEX IF NOT EXISTS idx_fact_time       ON fact_admissions(time_id);
CREATE INDEX IF NOT EXISTS idx_fact_readmit    ON fact_admissions(readmitted_within_30);
