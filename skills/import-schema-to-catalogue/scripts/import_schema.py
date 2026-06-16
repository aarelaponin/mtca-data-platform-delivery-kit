#!/usr/bin/env python3
"""
import_schema.py — source schema spec -> dbt sources.yml + OpenMetadata technical metadata
                   (+ reference-data vocabularies from a code table).

This is the *technical* half of cataloguing a source (DQC-S1-01: schema capture into the catalogue
at onboarding). It consumes the schema spec that `profile_source.py --emit-schema` produces (or a
hand-built one) and wires the source into the platform:

  default (schema mode):
    --schema schema_<src>.json --repo <repo>
      writes  dbt/models/_sources/<src>__sources.yml   (so staging can {{ source() }} + lineage)
        and   catalogue/import/<src>_technical.yaml      (OM technical metadata: CH types, nullability)

  --vocab (reference-data mode):
    --vocab --data ref.csv --code-col CODE --label-col LABEL --name <vocab>
      writes  catalogue/vocabularies/<vocab>.yml         (code->label terms + a ready accepted_values
                                                          list to drop into add-dq-checks validity)

Business *meaning* is NOT this skill's job — descriptions stay TODO/DRAFT here and are confirmed by
`verify-catalogue-semantics`. This skill establishes the structure: sources, technical types, and the
controlled vocabularies that downstream validity tests check against.

Pure standard library (uses PyYAML if present, else emits JSON — valid YAML, so dbt/OM parse it).
"""
import argparse, csv, json, os, re, sys, datetime

def dump_yaml(obj):
    try:
        import yaml
        return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)
    except Exception:
        return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

# Source type -> ClickHouse Bronze type (mirror of gen_bronze_ddl; money widened to Decimal(38,s)).
def ch_type(src_type):
    t = str(src_type).strip().lower()
    m = re.search(r'(?:decimal|numeric)\s*\(\s*\d+\s*,\s*(\d+)\s*\)', t)
    if m: return f"Decimal(38, {int(m.group(1))})"
    if t.startswith(("decimal", "numeric")) or "money" in t: return "Decimal(38, 4)"
    if "serial" in t or t in ("int8", "bigint"): return "Int64"
    if t.startswith("int") or t == "integer": return "Int32"
    if "smallint" in t: return "Int16"
    if "smallfloat" in t or t == "real": return "Float32"
    if "float" in t or "double" in t: return "Float64"
    if t.startswith("date") and "time" not in t: return "Date32"
    if "datetime" in t or "timestamp" in t: return "DateTime64(3)"
    if any(t.startswith(p) for p in ("char", "varchar", "nchar", "nvarchar", "lvarchar", "text", "string", "clob")):
        return "String"
    if "bool" in t: return "Bool"
    return "String"

# ----------------------------------------------------------------- dbt sources.yml
def build_sources(spec):
    source = spec["source"]
    tables = []
    for tname in sorted(spec["tables"]):
        t = spec["tables"][tname]
        cols = [{"name": c["name"],
                 "description": "TODO — verify via verify-catalogue-semantics.",
                 "meta": {"source_type": c.get("type", ""), "ch_type": ch_type(c.get("type", ""))}}
                for c in t.get("columns", [])]
        tbl = {"name": f"{source}__{tname}",
               "description": f"Bronze copy of {source}.{tname} (raw, as-ingested).",
               "columns": cols}
        if isinstance(t.get("row_count"), int):
            tbl["meta"] = {"source_row_count_at_onboard": t["row_count"]}
        tables.append(tbl)
    return dump_yaml({"version": 2,
                      "sources": [{"name": "bronze", "schema": "bronze",
                                   "description": f"Raw, as-ingested layer for source '{source}' (Informix -> ClickHouse).",
                                   "tables": tables}]})

