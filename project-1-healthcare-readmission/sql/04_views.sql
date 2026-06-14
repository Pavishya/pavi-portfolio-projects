-- ============================================================
-- Views — consumed by Python notebooks and Power BI
-- ============================================================

-- Summary view: one row per patient, aggregated risk profile
CREATE VIEW IF NOT EXISTS vw_patient_risk_summary AS
SELECT
    p.patient_id,
    p.age_group,
    p.gender,
    p.race,
    d.diag_category                                         AS primary_diag_category,
    COUNT(f.admission_id)                                   AS total_admissions,
    SUM(f.readmitted_within_30)                             AS readmit_30d_count,
    ROUND(100.0 * SUM(f.readmitted_within_30)
          / COUNT(f.admission_id), 2)                       AS patient_readmit_rate_pct,
    ROUND(AVG(f.time_in_hospital), 1)                       AS avg_los_days,
    ROUND(AVG(f.num_medications), 1)                        AS avg_medications,
    SUM(f.num_inpatient_visits)                             AS lifetime_inpatient_visits,
    MAX(CASE WHEN f.a1c_result = '>8' THEN 1 ELSE 0 END)   AS has_high_a1c,
    CASE
        WHEN SUM(f.readmitted_within_30) >= 2
             OR SUM(f.num_inpatient_visits) >= 5            THEN 'High'
        WHEN SUM(f.readmitted_within_30) = 1
             OR SUM(f.num_inpatient_visits) BETWEEN 2 AND 4 THEN 'Medium'
        ELSE                                                     'Low'
    END                                                     AS risk_tier
FROM fact_admissions f
JOIN dim_patient  p ON f.patient_id   = p.patient_id
JOIN dim_diagnosis d ON f.diagnosis_id = d.diagnosis_id
GROUP BY p.patient_id, p.age_group, p.gender, p.race, d.diag_category;


-- Aggregated view by diagnosis — feeds Power BI bar/map visuals
CREATE VIEW IF NOT EXISTS vw_readmission_by_diagnosis AS
SELECT
    d.diag_category,
    d.diag_code,
    COUNT(f.admission_id)                                           AS total_admissions,
    SUM(f.readmitted_within_30)                                     AS readmitted_30d,
    ROUND(100.0 * SUM(f.readmitted_within_30) / COUNT(*), 2)       AS readmit_rate_pct,
    ROUND(AVG(f.time_in_hospital), 1)                               AS avg_los,
    ROUND(AVG(f.num_medications), 1)                                AS avg_meds
FROM fact_admissions f
JOIN dim_diagnosis d ON f.diagnosis_id = d.diagnosis_id
GROUP BY d.diag_category, d.diag_code;


-- Medication analysis view — feeds Python statistical analysis
CREATE VIEW IF NOT EXISTS vw_medication_readmission AS
SELECT
    insulin_prescribed,
    diabetesMed_prescribed,
    a1c_result,
    COUNT(*)                                                        AS admissions,
    SUM(readmitted_within_30)                                       AS readmitted_30d,
    ROUND(100.0 * SUM(readmitted_within_30) / COUNT(*), 2)         AS readmit_rate_pct,
    ROUND(AVG(time_in_hospital), 1)                                 AS avg_los
FROM fact_admissions
GROUP BY insulin_prescribed, diabetesMed_prescribed, a1c_result
ORDER BY readmit_rate_pct DESC;
