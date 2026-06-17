---
name: legacy-module-to-openmetadata
description: >-
  Turn a legacy PowerBuilder module's SOURCE CODE into an OpenMetadata-ready semantic
  enrichment — without a database or a running system. From a .pbl it recovers the tables the
  module uses, the application→table lineage, the column inventory, and DRAFT business
  descriptions, as a loadable YAML plus a human-review markdown. Use this WHENEVER the goal is
  to document, catalogue, or recover the data meaning of a legacy module from its code: "which
  tables does this module use", "document these legacy tables/columns for the catalogue",
  "generate OpenMetadata input from this PowerBuilder app", "produce a data dictionary from the
  source", "seed the catalogue from legacy code". Trigger even when the user only names a module
  folder and a catalogue goal — recovering meaning from source beats waiting for DB access.
  Proven on the MTCA BOP Registration module (25 tables / 141 columns). Cross-platform, pure
  Python, no install.
---

# Legacy module → OpenMetadata semantic enrichment

## What this is for

Legacy systems hold their real business meaning in two places: the database schema (column
names, types) and the **application code** that reads and writes it. When you can't get to a
running database — common during a migration, where access is gated, slow, or the system is
being decommissioned — the source code is still right there, and it is enough to recover a
surprising amount: which tables a module touches, how columns are used, and the
application→table lineage a catalogue needs.

This skill automates that recovery for **PowerBuilder** modules (the dominant legacy stack at
MTCA) and produces input that drops straight into **OpenMetadata**: a YAML enrichment file plus
a markdown review sheet. It was built from a real experiment — one BOP Registration `.pbl`,
source only, yielded 25 tables and 141 documented columns in minutes.

The division of labour is deliberate, and it matters:

- **The bundled script does the mechanical, error-prone 60%** — decoding the binary library
  (PowerBuilder stores its text as UTF-16LE, which trips up every naïve `grep`), pulling table
  references out of DataWindows and embedded SQL, cross-checking them against a schema
  inventory to strip framework noise, grouping columns into prefix families, and
  auto-mapping the confident ones. This is the part that is tedious and easy to get wrong by
  hand, so let the script own it.
- **You (the model running this skill) do the judgement 40%** — pruning framework
  false-positives, mapping the column families the script flagged as ambiguous, and writing
  business descriptions a human reviewer can sign off. Descriptions are domain knowledge; they
  can't be hard-coded into a script, which is the whole reason this is a skill and not just a
  CLI tool.

Keep that split in mind throughout: run the script first, then apply your judgement to its
evidence. Don't try to parse the `.pbl` yourself — the script already did it correctly.

## Inputs you need

1. **The module source** — a `.pbl` library (or a folder of them). For BOP this is
   `…/BOP Registration/Bopindex/bopindex.pbl`. Paths often contain spaces, so quote them.
2. **A legacy schema inventory (optional but strongly recommended)** — any list of the real
   table names in the source database. The script accepts a YAML with `table_name:` /
   `database:` keys, a JSON list, or a plain newline-separated list of names. The inventory is
   what lets the script tell a real data table from a PowerBuilder class or a word inside a
   message string. At MTCA this is the legacy DWH inventory under `04-db-legacy/…/phase1_source_tables.yaml`.
   If you have no inventory, the script falls back to accepting only tables seen in
   INSERT/UPDATE/DELETE/DataWindow contexts — noisier, so confirm the table list more carefully.

## Workflow

### 1 — Run the extractor

```bash
# macOS / Linux
python3 scripts/extract_pb_tables.py \
  --source "/path/to/Module/library.pbl" \
  --inventory "/path/to/schema_inventory.yaml" \
  --out "/path/to/output-dir" \
  --module-name MyModule
```

```powershell
# Windows (PowerShell) — use py and back-quotes or one line
py -3 scripts\extract_pb_tables.py --source "C:\path\to\library.pbl" --inventory "C:\path\to\inventory.yaml" --out "C:\path\to\out" --module-name MyModule
```

`--inventory` and `--module-name` are optional (module name defaults to the filename). Point
`--out` at a **workspace / catalogue output directory in the repo** (e.g. `catalogue/module-semantics/`)
— **not** at the skill's own folder; the script writes three files there, and you want them with your
deliverables, not buried in the skill. The script needs only the Python standard library; if `PyYAML`
happens to be installed it uses it, otherwise it writes valid YAML itself. It produces three files in
`--out`:

- `<Module>_extraction.json` — the evidence: confirmed tables, dml-only candidates, authoritative
  `dbname` column pairs, column-prefix families, the auto-mapping, and the prefixes it could
  **not** confidently map (left for you).
- `<Module>_OpenMetadata.yaml` — the scaffold, with `usesTables` lineage and per-column
  `inferredType`. Table and business-column descriptions are deliberately left as `TODO` /
  `(to confirm)`.
- `<Module>_OpenMetadata.md` — the same content as a readable review sheet.

### 2 — Read the evidence and finalise the table list

Open `<Module>_extraction.json`. Two judgement calls:

- **Prune framework false-positives.** A schema inventory contains every table in the database,
  including generic ones the PowerBuilder *framework* touches (e.g. `administrator`,
  `application`, `list`, `parameter`, `std_message`, `sect`). These pass the inventory check but
  are not part of *this module's* business data. Drop the ones that are plainly framework/config
  unless the module genuinely reads them as business data.
- **Add real tables the inventory missed.** An inventory derived from a data-warehouse build
  won't contain every OLTP table — BOP-specific tables like `bopyearmember`, `partner`,
  `whitefile` showed up only as `dml-only` candidates, and `employer` showed up only as a column
  family (`em_*`). Treat strong column-family evidence as a reason to include a table even if the
  inventory didn't list it.

