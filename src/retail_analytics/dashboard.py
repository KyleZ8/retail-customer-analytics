"""Build aggregate exports and a self-contained Plotly dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.offline.offline import get_plotlyjs

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def write_aggregate_exports(
    *,
    segment_summary: pd.DataFrame,
    cohort_retention: pd.DataFrame,
    revenue_concentration: pd.DataFrame,
    revenue_at_risk_by_segment: pd.DataFrame,
    kpis: dict[str, float],
    root: Path = PROJECT_ROOT,
) -> None:
    """Write small aggregate CSVs for Tableau and dashboard reuse."""
    tableau_dir = root / "tableau"
    outputs_dir = root / "outputs"
    tableau_dir.mkdir(exist_ok=True)
    outputs_dir.mkdir(exist_ok=True)

    segment_export = segment_summary.rename(
        columns={
            "revenue": "revenue_gbp",
            "avg_customer_revenue": "avg_customer_revenue_gbp",
        }
    )
    risk_export = revenue_at_risk_by_segment.rename(
        columns={
            "historical_value": "historical_value_gbp",
            "projected_12m_value": "projected_12m_value_gbp",
            "revenue_at_stake": "revenue_at_stake_gbp",
        }
    )

    segment_export.to_csv(tableau_dir / "segment_summary.csv", index=False)
    cohort_retention.to_csv(tableau_dir / "cohort_retention.csv", index=False)
    revenue_concentration.to_csv(tableau_dir / "revenue_concentration.csv", index=False)
    risk_export.to_csv(tableau_dir / "revenue_at_risk_by_segment.csv", index=False)
    pd.DataFrame([kpis]).to_csv(outputs_dir / "kpi_summary.csv", index=False)


def _figure_div(fig: go.Figure) -> str:
    return plot(fig, output_type="div", include_plotlyjs=False)


def build_dashboard_html(
    *,
    kpis: dict[str, float],
    segment_summary: pd.DataFrame,
    cohort_retention: pd.DataFrame,
    revenue_concentration: pd.DataFrame,
    revenue_at_risk_by_segment: pd.DataFrame,
) -> str:
    """Return a self-contained dashboard page using aggregate data only."""
    segment_fig = go.Figure(
        data=[
            go.Bar(
                x=segment_summary["segment"],
                y=segment_summary["revenue"],
                marker_color="#1f77b4",
                text=segment_summary["revenue_pct"].round(1).astype(str) + "%",
                textposition="outside",
            )
        ]
    )
    segment_fig.update_layout(
        title="Revenue by RFM Segment",
        xaxis_title="Segment",
        yaxis_title="Revenue (GBP)",
        margin=dict(t=60, l=60, r=30, b=90),
    )

    pareto_fig = go.Figure()
    pareto_fig.add_trace(
        go.Scatter(
            x=revenue_concentration["cumulative_customer_pct"],
            y=revenue_concentration["cumulative_revenue_pct"],
            mode="lines",
            name="Cumulative revenue",
        )
    )
    pareto_fig.update_layout(
        title="Revenue Concentration",
        xaxis_title="Cumulative customers (%)",
        yaxis_title="Cumulative revenue (%)",
        margin=dict(t=60, l=60, r=30, b=60),
    )

    heatmap = cohort_retention.pivot_table(
        index="cohort_month",
        columns="months_since_acquisition",
        values="retention_pct",
        aggfunc="mean",
    ).sort_index()
    cohort_fig = go.Figure(
        data=[
            go.Heatmap(
                z=heatmap.values,
                x=[str(c) for c in heatmap.columns],
                y=[str(pd.Timestamp(i).date())[:7] for i in heatmap.index],
                colorscale="Blues",
                colorbar_title="Retention %",
            )
        ]
    )
    cohort_fig.update_layout(
        title="Cohort Retention",
        xaxis_title="Months since acquisition",
        yaxis_title="Cohort",
        margin=dict(t=60, l=80, r=30, b=60),
    )

    risk_fig = go.Figure(
        data=[
            go.Bar(
                x=revenue_at_risk_by_segment["segment"],
                y=revenue_at_risk_by_segment["revenue_at_stake"],
                marker_color="#d62728",
            )
        ]
    )
    risk_fig.update_layout(
        title="Projected Revenue at Stake",
        xaxis_title="Segment",
        yaxis_title="12-month revenue at stake (GBP)",
        margin=dict(t=60, l=70, r=30, b=80),
    )

    segment_table = segment_summary.copy()
    for col in ["revenue", "avg_customer_revenue"]:
        segment_table[col] = segment_table[col].map(lambda v: f"£{v:,.0f}")
    segment_table["customer_pct"] = segment_table["customer_pct"].map(lambda v: f"{v:.1f}%")
    segment_table["revenue_pct"] = segment_table["revenue_pct"].map(lambda v: f"{v:.1f}%")

    table_fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=list(segment_table.columns), fill_color="#eef2f7", align="left"),
                cells=dict(
                    values=[segment_table[col] for col in segment_table.columns],
                    fill_color="white",
                    align="left",
                ),
            )
        ]
    )
    table_fig.update_layout(title="Segment Table", margin=dict(t=50, l=10, r=10, b=10))

    tiles = [
        ("Customers", f"{int(kpis['n_customers']):,}"),
        ("Clean Revenue", f"£{kpis['total_revenue']:,.0f}"),
        ("Top 10% Revenue Share", f"{kpis['top_10_revenue_share']:.1f}%"),
        ("Revenue at Stake", f"£{kpis['revenue_at_stake']:,.0f}"),
    ]
    tile_html = "".join(
        f"<section class='tile'><div>{label}</div><strong>{value}</strong></section>"
        for label, value in tiles
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Retail Customer Analytics Dashboard</title>
  <script>{get_plotlyjs()}</script>
  <style>
    body {{
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      background: #f7f8fa;
      color: #172033;
    }}
    header {{
      padding: 28px 32px 16px;
      background: #ffffff;
      border-bottom: 1px solid #dfe4ea;
    }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    p {{ margin: 0; color: #53616f; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 24px; }}
    .tiles {{
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .tile {{ background: #fff; border: 1px solid #dfe4ea; border-radius: 8px; padding: 16px; }}
    .tile div {{ color: #53616f; font-size: 13px; }}
    .tile strong {{ display: block; margin-top: 8px; font-size: 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }}
    .panel {{ background: #fff; border: 1px solid #dfe4ea; border-radius: 8px; padding: 8px; }}
    .wide {{ grid-column: 1 / -1; }}
    @media (max-width: 800px) {{ .tiles, .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Retail Customer Analytics</h1>
    <p>SQL-cleaned RFM, cohort retention, CLV, and revenue-at-risk aggregates.</p>
  </header>
  <main>
    <div class="tiles">{tile_html}</div>
    <div class="grid">
      <section class="panel">{_figure_div(segment_fig)}</section>
      <section class="panel">{_figure_div(pareto_fig)}</section>
      <section class="panel wide">{_figure_div(cohort_fig)}</section>
      <section class="panel">{_figure_div(risk_fig)}</section>
      <section class="panel">{_figure_div(table_fig)}</section>
    </div>
  </main>
</body>
</html>
"""


def write_dashboard(html: str, root: Path = PROJECT_ROOT) -> None:
    dashboard_dir = root / "dashboard"
    docs_dir = root / "docs"
    dashboard_dir.mkdir(exist_ok=True)
    docs_dir.mkdir(exist_ok=True)
    (dashboard_dir / "index.html").write_text(html)
    (docs_dir / "index.html").write_text(html)
