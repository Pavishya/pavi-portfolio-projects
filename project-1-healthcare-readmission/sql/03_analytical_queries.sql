-- ============================================================
-- Analytical Queries — Healthcare Readmission Risk
-- Showcases: CTEs, window functions, subqueries, CASE, JOINs
-- ============================================================


-- -------------------------------------------------------
-- Q1: Readmission rate by diagnosis category
--     Skills: GROUP BY, CASE, ROUND, aggregate functions
-- -------------------------------------------------------
SELECT
    d.diag_category,
    COUNT(*)                                                        AS total_admissions,
    SUM(f.readmitted_within_30)                                     AS readmitted_count,
    ROUND(100.0 * SUM(f.readmitted_within_30) / COUNT(*), 2)       AS readmission_rate_pct
FROM fact_admissions f
JOIN dim_diagnosis d ON f.diagnosis_id = d.diagnosis_id
GROUP BY d.diag_category
ORDER BY readmission_rate_pct DESC;


-- -------------------------------------------------------
-- Q2: Patient risk ranking by prior inpatient visits
--     Skills: Window function RANK() OVER, CTE
-- -------------------------------------------------------
WITH patient_history AS (
    SELECT
        p.patient_id,
        p.age_group,
        p.gender,
        SUM(f.num_inpatient_visits)     AS total_prior_inpatient,
        SUM(f.num_emergency_visits)     AS total_emergency,
        SUM(f.readmitted_within_30)     AS times_readmitted_30
    FROM fact_admissions f
    JOIN dim_patient p ON f.patient_id = p.patient_id
    GROUP BY p.patient_id, p.age_group, p.gender
)
SELECT
    patient_id,
    age_group,
    gender,
    total_prior_inpatient,
    total_emergency,
    times_readmitted_30,
    RANK() OVER (ORDER BY total_prior_inpatient DESC)   AS inpatient_risk_rank,
    RANK() OVER (ORDER BY times_readmitted_30 DESC)     AS readmit_frequency_rank
FROM patient_history
ORDER BY inpatient_risk_rank
LIMIT 50;


-- -------------------------------------------------------
-- Q3: Month-over-month readmission trend
--     Skills: Window LAG(), date grouping, derived columns
-- -------------------------------------------------------
WITH monthly_stats AS (
    SELECT
        t.year,
        t.month,
        t.month_name,
        COUNT(*)                                            AS total_admissions,
        SUM(f.readmitted_within_30)                         AS readmissions_30d
    FROM fact_admissions f
    JOIN dim_time t ON f.time_id = t.time_id
    GROUP BY t.year, t.month, t.month_name
)
SELECT
    year,
    month,
    month_name,
    total_admissions,
    readmissions_30d,
    ROUND(100.0 * readmissions_30d / total_admissions, 2)           AS readmit_rate_pct,
    LAG(readmissions_30d) OVER (ORDER BY year, month)               AS prev_month_readmissions,
    readmissions_30d - LAG(readmissions_30d) OVER (ORDER BY year, month) AS mom_change
FROM monthly_stats
ORDER BY year, month;


-- -------------------------------------------------------
-- Q4: High-risk patient cohort using chained CTEs
--     Skills: Multi-level CTE, EXISTS, complex filtering
-- -------------------------------------------------------
WITH admission_profile AS (
    SELECT
        f.patient_id,
        f.time_in_hospital,
        f.num_medications,
        f.num_inpatient_visits,
        f.readmitted_within_30,
        d.diag_category,
        p.age_group
    FROM fact_admissions f
    JOIN dim_diagnosis d ON f.diagnosis_id = d.diagnosis_id
    JOIN dim_patient p   ON f.patient_id   = p.patient_id
),
risk_scores AS (
    SELECT
        patient_id,
        age_group,
        diag_category,
        AVG(time_in_hospital)           AS avg_los,
        AVG(num_medications)            AS avg_meds,
        SUM(num_inpatient_visits)       AS total_inpatient,
        SUM(readmitted_within_30)       AS readmit_count,
        -- Composite risk: weighted combination of factors
        ROUND(
            (AVG(time_in_hospital) * 0.3)
            + (AVG(num_medications) * 0.2)
            + (SUM(num_inpatient_visits) * 0.3)
            + (SUM(readmitted_within_30) * 2.0)
        , 2) AS composite_risk_score
    FROM admission_profile
    GROUP BY patient_id, age_group, diag_category
)
SELECT *
FROM risk_scores
WHERE composite_risk_score > 5
ORDER BY composite_risk_score DESC
LIMIT 100;


-- -------------------------------------------------------
-- Q5: Insulin impact on readmission — A/B style comparison
--     Skills: Subquery, conditional aggregation, CASE
-- -------------------------------------------------------
SELECT
    insulin_prescribed,
    COUNT(*)                                                            AS admissions,
    SUM(readmitted_within_30)                                           AS readmitted_30d,
    ROUND(100.0 * SUM(readmitted_within_30) / COUNT(*), 2)             AS readmit_rate_pct,
    ROUND(AVG(time_in_hospital), 1)                                     AS avg_los_days,
    ROUND(AVG(num_medications), 1)                                      AS avg_medications,
    -- Compare each group's rate against overall average
    ROUND(
        100.0 * SUM(readmitted_within_30) / COUNT(*)
        - (SELECT 100.0 * SUM(readmitted_within_30) / COUNT(*) FROM fact_admissions)
    , 2) AS vs_overall_avg_pct
FROM fact_admissions
WHERE insulin_prescribed IN ('Yes', 'No', 'Steady', 'Up', 'Down')
GROUP BY insulin_prescribed
ORDER BY readmit_rate_pct DESC;


-- -------------------------------------------------------
-- Q6: Length-of-stay percentile bands
--     Skills: NTILE window function, CTE, percentile banding
-- -------------------------------------------------------
WITH los_bands AS (
    SELECT
        admission_id,
        patient_id,
        time_in_hospital,
        readmitted_within_30,
        NTILE(4) OVER (ORDER BY time_in_hospital)   AS los_quartile
    FROM fact_admissions
)
SELECT
    CASE los_quartile
        WHEN 1 THEN 'Q1: Short stay (1-3 days)'
        WHEN 2 THEN 'Q2: Below average (3-5 days)'
        WHEN 3 THEN 'Q3: Above average (5-8 days)'
        WHEN 4 THEN 'Q4: Long stay (8+ days)'
    END                                                                 AS los_band,
    COUNT(*)                                                            AS patients,
    ROUND(AVG(time_in_hospital), 1)                                     AS avg_los,
    ROUND(100.0 * SUM(readmitted_within_30) / COUNT(*), 2)             AS readmit_rate_pct
FROM los_bands
GROUP BY los_quartile
ORDER BY los_quartile;
