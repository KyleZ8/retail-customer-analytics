-- Business question: what does each customer's basic transaction footprint
-- look like -- when did they first/last buy, how many orders, how much
-- revenue, how long have they been a customer? This is the base table every
-- other view (RFM, cohorts, Pareto) builds on. Assumes transactions_clean
-- exists (see 00_clean.sql).

CREATE OR REPLACE VIEW customer_base AS
SELECT
    customer_id,
    MIN(invoice_date) AS first_order_date,
    MAX(invoice_date) AS last_order_date,
    COUNT(DISTINCT invoice) AS n_orders,
    COUNT(*) AS n_line_items,
    SUM(revenue) AS total_revenue,
    DATE_DIFF('day', MIN(invoice_date), MAX(invoice_date)) AS tenure_days,
    DATE_DIFF(
        'day', MAX(invoice_date), (SELECT MAX(invoice_date) FROM transactions_clean)
    ) AS days_since_last_order
FROM transactions_clean
GROUP BY customer_id;
