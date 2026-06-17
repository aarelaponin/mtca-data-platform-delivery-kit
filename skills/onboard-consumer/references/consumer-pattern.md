# The consumer pattern — reference

## Why one repeatable path

The platform's value compounds only if each consumer is served from the **shared Gold layer**, not
from a private pipeline. If every consumer copied its own data, you'd have N drifting versions of "the
taxpayer" and N places to fix a bug. The onboarding pattern enforces the opposite: capture needs →
diff against Gold → build any gap into Gold (reused next time) → expose a surface → gate. Debt was the
first run of this; SAS is the second; the pattern is identical.

## The served-surface index (the inventory)

The `--inventory` YAML is the platform's catalogue of what Gold currently serves:

```yaml
marts:
  mart_debt__aged_balances: [taxpayer_id, taxpayer_name, balance, ageing_band, total_outstanding, debt_to_assessment]
  int_taxpayer__master: [taxpayer_id, taxpayer_name, segment]
  mart_vat__compliance: [taxpayer_id, vat_declared, vat_paid]
```

Keep it current — generate it from `dbt/models/marts` + `dbt/models/intermediate` (column lists from
the model YAMLs), or maintain it as a small index file. It's what lets the gap analysis say "already
served" vs "must build". Intermediate (`int_`) models are included because a golden record like
`int_taxpayer__master` is a legitimate serving surface for identity attributes.

## Gap analysis

For each need (field or metric), the tool checks whether any inventory mart exposes a column of that
name:
- **served** → it lists which mart(s) provide it (reuse — do not rebuild).
- **missing** → it becomes a build step, grouped by entity, with the skill chain to close it.

Naming matters: a metric is "served" when a mart exposes it under the same name. This is why metrics
are defined once (on the mart / the dataset) — so "total_outstanding" means the same thing to every
consumer and the gap analysis can match it.

## Worked example — SAS risk (feed + write-back), the second consumer

- **Surface: feed.** SAS reads the Gold marts directly for risk analytics (no copy) — it's "neither new
  nor open-source", a consumer of the platform, not the platform itself.
- **Needs** (taxpayer identity + debt metrics + VAT figures) are mostly already served by the Debt and
  VAT marts and `int_taxpayer__master` — so onboarding SAS is largely *reuse*, which is the point.
- **Write-back:** SAS's outputs (`mart_risk__scores`: taxpayer_id, risk_score, risk_band) are modelled
  as a **Gold mart** with DQ checks and a verified catalogue — so the dashboard and the API can read
  risk scores like any other Gold data, and the risk score the dashboard shows is the one SAS wrote.
- **Gates:** same as Debt — DQ green, catalogue VERIFIED, RBAC (`sas_analyst`, `risk_modeller`),
  production-readiness PASS.

## How it scales

Consumer 3+ (compliance, refunds, customs…) follows the same spec → gap → plan → gate. Each one:
- reuses whatever Gold already serves (the index grows, so later consumers reuse more),
- contributes any gap it needs back into the shared Gold (so it's there for the next consumer),
- gets the same DoD gate.

That's the depth thread of the platform: breadth (X3) brings the whole estate into Bronze/catalogue;
this pattern serves each consumer from the shared Gold on top of it. The first consumer is the hardest;
every subsequent one is mostly reuse — which is exactly what a comprehensive platform should make true.

## Definition of Done (the consumer gate)

`needs-captured · gaps-resolved · surface-exposed · writeback-wired (if any) · rbac-set · dq-green ·
catalogue-verified · readiness PASS · sign-off`. The tool seeds the statuses (needs-captured and
gaps-resolved are computed; the rest start pending). Don't relax it for a "small" consumer — a small
consumer with wrong or ungated data still produces wrong decisions.