# ----------------------------------------------------------------- OM technical import
def build_technical(spec, service):
    source = spec["source"]
    tables = []
    for tname in sorted(spec["tables"]):
        t = spec["tables"][tname]
        cols = [{"name": c["name"], "dataType": ch_type(c.get("type", "")),
                 "nullable": bool(c.get("nullable", True)),
                 "sourceType": c.get("type", ""), "description": ""}
                for c in t.get("columns", [])]
        tables.append({"name": f"{source}__{tname}", "description": "", "columns": cols})
    return dump_yaml({"service": service, "database": "bronze", "schema": "bronze",
                      "_meta": {"generated": str(datetime.date.today()),
                                "note": "Technical metadata only; OM's ClickHouse connector is authoritative for types. "
                                        "Business descriptions are added/verified separately."},
                      "tables": tables})

# ----------------------------------------------------------------- reference vocabulary
def build_vocab(data_csv, code_col, label_col, name):
    terms, seen = [], set()
    with open(data_csv, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        for col in (code_col, label_col):
            if col not in rd.fieldnames:
                sys.exit(f"column '{col}' not in {data_csv} (have: {rd.fieldnames})")
        for row in rd:
            code = (row.get(code_col) or "").strip()
            if code == "" or code in seen:
                continue
            seen.add(code)
            terms.append({"code": code, "label": (row.get(label_col) or "").strip()})
    terms.sort(key=lambda x: x["code"])
    return dump_yaml({"vocabulary": name, "source_table": os.path.basename(data_csv),
                      "term_count": len(terms),
                      "accepted_values": [t["code"] for t in terms],   # paste into add-dq-checks enums
                      "terms": terms})

# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", help="schema spec JSON (from profile_source --emit-schema)")
    ap.add_argument("--repo", help="repo root: writes dbt/models/_sources and catalogue/import")
    ap.add_argument("--service", default="mtca-clickhouse", help="OM service name for the technical import")
    ap.add_argument("--vocab", action="store_true", help="reference-data vocabulary mode")
    ap.add_argument("--data"); ap.add_argument("--code-col"); ap.add_argument("--label-col"); ap.add_argument("--name")
    ap.add_argument("-o", "--out", help="single-file output (stdout if omitted)")
    args = ap.parse_args()

    if args.vocab:
        if not (args.data and args.code_col and args.label_col and args.name):
            sys.exit("--vocab needs --data --code-col --label-col --name")
        out = build_vocab(args.data, args.code_col, args.label_col, args.name)
        if args.repo:
            d = os.path.join(args.repo, "catalogue", "vocabularies"); os.makedirs(d, exist_ok=True)
            p = os.path.join(d, f"{args.name}.yml"); open(p, "w", encoding="utf-8").write(out); print("wrote", p)
        elif args.out:
            open(args.out, "w", encoding="utf-8").write(out); print("wrote", args.out)
        else:
            sys.stdout.write(out)
        return

    if not args.schema:
        ap.error("provide --schema (schema mode) or --vocab (reference-data mode)")
    spec = json.load(open(args.schema, encoding="utf-8"))
    sources = build_sources(spec); technical = build_technical(spec, args.service)
    src = spec["source"]
    if args.repo:
        sd = os.path.join(args.repo, "dbt", "models", "_sources"); os.makedirs(sd, exist_ok=True)
        cd = os.path.join(args.repo, "catalogue", "import"); os.makedirs(cd, exist_ok=True)
        open(os.path.join(sd, f"{src}__sources.yml"), "w", encoding="utf-8").write(sources)
        open(os.path.join(cd, f"{src}_technical.yaml"), "w", encoding="utf-8").write(technical)
        print(f"wrote dbt/models/_sources/{src}__sources.yml and catalogue/import/{src}_technical.yaml "
              f"({len(spec['tables'])} tables)")
    else:
        print("==== dbt sources.yml ====\n" + sources)
        print("==== OM technical.yaml ====\n" + technical)

if __name__ == "__main__":
    main()
