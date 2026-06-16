# dbt modelling patterns & spec reference

## Spec field reference

### Common
- `kind` — `staging` | `intermediate` | `mart` (required).
- `name` — explicit model name; otherwise derived from the layer fields below.
- `key` — the grain / primary key; generates `unique` + `not_null` tests.
- `description` — model description (fill the TODO if you leave it out).

### `kind: staging`
- `source` — bronze source name; the model reads `{{ source('bronze', '<source>__<table>') }}`.
- `bronze_schema` — override the bronze schema name (default `bronze`).
- `table` — bronze table name.
- `columns` — list; each item is either a bare name (`tax_name`) or
  `{src: <col>, as: <alias>, cast: <ClickHouse type>}`. Casts use `cast(col as Type)`.
- Name derives to `stg_<source>__<table>`.

### `kind: intermediate`
- `domain`, `concept` — derive `int_<domain>__<concept>`.
- `base` — the first model in the FROM.
- `joins` — list of `{model, type, "on"}`. `type` defaults to `left`. **Quote `"on"`** (bare `on`
  is YAML boolean `True`; the generator tolerates both but quoting is clearer).
- `select` — the output column list (qualify with the model/alias name).
- `relationships` — the join contract: list of `{column, to, field}`. Each generates `not_null` +
  `relationships(to=…, field=…)` on that column. If `column` equals `key`, the tests merge onto the
  key column.

### `kind: mart`
- `domain`, `desc` — derive `mart_<domain>__<desc>`.
- `from` — the upstream `int_` (or another mart) the mart composes from.
- `select` — output columns (defaults to `*`).

## Materialisation & incremental

Defaults come from `dbt_project.yml` (staging→view/silver, intermediate→table/intermediate,
marts→table/gold). Override per model when needed by adding a config block at the top of the
generated SQL **via the spec's intent, then regenerating** — or, for a one-off, in a follow-up model
that you then keep in sync. For large, append-only facts (payments, assessments) use an incremental
materialisation keyed on `_extracted_at`/`_batch_id`; document the incremental predicate in the
model description so the next person understands the load semantics.

## Pattern — the golden record (Taxpayer-360)

`int_taxpayer__master` is the **one** place taxpayer identity is resolved across the nine databases
on TIN. Every downstream mart that needs taxpayer attributes joins to (or selects from) this model —
they do **not** re-join `stg_ird__taxpayer` to `stg_vat__registration` themselves. This keeps one
definition of "who the taxpayer is" and one place to fix it.

Build it incrementally: start with the two or three sources the first consumer (Debt) needs, with
the join contract, and add sources as later consumers require them. The contract tests are what make
adding a source safe — a new join that fans out or orphans keys fails immediately.

## Pattern — the debt marts

- `mart_debt__aged_balances` — per-taxpayer outstanding balance bucketed into ageing bands; composes
  from the debt `int_` (balances) + `int_taxpayer__master` for identity. No raw joins.
- `mart_debt__collection_performance` — collection/instalment tracking over time.

Both read from `int_` models only. If you find yourself joining `stg_` tables inside a mart, stop and
push that join up into an `int_` model with a contract — that is the signal the layering is being
bypassed.

## Pattern — avoiding silent fan-out

The most common modelling bug is a join that multiplies rows (a one-to-many where you assumed
one-to-one). Defences, in order:
1. Put the join in an `int_` model with a `relationships` contract and a `unique` test on the grain.
2. If the grain test fails, the join fanned out — add the missing join predicate or pre-aggregate the
   many-side in its own `int_` model first.
3. Never "fix" a fan-out by `distinct` in a mart; fix the join in the `int_` layer.
