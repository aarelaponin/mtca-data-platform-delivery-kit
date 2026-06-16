# DQ dimension → control → mechanism map

The authoritative definitions are in the DQF (`frameworks/data-quality-framework/`, §3 and §6). This
is the operational map the generator implements.

## The six dimensions (DAMA-DMBOK, MTCA operational form)

| Dimension | MTCA operational meaning | Generated mechanism | DQF control |
|---|---|---|---|
| **Completeness** | required data present; rows survive custody; mandatory fields populated | `not_null` (grain + mandatory); zero-row / row-budget singular test | DQC-S2-03, S3-02, S4-05 |
| **Validity** | values conform to domain/type/format | `accepted_values` (enums); range test (bounded numerics) | DQC-S2-02, S4-02 |
| **Accuracy** | values agree with an authoritative reference | cross-source reconciliation singular test (declared vs aggregate, tolerance) | DQC-S6-01, S1-03 |
| **Consistency** | same fact agrees across representations / over time | `relationships` on contracted keys | DQC-S4-03, S2-01 |
| **Uniqueness** | entities represented once at declared grain | `unique` on the grain | DQC-S4-01 |
| **Timeliness** | as fresh as the tier SLA requires, and age is visible | freshness singular test vs tier SLA | DQC-S4-04, S3-01/03 |

## Tier SLAs (DQF §3 Full targets) — timeliness

| Tier | SLA | Typical content |
|---|---|---|
| Hot | 5 min | debt sources (payments, assessments, taxpayer, compliance) |
| Warm | 1 h | reference & master data, most operational tables |
| Cold | 24 h | low-velocity history |
| Archive | 7 d | closed years, decommissioned systems |

The generator turns `tier:` into the freshness window — set the tier, don't hand-set the minutes.

## Proposed targets per dimension (DQF §3 — confirm with Data Owners & DGC)

| Dimension | PoC target | Full target |
|---|---|---|
| Completeness | ≥95% mandatory fill; ≥99% rows reconciled | ≥99% fill; 100% reconciled |
| Validity | ≥99% rows pass | ≥99.5% |
| Accuracy | reconciliations defined & measured (VAT chain) | tolerance bands agreed & met |
| Consistency | ≥98% cross-reference match | + cross-DB FK ≥ agreed floor |
| Uniqueness | <1% duplicates; 100% at grain post-dedup | 100% |
| Timeliness | freshness visible; tier SLAs defined | per-tier SLAs met |

These land in `quality/thresholds/<model>.yml` as `poc_target` / `full_target` per dimension.

## How tagged results become the badge

1. Each test carries `tags: [dq:<dimension>]` and `meta: {dq_dimension, control}`.
2. dbt writes results (pass/fail/rows) to its artifacts; the **thin reconciler** (DQF §7.4) reads the
   dimension-tagged results, computes a 0–100 score per table per dimension against the targets in the
   threshold config, and writes the composite **quality badge** back to the OpenMetadata entity.
3. The badge is what the DcP3 handover package and the field-selection view read (DQC-S5-01/02).

So a test that isn't dimension-tagged is invisible to the badge — which is why the generator tags
everything. If you add a test by hand, tag it the same way (`config: {tags: [dq:<dim>], meta:
{dq_dimension: <dim>}}`) or it won't count.

## Gates vs monitors

- **Gates** (this skill): dbt tests that **fail the build** — uniqueness, not-null, accepted-values,
  range, relationships, freshness, row-budget. A breach blocks promotion.
- **Monitors** (OpenMetadata profiler + test suites, separate tier): fitness signals that **open an
  incident** rather than blocking — distribution shift, fill-rate drift, profile anomalies. See the
  DQF §5 division of labour; this skill owns the gate tier and the threshold config the monitor tier
  scores against.

## Accuracy is special — don't ship a false green

A reconciliation you haven't written must not read as a pass. The generator emits an accuracy
**stub** that returns no rows (so `dbt test` is green) **only as a placeholder**, and records
`accuracy: not_implemented` in the threshold config. Until the real comparison is written, accuracy
for that model is an **open control** — report it as such, and implement it (the VAT chain is the
first one the DQF calls out).
