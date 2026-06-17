---
name: build-superset-dashboard
description: >-
  Build the Superset consumption surface over a Gold mart — a dataset (the SQL the dashboard reads,
  with calculated columns and reusable metrics defined ONCE) plus a dashboard manifest (charts, RBAC
  roles, threshold alerts). Use this WHENEVER the work is to build, change, or wire a dashboard,
  chart, KPI tile, or metric for a consumer: "build the Debt Management dashboard", "add a chart for
  aged balances", "define the debt-to-assessment metric", "make a KPI tile", "show the risk-ranked
  debtor list", "set up an alert when the 90+ band grows", "dashboard over this mart". Trigger even
  when the user just describes a view they want over Gold data — the dataset-with-metrics pattern
  (one definition reused by every chart) IS the method, and per-chart raw SQL is the drift this
  prevents. The Debt dashboard is the first; the pattern is reused by every later consumer.
  Cross-platform, pure Python.
---

# Build a Superset dashboard (the consumption surface)

This is the last mile: turning a gated Gold mart into the dashboard the Debt Management team and the
DMBB workflow actually use. It generates two things from one spec:

1. a **Superset dataset** — the virtual dataset (SQL over the mart) plus **calculated columns** and
   **metrics** defined *once* on the dataset, and
2. a **dashboard manifest** — the charts, the RBAC roles, and the threshold alerts.

The reason metrics live on the dataset (not in each chart's SQL): `total_outstanding`,
`debt_to_assessment`, the ageing bands — defined once, every chart uses the same definition, and so
does the API and SAS. A metric that's redefined per chart drifts; one semantic definition is the
Blueprint rule ("one semantic definition, reused everywhere").

## Workflow

### 1 — Write the dashboard spec

```yaml
dashboard: Debt Management
dataset:
  name: debt_aged_balances
  mart: mart_debt__aged_balances          # the Gold mart (schema defaults to gold)
  columns: [taxpayer_id, taxpayer_name, balance, ageing_band, assessment_total]
  calculated:                              # row-level expressions
    - {name: debt_to_assessment, expression: "balance / nullif(assessment_total, 0)", description: "Debt-to-assessment ratio"}
  metrics:                                 # aggregate metrics, reused by every chart
    - {name: total_outstanding, expression: "sum(balance)", description: "Total outstanding debt"}
    - {name: debtor_count, expression: "count(distinct taxpayer_id)"}
charts:
  - {name: Aged balances by band, type: bar, dataset: debt_aged_balances, metric: total_outstanding, dimension: ageing_band}
  - {name: Top debtors, type: table, dataset: debt_aged_balances, columns: [taxpayer_name, balance, ageing_band]}
  - {name: Outstanding, type: big_number, dataset: debt_aged_balances, metric: total_outstanding}
rbac:
  roles: [debt_officer, debt_manager]
alerts:
  - {name: ageing shift, dataset: debt_aged_balances, metric: total_outstanding, condition: ">", threshold: 1000000, note: "alert if 90+ band grows"}
```
Multiple datasets are allowed (`dataset:` may be a list). Chart `type` ∈ `bar | line | table |
big_number | pie | area`.

### 2 — Generate

```bash
python3 scripts/gen_superset.py --spec dashboard.yml --repo <repo-root>   # writes the assets
python3 scripts/gen_superset.py --spec dashboard.yml --print              # review first
```
Writes `consumption/dashboards/<slug>/dataset_<name>.yaml` (Superset import shape — the dataset, with
calculated columns + metrics) and `dashboard.yaml` (the chart/RBAC/alert manifest). Pure standard
library.

### 3 — Import, lay out, secure, alert

Import the dataset YAML into Superset (set the real `database_uuid` on import — it's a placeholder).
Build each chart in Superset from the manifest's definitions (chart layouts are positional and are
best assembled in the UI; the manifest gives you every chart's dataset, metric, dimension and
columns). Apply the `rbac_roles` as Superset roles / row-level security, and wire each alert as a
Superset Alert on its dataset+metric+threshold.

### 4 — Commit

Commit on the workstation (`repo-scaffold` git workflow): `consumption: add Debt Management dashboard`.

## Rules baked in

- **Metrics live on the dataset, once.** Don't hand-write the same aggregate in three charts — define
  it as a dataset metric and reference it. Same definition feeds the API and SAS.
- **Charts read the dataset, never raw mart SQL.** The dataset is the single semantic surface over the
  mart; charts compose from it.
- **RBAC is part of the deliverable.** A dashboard without its roles/row-level-security isn't done —
  Restricted-by-default applies to the consumption surface too.
- **Alerts are declared, not remembered.** The "90+ ageing band grew" watch is an alert on the
  manifest, not a person checking daily.

## Scripts & references

- `scripts/gen_superset.py` — spec → Superset dataset(s) + dashboard manifest.
- `references/dashboard-patterns.md` — the Debt dashboard panels, the standard debt metrics, RBAC and
  alert wiring, and how the same dataset feeds `expose-api` and the SAS consumer.
