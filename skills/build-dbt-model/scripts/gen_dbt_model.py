#!/usr/bin/env python3
"""
gen_dbt_model.py — generate a dbt model (SQL + schema YAML with tests) from a compact spec.

Covers the five-layer medallion's three authored layers:
  - kind: staging       stg_<source>__<entity>   one model per source table; cast/rename only, NO joins
  - kind: intermediate  int_<domain>__<concept>   the explicit join / golden-record layer; join keys
                                                   get not_null + relationships tests (the join CONTRACT)
  - kind: mart          mart_<domain>__<desc>      consumer-facing; composes from int_, never re-joins raw

The point of the int_ layer is that cross-source joins are declared as named, contract-tested models
(so lineage is legible and a broken join fails a test, not a dashboard). Marts compose from int_.

Deterministic, offline, pure standard library (uses PyYAML if present, else reads/writes JSON-ish
YAML it can parse itself for the simple spec shape). Generated files are drafts for review +
`dbt build`; never hand-edit them afterwards — change the spec and regenerate.

Usage:
  python gen_dbt_model.py --spec model.yml --out <repo>/dbt/models
"""
import argparse, json, os, re, sys

# --------------------------------------------------------------------- spec loading
def load_spec(path):
    txt = open(path, encoding="utf-8").read()
    try:
        import yaml
        return yaml.safe_load(txt)
    except Exception:
        pass
    try:
        return json.loads(txt)
    except Exception:
        sys.exit("Could not parse spec. Install PyYAML (pip install pyyaml) or provide JSON.")

LAYER_DIR = {"staging": "staging", "intermediate": "intermediate", "mart": "marts"}

def derive_name(spec):
    if spec.get("name"):
        return spec["name"]
    k = spec["kind"]
    if k == "staging":
        return f"stg_{spec['source']}__{spec['table']}"
    if k == "intermediate":
        return f"int_{spec['domain']}__{spec.get('concept','master')}"
    return f"mart_{spec['domain']}__{spec['desc']}"

# --------------------------------------------------------------------- SQL builders
def sql_staging(spec, name):
    src = f"{{{{ source('{spec.get('bronze_schema','bronze')}', '{spec['source']}__{spec['table']}') }}}}"
    sel = []
    for c in spec["columns"]:
        if isinstance(c, str):
            sel.append(f"    `{c}`")
        else:
            expr = f"`{c['src']}`"
            if c.get("cast"):
                expr = f"cast({expr} as {c['cast']})"
            sel.append(f"    {expr} as `{c.get('as', c['src'])}`")
    return (f"-- {name}  (staging: 1:1 clean of one source table, no joins)\n"
            f"with source as (\n    select * from {src}\n)\n"
            f"select\n" + ",\n".join(sel) + "\nfrom source\n")

def sql_intermediate(spec, name):
    base = spec["base"]
    ctes = [f"{base} as (\n    select * from {{{{ ref('{base}') }}}}\n)"]
    joins_sql = []
    for j in spec.get("joins", []):
        m = j["model"]
        # NB: YAML parses a bare `on:` key as boolean True — accept either spelling.
        on_clause = j.get("on", j.get(True))
        if not on_clause:
            sys.exit(f"join on {m} is missing its 'on:' clause (tip: quote it as \"on\": in YAML).")
        ctes.append(f"{m} as (\n    select * from {{{{ ref('{m}') }}}}\n)")
        joins_sql.append(f"{j.get('type','left')} join {m} on {on_clause}")
    sel = [f"    {c}" for c in spec["select"]]
    body = (f"select\n" + ",\n".join(sel) + f"\nfrom {base}\n" +
            ("\n".join(joins_sql) + "\n" if joins_sql else ""))
    return (f"-- {name}  (intermediate: explicit joins / golden record; join keys are contract-tested)\n"
            f"with " + ",\n".join(ctes) + "\n" + body)

