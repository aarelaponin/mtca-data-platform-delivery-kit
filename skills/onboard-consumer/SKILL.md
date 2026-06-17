---
name: onboard-consumer
description: >-
  Serve a new consumer from the platform the repeatable way — diff its data needs against the current
  Gold marts, then emit a tailored onboarding plan (which gaps to build, which surface to expose, what
  to gate) and the consumer's Definition-of-Done checklist. Use this WHENEVER a new consumer or module
  needs platform data: "onboard the SAS project", "serve the compliance team", "what does this consumer
  need that we don't have yet", "expose data for this new module", "plan onboarding for a new
  consumer", "can the platform already serve X". Trigger even when the user just names a team/module
  and the data they want — the gap-analysis-then-plan path IS the method, and the rule it enforces is
  that consumers pull from Gold (no bespoke side-pipelines); a missing need becomes a shared mart, not
  a private copy. Debt Management was the first consumer; SAS risk is the second. Cross-platform,
  pure Python.
---

# Onboard a new consumer (the depth pattern, generalised)

The platform is comprehensive and serves consumers in sequence — Debt Management first, the SAS risk
project second, then compliance, refunds, customs, the ITCAS feeds. Each is onboarded the **same** way,
and this skill makes that repeatable so the tenth consumer is as smooth as the second:

1. **capture** the consumer's data needs;
2. **diff** them against what Gold already serves (gap analysis);
3. **plan** the build for the gaps and the surface to expose, referencing the other skills;
4. **gate** with the consumer Definition-of-Done.

The rule it encodes: **consumers pull from Gold; nobody gets a side-pipeline.** A need that isn't
served becomes a mart or `int_` model in the shared platform, reused by whoever needs it next — so the
platform gets richer with each consumer instead of sprouting parallel copies.

## Workflow

### 1 — Capture the consumer needs spec

```yaml
consumer:
  name: sas-risk
  description: SAS VIYA risk scoring — the platform's second consumer.
  surface: feed                 # dashboard | api | feed
  freshness: warm               # tier the consumer needs
  writes_back:                  # feed consumers may write outputs back to Gold
    - {mart: mart_risk__scores, fields: [taxpayer_id, risk_score, risk_band]}
needs:
  - entity: taxpayer
    fields: [taxpayer_id, taxpayer_name, segment]
    metrics: [total_outstanding, debt_to_assessment]
  - entity: vat
    fields: [taxpayer_id, vat_declared, vat_paid]
rbac: [sas_analyst, risk_modeller]
```

### 2 — Provide the mart inventory

A YAML of what Gold currently exposes (generate it from the repo's `dbt/models/marts` + `intermediate`,
or maintain it as the platform's served-surface index):

```yaml
marts:
  mart_debt__aged_balances: [taxpayer_id, taxpayer_name, balance, ageing_band, total_outstanding, debt_to_assessment]
  int_taxpayer__master: [taxpayer_id, taxpayer_name, segment]
  mart_vat__compliance: [taxpayer_id, vat_declared, vat_paid]
```

### 3 — Generate the plan + checklist

```bash
python3 scripts/gen_consumer_plan.py --spec consumer.yml --inventory marts.yml --repo <repo-root>
python3 scripts/gen_consumer_plan.py --spec consumer.yml --inventory marts.yml --print   # review first
```
Writes `consumption/consumers/<name>/onboarding_plan.md` (coverage table + ordered plan + DoD checklist)
and `gap.json` (machine-readable served/missing). Pure standard library.

### 4 — Execute the plan, gate, sign off

Work the plan: close each gap with the named skills (**onboard-source** → **build-dbt-model** →
**add-dq-checks** → **import-schema-to-catalogue** + **verify-catalogue-semantics**), expose the surface
(**build-superset-dashboard** / **expose-api** / a Gold feed), set RBAC, run **production-readiness-check**,
and get sign-off. Commit on the workstation (`repo-scaffold` git workflow):
`consumption: onboard <consumer> (N served, M built)`.

## The three surfaces

- **dashboard** — Superset dashboard over the serving marts (`build-superset-dashboard`).
- **api** — OpenAPI + parameterized SQL for a workflow/app (`expose-api`).
- **feed** — the consumer reads the Gold marts directly (no copy); a **feed** consumer may also
  **write back** (e.g. SAS writes `mart_risk__scores`), which is modelled, DQ'd and verified like any
  other Gold mart, then read by downstream consumers normally.

## Rules baked in

- **Pull from Gold, never a side-pipeline.** A missing need is built into the shared platform, reused
  next time — not copied into the consumer's own store.
- **A new field belongs in the mart/`int_`, not the endpoint.** Don't transform privately in a
  dashboard or API; push it up so the meaning is shared.
- **Write-back is Gold too.** A consumer's outputs (risk scores) are a Gold mart with DQ + verified
  catalogue — so the next consumer can trust and reuse them.
- **Same gates as the first consumer.** DQ green, catalogue VERIFIED, RBAC set, readiness PASS — the
  consumer DoD doesn't get relaxed because it's the second (or tenth) consumer.

## Scripts & references

- `scripts/gen_consumer_plan.py` — needs + inventory → gap analysis, plan, DoD checklist, `gap.json`.
- `references/consumer-pattern.md` — the served-surface index, the SAS worked example (feed + write-back),
  and how the pattern scales from Debt to every later consumer.
