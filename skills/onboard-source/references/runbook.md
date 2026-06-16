# Onboarding runbook — exact commands & decisions

## §1 — Inventory + per-column profiling

### Inventory (row counts) by dialect
The profiler runs these for you; shown here so you can run them by hand or in a DB client.

- **Informix:** `SELECT tabname, nrows FROM systables WHERE tabid > 99 AND tabtype='T' ORDER BY nrows DESC;`
- **MySQL:** `SELECT table_name, table_rows FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type='BASE TABLE' ORDER BY table_rows DESC;`
- **MSSQL:** `SELECT t.name, SUM(p.rows) FROM sys.tables t JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN (0,1) GROUP BY t.name ORDER BY 2 DESC;`
- **Postgres:** `SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;`

> Informix `nrows` is an optimiser estimate. For tables you're about to load, confirm with an exact
> `SELECT COUNT(*)` — the reconciliation in §6 requires the exact number.

### Per-column profile (the gate signals)
For each candidate table, for each column you care about:

```sql
SELECT COUNT(*)                         AS n,
       COUNT(<col>)                     AS non_null,        -- fill rate = non_null / n
       COUNT(DISTINCT <col>)            AS distinct_vals,   -- 1 => constant column (trap)
       MIN(<col>) AS min_v, MAX(<col>)  AS max_v            -- real coverage, not a sample
FROM <table>;
```

Flags that block or qualify a load:
- **distinct_vals = 1** → constant column; it carries no information (a real incident source).
- **fill rate < 100% on a supposed key** → the real key is elsewhere; find it before modelling.
- **near-zero positive rate on an amount column** → likely the wrong column or a sign/units issue.
- **max date < analysis period start** → the table doesn't cover the period you need.

## §2 — The tiering decision (set per table at the review gate)

| Tier | Freshness target | Typical content |
|---|---|---|
| **Hot** | ~60 seconds | debt sources: payments, assessments, taxpayer, compliance status |
| **Warm** | hourly / daily | reference & master data, most operational tables |
| **Cold** | weekly / on-demand | low-velocity history used occasionally |
| **Archive** | one-off / frozen | closed years, decommissioned systems kept for audit |

Debt Management is the first consumer and needs **Hot** sources. Don't put a 300M-row history table
on Hot — tier it Cold/Archive and load incrementally by watermark or partition.

## §3 — Mystery-table A/B/C triage

Legacy estates carry tables of unknown purpose. Classify before loading:
- **A — clearly in scope:** named and understood; load.
- **B — confirm:** plausibly relevant but unverified; ask the source/data owner, then load or defer.
- **C — defer:** scratch/middleware/temp (`temp_*`, `wso2_*`, `bak_*`), empty, or clearly obsolete.

Record the classification in the profile so the next person doesn't re-litigate it.

## §4 — Generate & apply Bronze DDL

```bash
python3 scripts/gen_bronze_ddl.py --schema schema_<src>.json --out <repo>/ingestion/<src>/
```
- Review the emitted SQL. Money/decimal must be `Decimal(38, s)` (the generator enforces this).
- A table with no source primary key emits `ORDER BY tuple()` and a NOTE — choose a real
  `ORDER BY` (a natural key or `_extracted_at`) before production; don't ship `tuple()` for a Hot table.
- Save as the next-numbered migration in your ClickHouse/dbt migrations area, apply, and verify the
  table count matches the spec.

## §5 — Run the load

- Configure `ingestion/sources/<src>.yml`: connection (env-var credentials), the table registry,
  per-table tier and watermark. Pre-prod hosts differ from test defaults — set them explicitly.
- **Reload:** snapshot existing data (`<table>_bak`) and `TRUNCATE` first — the extractor appends.
- Big sources: run detached; the gates make it safe to leave unattended.
- Exit semantics to expect from a gated extractor: `0` = all tables reconciled; `1` = one or more
  gate failures (see manifests); `2` = environment (target or manifest store down). It must **never**
  fall back to a silent CSV/partial load.

## §6 — Verify manifests (reconciliation gate)

The load is complete only when, for every loaded table, the manifest store shows:
- one `SUCCESS` row, `reconciled = true`, `schema_check = PASS`, and
- loaded count **exactly equal** to the source `COUNT(*)` from §1.

Use a `_batch_id`-scoped count as the basis so it holds on a non-empty target. If a count is short,
the source truth and the loaded number are both recorded — investigate the gap; never adjust the
expectation to match the load.

## §7 — Failure-path test (do this once per new extractor wiring)

Deliberately point one small table at a bad target or feed a row that violates the schema, and
confirm: the table aborts, the run continues, and the manifest records the failure with the partial
count. If a failure does **not** show up in the manifest, the gate isn't wired — fix that before
trusting any load.

## Hosts & credentials

Record pre-prod hosts/ports/DB names for each source here as you onboard them (host, port,
database, schema owner). Never store passwords in the repo — they live in the workstation
environment / secret store and are read in-shell via `SRC_DB_PASSWORD`.

| Source | Host | Port | Database | Schema owner | Notes |
|---|---|---|---|---|---|
| _(fill as onboarded)_ | | | | | |