def sql_mart(spec, name):
    frm = spec["from"]
    sel = [f"    {c}" for c in spec["select"]] if spec.get("select") else ["    *"]
    return (f"-- {name}  (mart: consumer-facing; composes from int_, does not re-join raw sources)\n"
            f"with base as (\n    select * from {{{{ ref('{frm}') }}}}\n)\n"
            f"select\n" + ",\n".join(sel) + "\nfrom base\n")

BUILDERS = {"staging": sql_staging, "intermediate": sql_intermediate, "mart": sql_mart}

# --------------------------------------------------------------------- schema YAML (tests)
def schema_yaml(spec, name):
    import collections
    cols = collections.OrderedDict()   # name -> {"description":..., "tests":[...]}
    key = spec.get("key")

    def ensure(colname, desc=None):
        e = cols.setdefault(colname, {"description": "TODO — describe.", "tests": []})
        if desc and e["description"].startswith("TODO"):
            e["description"] = desc
        return e

    def add_test(e, t):
        if t not in e["tests"]:
            e["tests"].append(t)

    if key:
        e = ensure(key, "Grain / primary key.")
        add_test(e, "unique"); add_test(e, "not_null")
    # join contracts: each join key gets not_null + a relationships test (merged onto the key if same col)
    for rel in spec.get("relationships", []):
        e = ensure(rel["column"], "Join key — contract-tested against the parent.")
        add_test(e, "not_null")
        add_test(e, {"relationships": {"to": rel["to"], "field": rel["field"]}})
    # any explicitly listed columns carrying their own tests
    for c in spec.get("columns", []):
        if isinstance(c, dict) and c.get("tests"):
            e = ensure(c.get("as", c.get("src")))
            for t in c["tests"]:
                add_test(e, t)

    collist = []
    for n, meta in cols.items():
        entry = {"name": n, "description": meta["description"]}
        if meta["tests"]:
            entry["tests"] = meta["tests"]
        collist.append(entry)
    model = {"name": name,
             "description": spec.get("description", f"TODO — what {name} represents."),
             "columns": collist or [{"name": key or "TODO", "description": "TODO"}]}
    doc = {"version": 2, "models": [model]}
    try:
        import yaml
        return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False, width=100)
    except Exception:
        return _mini_yaml(doc)

def _mini_yaml(o, ind=0):
    pad = "  " * ind; out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                out.append(f"{pad}{k}:"); out.append(_mini_yaml(v, ind + 1))
            else:
                out.append(f"{pad}{k}: {v}")
    elif isinstance(o, list):
        for it in o:
            if isinstance(it, dict):
                first = True
                for k, v in it.items():
                    lead = "- " if first else "  "
                    first = False
                    if isinstance(v, (dict, list)):
                        out.append(f"{pad}{lead}{k}:"); out.append(_mini_yaml(v, ind + 2))
                    else:
                        out.append(f"{pad}{lead}{k}: {v}")
            else:
                out.append(f"{pad}- {it}")
    return "\n".join(x for x in out if x)

# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", help="dbt models dir (writes <layer>/<name>.sql + .yml); else stdout")
    args = ap.parse_args()
    spec = load_spec(args.spec)
    kind = spec.get("kind")
    if kind not in BUILDERS:
        sys.exit("spec needs kind: staging | intermediate | mart")
    name = derive_name(spec)
    sql = BUILDERS[kind](spec, name)
    yml = schema_yaml(spec, name)

    if args.out:
        d = os.path.join(args.out, LAYER_DIR[kind]); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, name + ".sql"), "w", encoding="utf-8", newline="\n").write(sql)
        open(os.path.join(d, name + ".yml"), "w", encoding="utf-8", newline="\n").write(yml)
        print(f"wrote {LAYER_DIR[kind]}/{name}.sql and .yml")
    else:
        print("=" * 8, name + ".sql", "=" * 8); print(sql)
        print("=" * 8, name + ".yml", "=" * 8); print(yml)

if __name__ == "__main__":
    main()