### 3 — Map the prefixes the script flagged

`unmapped_prefixes_for_human` lists column families the script wouldn't guess (an abbreviation or
initialism rather than a literal prefix of the table name). Map each to its table using the
column names, the SQL context, and domain sense. From the BOP run, the canonical examples:

| Prefix | Table | Why it isn't auto-mapped |
|---|---|---|
| `bym_*` | `bopyearmember` | initials of BOP-Year-Member |
| `cin_*` | `coincentive` | abbreviation, not a literal prefix |
| `cdn_*` | `codednote` | abbreviation |
| `wfl_*` | `whitefile` | abbreviation |
| `sbc_*` | `subcategory` | abbreviation |
| `par_*` | `partner` | table was dml-only |
| `rol_*` | `role` | table missed by inventory |
| `em_*`  | `employer` | table only present as a family |
| `tax_*` | `taxpayer` | ambiguous (`taxpayer` vs `taxpayerlock`) |
| `yea_*` | `year` | PB keyword collision truncated the table token |

Ignore genuine noise prefixes (short driver/log fragments like `ird`, `fsse`). When in doubt,
the cleaned column names in the family tell you what the table is.

### 4 — Write DRAFT business descriptions

For every kept table and every column without a rule-based description, write a short business
description from the naming and the module's purpose. The script already filled audit/key columns
(`*_serial`, `*_timestamp`, `*_userid`, `*_ref`, …) via suffix rules — leave those unless wrong.
Keep descriptions factual and concise; you are seeding a catalogue, not writing prose. Where you
are genuinely unsure, keep `(to confirm with the Data Owner)` rather than guessing — an honest gap
is more useful to a reviewer than a confident error.

### 5 — Apply the verification gate before publishing

This is the rule that keeps the catalogue trustworthy, and it is non-negotiable for anything that
will drive a model or a hand-over: descriptions recovered from code are **DRAFT** until verified
against an authoritative source — the Data Owner, a data dictionary, or arithmetic against the
actual data once a connection exists. Mark the output `DRAFT`/`status: DRAFT` and say plainly what
still needs confirming. Two specifics that always need verifying:

- **Data types.** `inferredType` is a hint from the column name only. The *authoritative* type
  comes from the OpenMetadata database connector (or the DDL). Don't present inferred types as fact.
- **FK / lineage edges** you assert beyond the obvious `*_ref`/`*_taxref` conventions.

### 6 — Produce the final artifacts

Finalise `<Module>_OpenMetadata.yaml` (set the real `service`, fill `application.description`,
replace every `TODO`/`(to confirm)` you resolved, keep `confirmedAgainstInventory` honest) and the
`.md` review sheet. The YAML is structured to be uploaded to OpenMetadata as a semantic enrichment:
`application.usesTables` seeds the app→table lineage; each `tables[].columns[]` carries the
description. Hand both to the catalogue team — YAML to load, markdown to review.

### 7 — Commit the result to version control

The job isn't done when the files exist — it's done when they're **committed**. A recovered
semantic enrichment is platform metadata; it belongs in the versioned catalogue repository
alongside every other module's, so it has history, review and a single source of truth. Save the
finalised `.yaml` and `.md` into the repo's module-semantics area and commit them with a clear
message (e.g. `catalogue: add <Module> semantic enrichment (DRAFT, NN tables/MM cols)`).

Important Cowork detail: the Cowork sandbox **cannot delete files on the workstation**, so an
in-sandbox `git` strands lock files. Run git **on the machine** instead — via Desktop Commander or
a terminal — on whichever OS the team member uses:

```bash
# macOS / Linux
cd "<repo>/<catalogue-path>" && git add <Module>_OpenMetadata.* && \
  git commit -m "catalogue: add <Module> semantic enrichment (DRAFT)"
```
```powershell
# Windows (PowerShell)
cd "<repo>\<catalogue-path>"; git add <Module>_OpenMetadata.*; `
  git commit -m "catalogue: add <Module> semantic enrichment (DRAFT)"
```

Committing is for traceability, not a substitute for the verification gate in step 5 — the
description stays **DRAFT** in the commit until a Data Owner verifies it. Open a PR if the repo
uses review.

## OpenMetadata output contract

```yaml
service: <om-database-service>          # set to the real service before loading
application:
  name: <Module>
  description: <what the module does>
  usesTables: [ ... ]                    # lineage seed: this app reads/writes these tables
tables:
  - name: <table>
    description: <business description>   # DRAFT until verified
    confirmedAgainstInventory: true|false
    columns:
      - name: <column>
        description: <business description>
        inferredType: <hint only — connector is authoritative>
```

## Reference material

- `references/powerbuilder-extraction-notes.md` — how PowerBuilder stores tables/columns
  (UTF-16LE, DataWindow `dbname=`, prefix conventions, compute-copy `c*` families) and the
  heuristics the script encodes. Read this if the script under-/over-extracts on a new module and
  you need to adjust, or to understand a confusing family.
- `references/bop-worked-example.md` — the finished BOP Registration enrichment (25 tables /
  141 columns). Use it as the quality bar for what a completed output should look like.

## Adapting to non-PowerBuilder legacy modules

The workflow generalises: decode the source, find table/column references, cross-check an
inventory, group columns, auto-map the easy ones, finish by judgement, verify before publishing.
For a different stack (Oracle Forms, COBOL copybooks, VB6), the decode and reference-extraction
regexes in `scripts/extract_pb_tables.py` are the parts to adapt — the rest of the method and the
OpenMetadata output contract stay the same.
