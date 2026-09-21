from __future__ import annotations

import pandas as pd

from retail_analytics.clv import (
    build_customer_clv,
    clv_summary,
    cohort_survival_curve,
    projected_retention_multiplier,
)


def test_cohort_survival_projection_known_answer() -> None:
    retention = pd.DataFrame(
        {
            "months_since_acquisition": [0, 1, 2, 3],
            "retention_pct": [100.0, 50.0, 25.0, 25.0],
        }
    )

    curve = cohort_survival_curve(retention)

    assert curve.loc[0] == 1.0
    assert projected_retention_multiplier(0, curve, horizon_months=3) == 1.0
    assert projected_retention_multiplier(1, curve, horizon_months=2) == 1.0


def test_build_customer_clv_flags_slipping_high_value() -> None:
    customers = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "first_order_date": ["2020-01-01", "2020-01-01"],
            "last_order_date": ["2020-03-01", "2020-03-01"],
            "total_revenue": [120.0, 90.0],
            "tenure_days": [60, 60],
            "n_orders": [3, 2],
            "days_since_last_order": [200, 10],
            "segment": ["Can't Lose", "Champions"],
            "m_score": [5, 5],
        }
    )
    retention = pd.DataFrame(
        {
            "months_since_acquisition": [0, 1, 2, 3, 4],
            "retention_pct": [100.0, 50.0, 25.0, 25.0, 25.0],
        }
    )

    result = build_customer_clv(customers, retention, "2020-03-31", horizon_months=2)
    summary = clv_summary(result)

    slipping = result.loc[result["customer_id"] == 1].iloc[0]
    champion = result.loc[result["customer_id"] == 2].iloc[0]
    assert slipping["is_slipping_high_value"]
    assert slipping["revenue_at_stake"] > 0
    assert not champion["is_slipping_high_value"]
    assert champion["revenue_at_stake"] == 0
    assert summary["target_customers"] == 1
