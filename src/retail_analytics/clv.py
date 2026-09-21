"""Transparent customer-value helpers for the retail analytics case."""

from __future__ import annotations

import numpy as np
import pandas as pd


def cohort_survival_curve(cohort_retention: pd.DataFrame) -> pd.Series:
    """Average observed retention by month since acquisition.

    Month 0 is always acquisition month. Later months are cohort-level active
    shares. The returned values are proportions, not percentages.
    """
    curve = (
        cohort_retention.groupby("months_since_acquisition")["retention_pct"]
        .mean()
        .sort_index()
        .div(100.0)
    )
    if 0 not in curve.index:
        curve.loc[0] = 1.0
        curve = curve.sort_index()
    return curve.clip(lower=0.0, upper=1.0)


def projected_retention_multiplier(
    customer_age_months: int,
    survival_curve: pd.Series,
    horizon_months: int = 12,
) -> float:
    """Expected active-month multiplier for the next horizon.

    The projection is conditional on being in the file at the snapshot date:
    future survival at age t+h is divided by observed survival at age t. If the
    curve is shorter than the requested horizon, the last observed rate is used.
    """
    if horizon_months <= 0:
        return 0.0
    max_age = int(survival_curve.index.max())
    current_age = min(max(customer_age_months, 0), max_age)
    current_survival = max(float(survival_curve.loc[current_age]), 1e-9)
    multiplier = 0.0
    for step in range(1, horizon_months + 1):
        future_age = min(current_age + step, max_age)
        future_survival = float(survival_curve.loc[future_age])
        multiplier += min(future_survival / current_survival, 1.0)
    return float(multiplier)


def build_customer_clv(
    customer_segments: pd.DataFrame,
    cohort_retention: pd.DataFrame,
    snapshot_date,
    horizon_months: int = 12,
) -> pd.DataFrame:
    """Add historical value, cohort-projected 12-month value, and target flag."""
    required = {
        "customer_id",
        "first_order_date",
        "last_order_date",
        "total_revenue",
        "tenure_days",
        "n_orders",
        "segment",
        "m_score",
    }
    missing = required.difference(customer_segments.columns)
    if missing:
        raise ValueError(f"customer_segments missing columns: {sorted(missing)}")

    snapshot = pd.Timestamp(snapshot_date)
    curve = cohort_survival_curve(cohort_retention)
    df = customer_segments.copy()
    df["first_order_date"] = pd.to_datetime(df["first_order_date"])
    df["last_order_date"] = pd.to_datetime(df["last_order_date"])
    df["age_months"] = (
        (snapshot.year - df["first_order_date"].dt.year) * 12
        + (snapshot.month - df["first_order_date"].dt.month)
    ).clip(lower=0)
    df["observed_months"] = (df["tenure_days"].clip(lower=0) / 30.4375 + 1).clip(lower=1)
    df["historical_value"] = df["total_revenue"].round(2)
    df["monthly_value"] = df["historical_value"] / df["observed_months"]
    df["retention_multiplier_12m"] = df["age_months"].apply(
        lambda age: projected_retention_multiplier(int(age), curve, horizon_months)
    )
    df["projected_12m_value"] = (df["monthly_value"] * df["retention_multiplier_12m"]).round(2)
    df["transparent_clv_12m"] = (df["historical_value"] + df["projected_12m_value"]).round(2)
    df["is_slipping_high_value"] = (
        df["segment"].isin(["Can't Lose", "At Risk"]) & (df["m_score"] >= 4)
    )
    df["revenue_at_stake"] = np.where(df["is_slipping_high_value"], df["projected_12m_value"], 0.0)
    return df.sort_values(["revenue_at_stake", "historical_value"], ascending=False)


def clv_summary(customer_clv: pd.DataFrame) -> dict[str, float]:
    """Small KPI dictionary for docs, memo, and dashboard."""
    target = customer_clv[customer_clv["is_slipping_high_value"]]
    return {
        "target_customers": int(len(target)),
        "revenue_at_stake": float(target["revenue_at_stake"].sum().round(2)),
        "historical_value": float(target["historical_value"].sum().round(2)),
        "avg_days_since_last_order": float(target["days_since_last_order"].mean().round(1)),
    }
