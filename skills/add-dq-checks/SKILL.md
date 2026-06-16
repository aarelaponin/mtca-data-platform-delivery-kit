---
name: add-dq-checks
description: >-
  Generate the six-dimension data-quality checks for a dbt model per the MTCA Data Quality
  Framework — dimension-tagged dbt schema tests (uniqueness, completeness, validity, consistency),
  singular tests (timeliness freshness vs tier SLA, completeness row-budget/zero-row, accuracy
  reconciliation), and the per-dimension threshold config the reconciler scores into the 0–100
  quality badge. Use this WHENEVER the work is to add data-quality tests, gates, or monitoring to a
  model: "add DQ checks to this mart", "test the debt marts", "set up quality gates", "add freshness
  / completeness / validity tests", "make the quality badge work", "tag tests by dimension", "apply
  the DQF to this table". Trigger even when the user just says "make sure this data is trustworthy"
  or "gate this before production" — the six-dimension, DQF-tagged test set IS the method here, and
  untagged ad-hoc tests that don't roll up to a badge are the gap this fills. Cross-platform, pure Python.
---

# Add six-dimension DQ checks (DQF-applied)

This skill operationalises the **MTCA Data Quality Framework** (`frameworks/data-quality-framework/`
in this kit) on a single model. It generates tests that are **tagged by dimension** so the reconciler
can roll them up to the 0–100 quality badge written back to OpenMetadata — the headline Data Quality
Score the programme tracks (~60% → 90% by Q4 2026).

The two-tier model from the DQF: **dbt tests are build-time contracts (gates that fail the build);**
OpenMetadata profiling is fitness monitoring (incidents). This skill generates the dbt tier plus the
threshold config the reconciler and OM badge read.

## The six dimensions → what gets generated (and the DQF control)

| Dimension | Generated check | DQC |
|---|---|---|
| **Uniqueness** | `unique` on the grain | DQC-S4-01 |
| **Completeness** | `not_null` on grain + mandatory fields; a zero-row / row-budget singular test | DQC-S4-02, S3-02 |
| **Validity** | `accepted_values` on enums; range test on bounded numerics | DQC-S4-02 |
| **Consistency** | `relationships` on contracted join keys | DQC-S4-03 |
| **Timeliness** | a freshness singular test: newest `_extracted_at` vs the **tier SLA** (Hot 5 min, Warm 1 h, Cold 24 h, Archive 7 d) | DQC-S4-04 |
| **Accuracy** | a cross-source reconciliation singular test (a **stub** to implement — declared vs authoritative aggregate within tolerance) | DQC-S6-01 |

Every test carries `tags: [dq:<dimension>]` and `meta: {dq_dimension, control}` so results are
attributable to a dimension and a DQF control.

## Workflow

### 1 — Write the DQ spec

```yaml
model: mart_debt__aged_balances
tier: hot                      # sets the timeliness SLA (hot|warm|cold|archive)
description: DQ checks for the debt aged-balances mart.
grain: [taxpayer_id]           # uniqueness + not_null
mandatory: [taxpayer_id, balance, ageing_band]   # completeness (not_null)
enums:
  ageing_band: ["0-30","31-60","61-90","90+"]    # validity (accepted_values)
ranges:
  balance: {min: 0}            # validity (range; needs the dbt_expectations package)
relationships:                 # consistency (referential)
  - {column: taxpayer_id, to: "ref('int_taxpayer__master')", field: taxpayer_id}
freshness: {column: _extracted_at}   # timeliness column (default _extracted_at)
row_budget: {min_rows: 1}      # completeness (zero-row / minimum)
accuracy:                      # accuracy reconciliation(s) — generates a stub to implement
  - {name: vat_chain, description: "VAT declared vs e-invoice/customs aggregate within tolerance"}
```

### 2 — Generate

```bash
python3 scripts/gen_dq_checks.py --spec dq.yml --repo <repo-root>   # writes into the repo
python3 scripts/gen_dq_checks.py --spec dq.yml --print              # review on stdout first
```

It writes: `dbt/models/_dq/<model>.dq.yml` (the schema tests), `dbt/tests/<model>__*.sql` (the
freshness, row-budget, and accuracy singular tests), and `quality/thresholds/<model>.yml` (the
per-dimension PoC/Full targets from the DQF — **placeholders to confirm with the Data Owners & DGC**).
Pure standard library; uses PyYAML if present, otherwise emits JSON (valid YAML, so dbt still parses it).

### 3 — Wire dependencies, then build & test

The range test uses **`dbt_expectations`** — add it to `packages.yml` and `dbt deps` if you use range
checks (drop the `ranges:` block if you don't want the dependency). Then:
```bash
python tasks.py dbt-build && python tasks.py dbt-test
```
The gating tests fail the build on a breach. The accuracy stub **passes** until you implement it —
treat it as an **open control**, not a green check (it's flagged `not_implemented` in the threshold
config for exactly this reason).

### 4 — Implement accuracy, confirm thresholds, commit

Replace each accuracy stub with the real cross-source reconciliation (e.g. VAT declared vs the
e-invoice/customs aggregate, within an agreed tolerance). Confirm the threshold numbers with the Data
Owners. Then commit on the workstation (`repo-scaffold` git workflow):
`quality: add six-dimension DQ checks to mart_debt__aged_balances`.

## Rules baked in

- **Every test is tagged by dimension.** An untagged test doesn't roll up to the badge — so it
  doesn't count toward the score the programme reports.
- **The accuracy stub is not a pass.** A reconciliation you haven't written is an open control; the
  threshold config records it as `not_implemented` so a green `dbt test` doesn't mislead.
- **Timeliness follows the tier.** Don't hand-set a freshness window that contradicts the table's
  tier — set the tier and let the SLA follow (Hot 5 min … Archive 7 d).
- **Gates vs monitors.** dbt tests here are gates (fail the build); the OpenMetadata profiler does the
  fitness monitoring/incidents — see the DQF for that tier.

## Scripts & references

- `scripts/gen_dq_checks.py` — the generator (schema tests + singular tests + threshold config).
- `references/dq-dimension-map.md` — the full dimension → control → mechanism map, the tier SLAs, and
  how the reconciler turns tagged results into the 0–100 badge.
