---
name: import-schema-to-catalogue
description: >-
  Wire a source's schema into the platform — generate the dbt `sources.yml`, the OpenMetadata
  technical-metadata import, and reference-data vocabularies (code→label) from a source schema spec.
  Use this WHENEVER the work is to register a source's structure for dbt and the catalogue: "create
  the dbt sources file", "import the schema into OpenMetadata", "register these tables for dbt",
  "set up lineage for this source", "extract the code/lookup tables", "build the reference
  vocabulary", "what are the accepted values for this status column". Trigger right after
  `onboard-source` has profiled and loaded a source (it consumes the same schema spec), and before
  staging models `{{ source() }}` it. This is the *technical* half of cataloguing — business meaning
  is added/verified separately by `verify-catalogue-semantics`. Cross-platform, pure Python.
---

# Import a source schema into dbt + the catalogue

Cataloguing a source has two halves. This skill does the **technical** half — the structure: declare
the source to dbt so models can reference it and lineage is captured, seed OpenMetadata with the
technical metadata, and extract the controlled **reference vocabularies** (the code→label lookups)
that validity tests and the glossary depend on. The **business** half — what each column *means* —
is DRAFT here and is confirmed by `verify-catalogue-semantics`. Keeping them separate is deliberate:
structure is mechanical and can be generated; meaning needs evidence.

It consumes the schema spec that `onboard-source`'s `profile_source.py --emit-schema` produces (the
same JSON), so it slots straight in after a load.

## Workflow

### 1 — Generate the dbt sources + technical metadata

```bash
python3 scripts/import_schema.py --schema schema_<src>.json --repo <repo-root>
```
Writes:
- `dbt/models/_sources/<src>__sources.yml` — the dbt source declaration: `source: bronze`, each
  Bronze table (`<src>__<table>`) and its columns, with the source type and the mapped ClickHouse
  type in `meta` (money widened to `Decimal(38,s)`, matching the Bronze DDL). Staging models then
  `{{ source('bronze', '<src>__<table>') }}` and dbt captures the lineage.
- `catalogue/import/<src>_technical.yaml` — technical metadata for OpenMetadata (column `dataType`,
  nullability, the original `sourceType`). Note: OM's ClickHouse connector is **authoritative** for
  live types; this import seeds structure and is the place description stubs hang off until verified.

Descriptions are written as `TODO — verify via verify-catalogue-semantics` on purpose — this skill
does not invent meaning.

### 2 — Extract reference-data vocabularies (code tables)

Small code/lookup tables (status, category, reason, role…) are the controlled vocabularies the
platform validates against. Turn one into a vocabulary from its rows:

```bash
python3 scripts/import_schema.py --vocab --data <ref_table>.csv \
  --code-col <CODE> --label-col <LABEL> --name <vocab_name> --repo <repo-root>
```
Writes `catalogue/vocabularies/<vocab_name>.yml` — the `code → label` terms (deduplicated, blanks
dropped, sorted) **plus** a ready `accepted_values` list. Drop that list straight into an
`add-dq-checks` `enums:` block so the column is validity-tested against the real vocabulary, and
register the terms in the OpenMetadata glossary.

### 3 — Wire, build, verify, commit

Add the source file to the dbt project (it lives under `models/_sources/`), run `dbt build` so the
source resolves and lineage appears, ingest the technical metadata / glossary terms into
OpenMetadata, then hand the table/column descriptions to `verify-catalogue-semantics` to take them
DRAFT → VERIFIED. Commit on the workstation (`repo-scaffold` git workflow):
`catalogue: import <src> schema (sources + technical + vocabularies)`.

## How it fits the catalogue trio

- **`onboard-source`** profiles + loads the source and emits the schema spec.
- **this skill** registers the structure: dbt sources, technical metadata, reference vocabularies.
- **`legacy-module-to-openmetadata`** recovers business descriptions from legacy code.
- **`verify-catalogue-semantics`** takes those descriptions DRAFT → VERIFIED and gates them.

## Rules baked in

- **Structure now, meaning later.** Descriptions stay TODO/DRAFT; don't fill business meaning here —
  that's verified evidence, not generation.
- **The connector is authoritative for types.** The technical import seeds structure; it doesn't
  override what OM reads live from ClickHouse.
- **Vocabularies are controlled.** A reference table becomes one source of truth for its codes — its
  `accepted_values` drive the validity tests, so the data can't drift from the vocabulary silently.
- **Money stays widened.** The `ch_type` meta mirrors the Bronze DDL (`Decimal(38,s)`); don't narrow it.

## Scripts & references

- `scripts/import_schema.py` — schema mode (sources.yml + technical) and `--vocab` mode (code→label).
- `references/import-notes.md` — the schema-spec shape, the type-mapping table, identifying reference
  tables, and how vocabularies feed `add-dq-checks` and the glossary.
