-- Business question: how concentrated is revenue -- what share comes from
-- the top 5% / 10% / 20% of customers (a Pareto view)? Tells the retention
-- team how much revenue risk rides on a small group, i.e. where a retention
-- budget has the most leverage.

CREATE OR REPLACE VIEW revenue_concentration AS
WITH ranked AS (
    SELECT
        customer_id,
        total_revenue,
        RANK() OVER (ORDER BY total_revenue DESC) AS revenue_rank,
        SUM(total_revenue) OVER (
            ORDER BY total_revenue DESC ROWS UNBOUNDED PRECEDING
        ) AS cumulative_revenue,
        SUM(total_revenue) OVER () AS grand_total_revenue,
        COUNT(*) OVER () AS n_customers
    FROM customer_base
)
SELECT
    customer_id,
    total_revenue,
    revenue_rank,
    ROUND(100.0 * revenue_rank / n_customers, 4) AS cumulative_customer_pct,
    ROUND(100.0 * cumulative_revenue / grand_total_revenue, 2) AS cumulative_revenue_pct
FROM ranked
ORDER BY revenue_rank;

-- Convenience rollup: revenue share captured at standard Pareto thresholds.
CREATE OR REPLACE VIEW revenue_concentration_summary AS
SELECT 5 AS top_pct_of_customers, MAX(cumulative_revenue_pct) AS revenue_share_pct
FROM revenue_concentration WHERE cumulative_customer_pct <= 5
UNION ALL
SELECT 10, MAX(cumulative_revenue_pct)
FROM revenue_concentration WHERE cumulative_customer_pct <= 10
UNION ALL
SELECT 20, MAX(cumulative_revenue_pct)
FROM revenue_concentration WHERE cumulative_customer_pct <= 20
ORDER BY top_pct_of_customers;
