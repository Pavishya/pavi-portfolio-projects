-- ============================================================
-- Analytical Queries — Personal Finance Dashboard
-- Showcases: GROUP BY, LAG(), budget variance, conditional agg
-- ============================================================


-- -------------------------------------------------------
-- Q1: Monthly spend by category (feeds Tableau stacked bar)
-- -------------------------------------------------------
SELECT
    month,
    category,
    ROUND(SUM(amount), 2)   AS total_spend,
    COUNT(*)                AS transaction_count
FROM transactions
WHERE type = 'debit'
GROUP BY month, category
ORDER BY month, total_spend DESC;


-- -------------------------------------------------------
-- Q2: Budget vs Actual variance with status flag
--     Skills: JOIN, ROUND, CASE, derived columns
-- -------------------------------------------------------
SELECT
    t.month,
    t.category,
    ROUND(SUM(t.amount), 2)                                     AS actual_spend,
    b.budget_amount,
    ROUND(SUM(t.amount) - b.budget_amount, 2)                   AS variance_amount,
    ROUND((SUM(t.amount) - b.budget_amount)
          / b.budget_amount * 100, 1)                           AS variance_pct,
    CASE
        WHEN SUM(t.amount) > b.budget_amount * 1.1  THEN 'Over Budget'
        WHEN SUM(t.amount) < b.budget_amount * 0.9  THEN 'Under Budget'
        ELSE                                              'On Track'
    END                                                         AS budget_status
FROM transactions t
JOIN monthly_budgets b
    ON t.month = b.month AND t.category = b.category
WHERE t.type = 'debit'
GROUP BY t.month, t.category, b.budget_amount
ORDER BY t.month, variance_pct DESC;


-- -------------------------------------------------------
-- Q3: Month-over-month spend change per category
--     Skills: LAG() window function, CTE
-- -------------------------------------------------------
WITH monthly_category AS (
    SELECT
        month,
        category,
        ROUND(SUM(amount), 2) AS monthly_spend
    FROM transactions
    WHERE type = 'debit'
    GROUP BY month, category
)
SELECT
    month,
    category,
    monthly_spend,
    LAG(monthly_spend) OVER (PARTITION BY category ORDER BY month)  AS prev_month_spend,
    ROUND(
        monthly_spend
        - LAG(monthly_spend) OVER (PARTITION BY category ORDER BY month)
    , 2)                                                            AS mom_change,
    ROUND(
        100.0 * (monthly_spend
        - LAG(monthly_spend) OVER (PARTITION BY category ORDER BY month))
        / NULLIF(LAG(monthly_spend) OVER (PARTITION BY category ORDER BY month), 0)
    , 1)                                                            AS mom_change_pct
FROM monthly_category
ORDER BY category, month;


-- -------------------------------------------------------
-- Q4: Savings rate by month
--     Skills: conditional aggregation, CASE, derived column
-- -------------------------------------------------------
SELECT
    month,
    ROUND(SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END), 2) AS income,
    ROUND(SUM(CASE WHEN type = 'debit'  THEN amount ELSE 0 END), 2) AS total_spend,
    ROUND(
        SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END)
        - SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END)
    , 2)                                                             AS net_savings,
    ROUND(
        100.0 * (
            SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END)
            - SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END)
        ) / NULLIF(SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END), 0)
    , 1)                                                             AS savings_rate_pct
FROM transactions
GROUP BY month
ORDER BY month;


-- -------------------------------------------------------
-- Q5: Top merchants by annual spend (with rank)
--     Skills: RANK() OVER, aggregate, window function
-- -------------------------------------------------------
WITH merchant_totals AS (
    SELECT
        merchant,
        category,
        ROUND(SUM(amount), 2)   AS annual_spend,
        COUNT(*)                AS transaction_count
    FROM transactions
    WHERE type = 'debit'
    GROUP BY merchant, category
)
SELECT
    merchant,
    category,
    annual_spend,
    transaction_count,
    RANK() OVER (ORDER BY annual_spend DESC)            AS spend_rank,
    RANK() OVER (PARTITION BY category ORDER BY annual_spend DESC) AS rank_within_category
FROM merchant_totals
ORDER BY spend_rank
LIMIT 20;
