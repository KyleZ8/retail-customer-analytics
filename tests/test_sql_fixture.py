from __future__ import annotations

from retail_analytics.engine import FIXTURE_CSV, build_connection


def test_cleaning_rules_on_fixture() -> None:
    con = build_connection(FIXTURE_CSV)

    summary = {
        row["removal_reason"]: row["n_rows"]
        for row in con.sql("SELECT removal_reason, n_rows FROM removed_rows_summary").df().to_dict(
            "records"
        )
    }

    assert summary == {
        "kept": 2500,
        "cancelled_invoice": 204,
        "missing_customer_id": 150,
        "non_product_stock_code": 140,
    }
    clean = con.sql(
        """
        SELECT
            COUNT(*) AS n_rows,
            ROUND(SUM(revenue), 2) AS revenue,
            COUNT(DISTINCT customer_id) AS customers,
            SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customers,
            SUM(CASE WHEN revenue <= 0 THEN 1 ELSE 0 END) AS non_positive_revenue
        FROM transactions_clean
        """
    ).fetchone()
    assert clean == (2500, 53427.58, 1427, 0, 0)


def test_rfm_scores_known_customers() -> None:
    con = build_connection(FIXTURE_CSV)
    rows = con.sql(
        """
        SELECT customer_id, days_since_last_order, frequency, monetary, r_score, f_score, m_score,
               rfm_total
        FROM rfm_scores
        WHERE customer_id IN (12360, 12368, 12388)
        ORDER BY customer_id
        """
    ).fetchall()

    assert rows == [
        (12360, 392, 2, 32.16, 2, 4, 4, 10),
        (12368, 628, 1, 72.5, 1, 1, 5, 7),
        (12388, 148, 2, 47.0, 4, 4, 5, 13),
    ]


def test_segment_and_cohort_known_answers() -> None:
    con = build_connection(FIXTURE_CSV)

    segment_counts = {
        segment: n_customers
        for segment, n_customers in con.sql(
            "SELECT segment, n_customers FROM rfm_segment_summary"
        ).fetchall()
    }
    assert segment_counts["Champions"] == 195
    assert segment_counts["Can't Lose"] == 74
    assert segment_counts["Hibernating"] == 276

    cohort = con.sql(
        """
        SELECT cohort_size, active_customers, retention_pct
        FROM cohort_retention
        WHERE cohort_month = DATE '2009-12-01'
          AND months_since_acquisition = 1
        """
    ).fetchone()
    assert cohort == (87, 11, 12.64)
