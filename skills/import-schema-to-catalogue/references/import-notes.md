# Import notes — schema spec, types, and vocabularies

## The schema spec (input)

The same JSON `onboard-source`'s `profile_source.py --emit-schema` writes:

```json
{
  "source": "ird",
  "tables": {
    "taxpayer": {
      "row_count": 1234567,
      "primary_key": ["tax_serial"],
      "columns": [
        {"name": "tax_serial",  "type": "serial",       "nullable": false},
        {"name": "tax_balance", "type": "decimal(16,2)", "nullable": true}
      ]
    }
  }
}
```

You can also hand-build one (e.g. from a DDL dump or a Visual Expert export) — only `source`,
`tables.<t>.columns[].name/type/nullable` are required; `row_count`/`primary_key` enrich the output.

## Type mapping (source → ClickHouse Bronze)

The `meta.ch_type` in the sources file and the `dataType` in the technical import use this map (it
mirrors the Bronze DDL generator so the catalogue and the warehouse agree):

| Source type | ClickHouse |
|---|---|
| `serial`, `int8`, `bigint` | `Int64` |
| `int`, `integer` | `Int32` |
| `smallint` | `Int16` |
| `decimal(p,s)`, `numeric(p,s)`, `money` | **`Decimal(38, s)`** (widened; never 18) |
| `smallfloat`, `real` | `Float32` |
| `float`, `double` | `Float64` |
| `date` | `Date32` |
| `datetime…`, `timestamp` | `DateTime64(3)` |
| `char/varchar/lvarchar/nchar/nvarchar/text/clob` | `String` |
| `bool*` | `Bool` |
| anything else | `String` (never silently dropped) |

OpenMetadata's ClickHouse connector reads the **live** types from the warehouse and is authoritative;
this import just seeds the structure and gives descriptions somewhere to hang before they're verified.

## Identifying reference (code/lookup) tables

A reference table is small and maps a code to a label (status, category, reason, role, country,
locality…). Signs: low row count, a short code column + a name/description column, referenced by FK
columns elsewhere (`*_ref`, `*ref`). Turn each into a vocabulary with `--vocab`. These are exactly the
tables whose codes should drive `accepted_values` validity tests — so the operational data can't carry
a code the vocabulary doesn't know.

## How a vocabulary feeds the rest

`catalogue/vocabularies/<name>.yml` carries:
- `terms` — the `code → label` pairs (deduplicated, blanks dropped, sorted) for the OpenMetadata
  glossary and for human reference.
- `accepted_values` — just the codes, ready to paste into an `add-dq-checks` `enums:` block:

```yaml
# in the DQ spec for a model that has a status column:
enums:
  status_code: ["1", "2", "3"]     # <- from catalogue/vocabularies/taxpayer_status.yml
```

That closes the loop: the reference table defines the vocabulary, the vocabulary drives the validity
gate, and a value outside it fails `dbt test`.

## What this skill does NOT do

- It does not write business descriptions — those are DRAFT here and become VERIFIED via
  `verify-catalogue-semantics` (with evidence).
- It does not load data — `onboard-source` does the gated load; this consumes the schema spec only.
- It does not override live types — the OM connector is authoritative; this seeds structure.
