-- Business question: how should the retention/CRM team segment customers by
-- Recency, Frequency, and Monetary value? NTILE(5) quintiles are the
-- standard RFM scoring convention: 5 = best (most recent / most frequent /
-- highest spend), 1 = worst. Recency is ordered DESC (largest
-- days-since-last-order first) so that quintile 5 lands on the SMALLEST
-- days-since-last-order, i.e. the most recent buyers -- otherwise a plain
-- ascending NTILE would score "hasn't bought in a year" as best.

CREATE OR REPLACE VIEW rfm_scores AS
SELECT
    customer_id,
    days_since_last_order,
    n_orders AS frequency,
    total_revenue AS monetary,
    NTILE(5) OVER (ORDER BY days_since_last_order DESC, customer_id ASC) AS r_score,
    NTILE(5) OVER (ORDER BY n_orders ASC, customer_id ASC) AS f_score,
    NTILE(5) OVER (ORDER BY total_revenue ASC, customer_id ASC) AS m_score,
    NTILE(5) OVER (ORDER BY days_since_last_order DESC, customer_id ASC)
        + NTILE(5) OVER (ORDER BY n_orders ASC, customer_id ASC)
        + NTILE(5) OVER (ORDER BY total_revenue ASC, customer_id ASC) AS rfm_total
FROM customer_base;
