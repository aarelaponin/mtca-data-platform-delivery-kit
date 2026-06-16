# Repo conventions — the full map

## Directory map (where does this file go?)

| You are producing… | It goes in… | Named… |
|---|---|---|
| An ingestion source config | `ingestion/sources/` | `<source>.yml` |
| A dbt staging model (1:1 clean of one source table) | `dbt/models/staging/` | `stg_<source>__<entity>.sql` |
| A dbt intermediate model (joins / golden record) | `dbt/models/intermediate/` | `int_<domain>__<concept>.sql` |
| A dbt mart (consumer-facing) | `dbt/models/marts/` | `mart_<domain>__<description>.sql` |
| A source/lineage declaration | `dbt/models/_sources/` | `sources.yml` |
| A reusable dbt macro | `dbt/macros/` | `<verb>_<noun>.sql` |
| A singular/data test | `dbt/tests/` | `<assertion>.sql` |
| A catalogue semantic enrichment | `catalogue/module-semantics/` | `<Module>_OpenMetadata.yaml` |
| A quality threshold / test spec | `quality/thresholds/` | `<mart>.yml` |
| A Superset dashboard spec | `consumption/dashboards/` | `<consumer>_<dashboard>.yml` |
| An API contract | `consumption/api/` | `<consumer>_<endpoint>.yml` |
| An RBAC / classification register | `security/` | `access-control-matrix.yml`, `classification-register.yml` |
| An ops runbook | `ops/runbooks/` | `<scenario>.md` |
| A principle / template / checklist | `docs/principles|templates|checklists/` | `<topic>.md` |
| An architecture decision record | `docs/adr/` | `NNNN-<slug>.md` |

## The five-layer medallion — placement is the rule

```
Bronze (raw, as-ingested)            ← ingestion-service writes here; not a dbt layer
   └─ staging/   stg_<source>__<entity>     one model per source table; types/cleaning ONLY, no joins
        └─ intermediate/ int_<domain>__<concept>   ALL cross-source joins + golden records (Taxpayer-360)
             └─ marts/  mart_<domain>__<desc>       consumer-facing; compose from int_, never re-join raw
                  └─ Published                       what consumers (Debt, SAS, …) actually read
```

Why the `int_` layer is mandatory and explicit: joins declared as named `int_` models (with
join-key not-null / `relationships` tests) make lineage legible and debugging tractable. Marts that
re-join raw sources hide the join logic and duplicate it across marts — the thing this layout
prevents. The Single Taxpayer Account / Taxpayer-360 is the canonical `int_` golden record.

## Two conventions that save the most pain

- **Generated artefacts are never hand-edited.** If a skill generated a model or config, fix the
  spec or the generator and regenerate. A hand edit is silently overwritten on the next run, and the
  divergence is hard to spot.
- **Everything-as-code, PR-reviewed.** No platform definition lives only in a chat, a Downloads
  folder, or a personal drive. It lands in this repo and is reviewed. Version control is the last
  step of every task, not an optional extra.

## Materialisation defaults (in `dbt_project.yml`)

| Layer | Materialised as | Schema |
|---|---|---|
| `staging` | view | `silver` |
| `intermediate` | table | `intermediate` |
| `marts` | table | `gold` |

Override per-model with a `{{ config(materialized=...) }}` block when a model needs it (e.g. an
incremental mart, or an ephemeral helper).
