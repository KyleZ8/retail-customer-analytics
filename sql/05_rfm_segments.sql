-- Business question: what marketing-friendly segment should each customer
-- receive from the RFM quintiles? These are deliberately simple SQL rules so
-- a CRM lead can explain and operationalize the list without a model serving
-- layer. They complement, rather than replace, the raw r/f/m scores.

CREATE OR REPLACE VIEW rfm_segments AS
SELECT
    customer_id,
    days_since_last_order,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 4 THEN 'Loyal'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'Promising'
        WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'Can''t Lose'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
        WHEN r_score = 3 THEN 'Need Attention'
        ELSE 'Potential Loyalist'
    END AS segment
FROM rfm_scores;

CREATE OR REPLACE VIEW rfm_segment_summary AS
SELECT
    segment,
    COUNT(*) AS n_customers,
    ROUND(SUM(monetary), 2) AS revenue,
    ROUND(AVG(monetary), 2) AS avg_customer_revenue,
    ROUND(AVG(days_since_last_order), 1) AS avg_days_since_last_order,
    ROUND(AVG(frequency), 1) AS avg_orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS customer_pct,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS revenue_pct
FROM rfm_segments
GROUP BY segment
ORDER BY revenue DESC;
