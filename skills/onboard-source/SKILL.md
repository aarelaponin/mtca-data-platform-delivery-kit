---
name: onboard-source
description: >-
  Onboard a legacy MTCA source database into the Data Platform's Bronze layer under the Data
  Quality Framework gates: profile the source BEFORE writing any DDL, review the profile as a human
  gate, generate ClickHouse Bronze DDL (money widened to Decimal(38,s)), configure the gated
  ingestion, run the load, and verify reconciliation manifests. Use this WHENEVER the work is to
  load, reload, or connect a source into the platform — "onboard the ARS / Income Tax / VAT source",
  "load these tables into Bronze", "profile the database", "pull the legacy tables", "re-ingest",
  "is the load complete", "check the manifests", "the extractor failed", "set up ingestion for X".
  Trigger even when the user just names a source system and a data need — onboarding under the gates
  IS the method, and ad-hoc pulls without profiling and manifests are exactly the failure mode this
  prevents. Ported from the proven ARMS (Moldova) onboarding pipeline. Cross-platform, pure Python.
---

# Onboard a source into Bronze (DQF-gated)

This skill ports the source-onboarding pipeline proven on the sister ARMS project (one load run
brought in 21 + 10 tables including 24.7M- and 15.9M-row tables, all reconciled). It exists because
every step skipped here has caused a real incident on that project: a silent multi-million-row
truncation, a `Decimal(18,4)` overflow, a constant column mistaken for data, a refund box read as
tax-due, and schema drift. The gates are the point — they make an unattended load safe.

The controls referenced (DQC-S1-…, DQC-S2-…) are defined in the **MTCA Data Quality Framework**
(`frameworks/data-quality-framework/` in this kit). The repo layout the artefacts land in comes
from the `repo-scaffold` skill (`ingestion/sources/`, `dbt/`, `catalogue/`). Git runs on the
workstation — see `repo-scaffold/references/git-on-the-workstation.md`.

## The pipeline — in order, no skipping

**1. Inventory + profile (DQC-S1-01) — BEFORE any DDL.**
Run `scripts/profile_source.py` to list tables with row counts and profile the candidate columns.
It is dialect-aware (`--dialect informix|mysql|mssql|postgres`); MTCA's legacy estate is Informix.
Use `--dry-run` first to review the exact SQL (no DB needed), then run live. The profile flags the
traps that otherwise only appear after a wrong Silver build: constant columns, low fill rates,
near-zero positive rates on amount columns, and **real** MIN/MAX date coverage (TOP-sample dates
mislead). See `references/runbook.md` §1 for the per-column profiling SQL.

```bash
# review the SQL offline
python3 scripts/profile_source.py --dialect informix --dry-run --tables taxpayer,bop
# live (password via env var, never on the command line) → writes the gate report + schema spec
SRC_DB_PASSWORD=... python3 scripts/profile_source.py --dialect informix \
  --host <pre-prod-host> --db <db> --user <user> \
  --tables <subset> --out profile_<src>.md --emit-schema schema_<src>.json
```

**2. Human review gate.** Present the profile and get an explicit decision on the load set. Every
time, check: real date coverage vs the analysis period (query MIN/MAX explicitly); whether the
obvious key column is actually filled (a 0%-filled "ID" means the real key is elsewhere); the
**mystery-table A/B/C triage** for tables of unknown purpose (A = clearly in scope, B = confirm with
the owner, C = defer); and document-class giants (>100M rows) get a chunked, tiered strategy, never
a wholesale pull. Defer middleware/scratch tables (`temp_*`, `wso2_*`). Decide the **tier** here too
— Hot / Warm / Cold / Archive — the debt sources are **Hot (≈60-second freshness)**.

**3. Generate Bronze DDL.** `scripts/gen_bronze_ddl.py` reads the schema spec from step 1 and emits
repo-convention ClickHouse DDL: `MergeTree`, meta columns (`_extracted_at`, `_batch_id`, `_source`),
`PARTITION BY toYYYYMM(_extracted_at)`, `ORDER BY` the key. **Money/decimal is widened to
`Decimal(38, s)` — never 18**: real pre-prod values overflow `Decimal(18,4)`. Review the DDL, save
it as the next-numbered `dbt/`/`clickhouse` migration, apply it, and verify the table count.

```bash
python3 scripts/gen_bronze_ddl.py --schema schema_<src>.json --out <repo>/ingestion/<src>/
```

**4. Configure the gated ingestion.** Register the source and its tables in
`ingestion/sources/<src>.yml` (host/port/db/credentials via env vars; the tier; watermarks for
incremental tables). Pre-prod hosts differ from defaults — set them explicitly. The extractor
**appends** and is gated: it never silently falls back to CSV or partial loads (DQC-S2-05).

**5. Run the gated load.** Small sources inline; large ones detached (the gates make unattended
safe). If a table is being **reloaded**, snapshot the old data and TRUNCATE first (the extractor
appends). A mid-load insert error aborts that *table* (a gate), not the run — the failure and the
partial count land in the manifest.

**6. Verify manifests — the load is not done until this passes (DQC-S2 reconciliation).**
Every table must have one SUCCESS manifest row with `reconciled = true` and `schema_check = PASS`,
and the loaded count must equal the source profile **exactly**. A `_batch_id`-scoped count is the
reconciliation basis (it works even on a non-empty target). If reconciliation fails, the source
truth and the loaded count are both in the manifest — investigate, don't paper over.

**7. Catalogue + commit.** Copy the profile into `catalogue/onboarding/`, run OpenMetadata
ingestion if a new schema appeared, write semantic descriptions (use the `legacy-module-to-openmetadata`
or `verify-catalogue-semantics` skills), then **commit on the workstation** (`repo-scaffold` git
workflow): `ingestion: onboard <src> (<N> tables, <tier> tier)`.

## Hard-won rules (do not rediscover)

- **Profile before DDL, always.** The cost of profiling is minutes; the cost of a wrong Silver build
  discovered downstream is days and a credibility hit.
- **`Decimal(38, s)`, never 18.** This is encoded in the generator; don't override it down.
- **Reconcile every custody transfer.** No SUCCESS manifest with an exact count = not loaded.
- **No silent fallback.** A gated extractor that can't complete fails loudly; that is the feature.
- **Confirm the real key and real date range** by explicit MIN/MAX, not a sampled preview.
- **Tier on purpose.** Debt = Hot (~60s); reference data = Warm/Cold; history = Archive.

## Scripts & references

- `scripts/profile_source.py` — the pre-DDL profiler / gate-report generator (dialect-aware;
  `--dry-run`, `--emit-schema`).
- `scripts/gen_bronze_ddl.py` — schema spec → ClickHouse Bronze DDL with the MTCA conventions and
  money-widening.
- `references/runbook.md` — exact command blocks per dialect (inventory, per-column profiling,
  DDL apply, manifest verification, failure-path), the tiering guide, and the mystery-table A/B/C
  triage.
