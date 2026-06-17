# Dashboard patterns — the Debt Management surface

## The Debt Management dashboard (the first consumer, per the Blueprint)

Panels:
- **Aged balances by band** — `total_outstanding` by `ageing_band` (0–30 / 31–60 / 61–90 / 90+). Bar.
- **Risk-ranked debtor list** — top debtors by balance (and risk band once SAS scores land). Table.
- **Collection performance** — collected vs outstanding over time, from `mart_debt__collection_performance`. Line.
- **Instalment monitoring** — instalment plans on track vs in arrears. Table / big-number.
- **Outstanding KPI** — `total_outstanding` headline. Big number.

These reuse one dataset over `mart_debt__aged_balances` (+ a second over the collection mart). Every
panel reads the dataset's metrics, so the number on the KPI tile and the number in the bar chart can't
disagree.

## Standard debt metrics (define once on the dataset)

| Metric / calc | Expression | Kind |
|---|---|---|
| `total_outstanding` | `sum(balance)` | metric |
| `debtor_count` | `count(distinct taxpayer_id)` | metric |
| `debt_to_assessment` | `balance / nullif(assessment_total, 0)` | calculated column |
| `ageing_band` | bucket of days-overdue (0–30/31–60/61–90/90+) | usually built in the mart |
| `avg_days_overdue` | `avg(days_overdue)` | metric |

Ageing bands belong in the mart (so every consumer sees the same buckets); the dashboard just groups
by the `ageing_band` column. Keep band boundaries in one place — the mart — not in chart filters.

## RBAC (Restricted-by-default)

- Map `rbac_roles` to Superset roles; debt data is Restricted, so the dashboard is visible only to the
  debt roles, not "all users".
- Use row-level security if officers should see only their assigned portfolio.
- This mirrors the platform's classification: the consumption surface inherits the data's
  classification, it doesn't relax it.

## Alerts

Each alert in the manifest becomes a Superset Alert: it runs the metric on a schedule and notifies when
the condition/threshold is met (e.g. the 90+ ageing band's `total_outstanding` grows past a threshold,
or a freshness/coverage check fails). Declared alerts beat a human remembering to look.

## One dataset, many consumers

The dataset + its metrics are the **single semantic surface** over the mart. The same definitions feed:
- the **Superset dashboard** (this skill),
- the **API** the DMBB/Joget workflow calls (`expose-api` reads the same mart/fields),
- the **SAS** consumer (reads the Gold mart for risk analytics).

So define a metric here and it means the same thing everywhere. If a new consumer needs a new metric,
add it to the dataset (or the mart), not to a private copy — that's the `onboard-consumer` pattern.

## Don't hand-roll a charting front-end

Charts read **server-side SQL via the dataset** — never a custom Chart.js/HTML page that scrapes
rendered data or embeds its own queries. The dataset is the contract; Superset renders it. (This is the
anti-pattern the sister project hit and corrected.)
