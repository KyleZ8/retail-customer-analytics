-- Business question: of the customers acquired (first order) in a given
-- month, what share are still buying N months later? This is the direct
-- answer to "who is slipping away" -- a retention matrix by acquisition
-- cohort, the standard CRM lens for subscription/repeat-purchase health.

CREATE OR REPLACE VIEW cohort_retention AS
WITH cohorts AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', first_order_date) AS cohort_month,
        COUNT(*) OVER (PARTITION BY DATE_TRUNC('month', first_order_date)) AS cohort_size
    FROM customer_base
),
activity AS (
    SELECT DISTINCT
        customer_id,
        DATE_TRUNC('month', invoice_date) AS activity_month
    FROM transactions_clean
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        c.cohort_size,
        DATE_DIFF('month', c.cohort_month, a.activity_month) AS months_since_acquisition,
        a.customer_id
    FROM cohorts c
    JOIN activity a ON a.customer_id = c.customer_id
    WHERE a.activity_month >= c.cohort_month
)
SELECT
    cohort_month,
    months_since_acquisition,
    cohort_size,
    COUNT(DISTINCT customer_id) AS active_customers,
    ROUND(100.0 * COUNT(DISTINCT customer_id) / cohort_size, 2) AS retention_pct
FROM cohort_activity
GROUP BY cohort_month, months_since_acquisition, cohort_size
ORDER BY cohort_month, months_since_acquisition;
