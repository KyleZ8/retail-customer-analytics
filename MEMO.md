# CRM Retention Recommendation

## Recommendation

Prioritize a save campaign for **335 high-value customers** in the **Can't Lose** and **At Risk** RFM segments. These customers have strong historical spend but weak recent activity. The transparent 12-month cohort projection estimates **$1,999,052** of revenue at stake.

## Who to Target

| Segment | Target customers | Historical value | 12-month revenue at stake | Avg. days since last order |
|---|---:|---:|---:|---:|
| Can't Lose | 232 | $966,514 | $1,246,714 | 340.2 |
| At Risk | 103 | $329,675 | $752,339 | 382.0 |

Champions and Loyal customers should receive lower-cost loyalty messaging, but the incremental retention budget should go first to the slipping high-value group. Hibernating customers are numerous, but their expected return is lower.

## Budget Logic

Use the targeting list in `outputs/revenue_at_risk_targeting_list.csv`, ranked by `revenue_at_stake`. A practical starting point is to cap the incentive and contact cost well below the protected revenue estimate for each customer. For example, a 10% reinvestment cap implies a working budget ceiling of about **$199,905** against the **$1,999,052** at stake.

## Measurement

Run a holdout test before scaling:

- Randomly assign eligible customers within segment and value bands to treatment and holdout.
- Track 90-day repeat purchase rate, revenue per customer, margin after incentive cost, and unsubscribe/complaint rate.
- Declare success only if treatment produces incremental profit net of campaign cost, not just higher gross revenue.
- Refresh the RFM and CLV list monthly; customers who reactivate should move out of the save campaign and into loyalty messaging.
