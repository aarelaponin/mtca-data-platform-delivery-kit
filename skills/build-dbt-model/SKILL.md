---
name: build-dbt-model
description: >-
  Generate dbt models for the MTCA five-layer medallion from a compact spec — staging (`stg_`),
  the intermediate join / golden-record layer (`int_`), and consumer marts (`mart_`) — each with a
  schema YAML carrying tests, including the join CONTRACT (not-null keys + relationships) on `int_`
  models. Use this WHENEVER the work is to build, add, or change a dbt model: "create a staging
  model for this source table", "build the Taxpayer-360 / Single Taxpayer Account", "join these
  sources", "build the debt aged-balances mart", "add tests to this model", "scaffold stg_/int_/mart_",
  "model this in dbt". Trigger even when the user just describes a transformation or a join they
  need — the five-layer placement and the contract tests ARE the method, and free-hand SQL that
  re-joins raw sources in a mart is the anti-pattern this prevents. Cross-platform, pure Python.
---

# Build a dbt model (the five-layer medallion)

This skill generates dbt models that obey the platform's modelling rules so the team doesn't have
to hold them all in their head. The rules (from `repo-scaffold/references/repo-conventions.md`):

- **Bronze → `stg_` → `int_` → `mart_` → Published.**
- **`stg_<source>__<entity>`** — one model per source table; types/cleaning only, **no joins**.
- **`int_<domain>__<concept>`** — the **explicit join layer and golden-record hub**. Every
  cross-source join lives here as a named model, and its join keys are **contract-tested**
  (not-null + `relationships`). The Single Taxpayer Account / **Taxpayer-360 is the canonical
  `int_` golden record** (`int_taxpayer__master`).
- **`mart_<domain>__<desc>`** — consumer-facing; **composes from `int_`, never re-joins raw
  sources** (that hides the join logic and duplicates it across marts).

Why the `int_` contract matters: when joins are named models with not-null/relationships tests, a
broken or fan-out join fails `dbt test` at build time — not silently in a dashboard a week later.

## Workflow

### 1 — Write the model spec

A small YAML file describes one model. `kind` selects the layer.

**Staging** (`kind: staging`):
```yaml
kind: staging
source: ird            # bronze source name -> reads {{ source('bronze','ird__taxpayer') }}
table: taxpayer
key: taxpayer_id
description: One row per taxpayer from the IRD taxpayer table.
columns:
  - {src: tax_serial,  as: taxpayer_id,   cast: Int64}
  - {src: tax_name,    as: taxpayer_name}
  - {src: tax_balance, as: balance,       cast: "Decimal(38,2)"}
```

**Intermediate** (`kind: intermediate`) — joins + the golden record + the join contract:
```yaml
kind: intermediate
domain: taxpayer
concept: master         # -> int_taxpayer__master
key: taxpayer_id
description: Taxpayer-360 golden record joining IRD and VAT on TIN.
base: stg_ird__taxpayer
joins:
  - {model: stg_vat__registration, type: left, "on": "stg_ird__taxpayer.taxpayer_id = stg_vat__registration.taxpayer_id"}
select:
  - stg_ird__taxpayer.taxpayer_id
  - stg_ird__taxpayer.taxpayer_name
  - stg_vat__registration.vat_no
relationships:          # the join CONTRACT — generates not_null + relationships tests
  - {column: taxpayer_id, to: "ref('stg_ird__taxpayer')", field: taxpayer_id}
```
Quote the `"on":` key — bare `on` is parsed as a boolean in YAML (the generator tolerates both, but
quoting is clearer).

**Mart** (`kind: mart`) — composes from `int_`:
```yaml
kind: mart
domain: debt
desc: aged_balances     # -> mart_debt__aged_balances
key: taxpayer_id
description: Aged debt balances per taxpayer for the Debt dashboard.
from: int_taxpayer__master
select: [taxpayer_id, taxpayer_name, balance]
```

### 2 — Generate the model

```bash
# macOS / Linux
python3 scripts/gen_dbt_model.py --spec model.yml --out <repo>/dbt/models
```
```powershell
# Windows
py -3 scripts\gen_dbt_model.py --spec model.yml --out <repo>\dbt\models
```

It writes `<layer>/<name>.sql` and `<layer>/<name>.yml` (the schema file with tests) into the right
medallion directory. Omit `--out` to print to stdout for review first. Pure standard library
(PyYAML used if present).

### 3 — Review, then build and test

Read the generated SQL and YAML. Fill any `TODO` descriptions, confirm the grain and the join keys.
Then:
```bash
python tasks.py dbt-build && python tasks.py dbt-test     # from repo-scaffold's task runner
```
The `int_` relationships/not-null tests enforce the join contract; a fan-out or orphaned key fails
here. Marts should turn green only once their upstream `int_` models do.

### 4 — Commit

Commit on the workstation (the `repo-scaffold` git workflow): `dbt: add int_taxpayer__master with
join contract`. **Never hand-edit a generated model** — change the spec and regenerate, or the next
generation silently overwrites your edit.

## Rules baked in (don't fight them)

- **Staging never joins.** If you need a join, it belongs in an `int_` model.
- **Marts compose from `int_`.** A mart that selects from raw/staging and joins is the anti-pattern.
- **Every cross-source join is a contract.** Give it `relationships` so a break fails a test.
- **One golden record per entity.** `int_taxpayer__master` is the single Taxpayer-360; don't
  re-derive taxpayer joins in five different marts.

## Scripts & references

- `scripts/gen_dbt_model.py` — the generator (staging / intermediate / mart → SQL + tested schema YAML).
- `references/modelling-patterns.md` — the spec reference, the materialisation/incremental guidance,
  and worked patterns (golden record, debt marts, fan-out avoidance).
