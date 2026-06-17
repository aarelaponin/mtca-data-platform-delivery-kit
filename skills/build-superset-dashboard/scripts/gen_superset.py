#!/usr/bin/env python3
"""
gen_superset.py — spec -> Superset dataset (virtual dataset + metrics) + a dashboard manifest.

Builds the consumption surface over a Gold mart: a Superset **dataset** (the SQL the dashboard reads,
plus calculated columns and metrics — one semantic definition, reused by every chart) and a
**dashboard manifest** (the charts, their RBAC roles, and threshold alerts). The dataset is emitted
in Superset's import shape; the dashboard manifest is the chart/layout spec the team realises in
Superset (layouts are positional and best assembled in the UI from these definitions).

Why a dataset with metrics rather than raw SQL per chart: define `total_outstanding`,
`debt_to_assessment` etc. ONCE on the dataset, and every chart (and the API, and SAS) uses the same
definition — no metric drifts between the dashboard and the API.

Deterministic, offline, pure standard library (PyYAML if present, else JSON — valid YAML).

Usage:
  python gen_superset.py --spec dashboard.yml --repo <repo-root>
  python gen_superset.py --spec dashboard.yml --print
"""
import argparse, json, os, re, sys, uuid, datetime

def load(p):
    txt = open(p, encoding="utf-8").read()
    try:
        import yaml; return yaml.safe_load(txt)
    except Exception:
        try: return json.loads(txt)
        except Exception: sys.exit("Could not parse spec (install pyyaml or use JSON).")

def dump_yaml(obj):
    try:
        import yaml; return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)
    except Exception:
        return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

def slug(s): return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')

# ----------------------------------------------------------------- dataset (Superset import shape)
def build_dataset(ds):
    name = ds["name"]
    mart = ds.get("mart")
    schema = ds.get("schema", "gold")
    sql = ds.get("sql") or (f"select * from {schema}.{mart}" if mart else None)
    if not sql:
        sys.exit(f"dataset {name}: provide 'mart' or 'sql'")
    columns = []
    for c in ds.get("columns", []):
        columns.append({"column_name": c, "is_dttm": c in ds.get("time_columns", []), "type": "VARCHAR"})
    for cc in ds.get("calculated", []):                       # calculated columns (expressions)
        columns.append({"column_name": cc["name"], "expression": cc["expression"],
                        "description": cc.get("description", ""), "is_dttm": False})
    metrics = []
    for m in ds.get("metrics", []):                           # reusable metrics
        metrics.append({"metric_name": m["name"], "expression": m["expression"],
                        "description": m.get("description", ""),
                        "extra": json.dumps({"dq_note": "one definition, reused everywhere"})})
    return {"version": "1.0.0", "uuid": str(uuid.uuid4()),
            "table_name": name, "schema": schema, "sql": sql.strip(),
            "main_dttm_col": (ds.get("time_columns") or [None])[0],
            "database_uuid": "REPLACE_ON_IMPORT", "cache_timeout": ds.get("cache_timeout"),
            "columns": columns, "metrics": metrics}

# ----------------------------------------------------------------- dashboard manifest
CHART_TYPES = {"bar": "dist_bar", "line": "line", "table": "table", "big_number": "big_number_total",
               "pie": "pie", "area": "area"}

def build_dashboard(spec, dataset_names):
    charts = []
    for ch in spec.get("charts", []):
        dsname = ch.get("dataset")
        if dsname not in dataset_names:
            sys.exit(f"chart '{ch.get('name')}' references unknown dataset '{dsname}'")
        viz = CHART_TYPES.get(ch.get("type", "table"), "table")
        charts.append({"name": ch["name"], "viz_type": viz, "dataset": dsname,
                       "metric": ch.get("metric"), "dimension": ch.get("dimension"),
                       "columns": ch.get("columns"), "filters": ch.get("filters", []),
                       "row_limit": ch.get("row_limit", 1000)})
    alerts = []
    for a in spec.get("alerts", []):
        alerts.append({"name": a["name"], "dataset": a.get("dataset"), "metric": a.get("metric"),
                       "condition": a.get("condition"), "threshold": a.get("threshold"),
                       "note": a.get("note", "")})
    return {"dashboard_title": spec["dashboard"],
            "slug": slug(spec["dashboard"]),
            "_meta": {"generated": str(datetime.date.today()),
                      "note": "Charts + RBAC + alerts. Realise the layout in Superset from these chart "
                              "definitions; datasets import directly."},
            "rbac_roles": spec.get("rbac", {}).get("roles", []),
            "charts": charts, "alerts": alerts}

# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--repo"); ap.add_argument("--print", action="store_true", dest="to_stdout")
    args = ap.parse_args()
    spec = load(args.spec)
    if "dashboard" not in spec or "dataset" not in spec:
        sys.exit("spec needs 'dashboard' and at least one 'dataset'")
    datasets = spec["dataset"]
    datasets = datasets if isinstance(datasets, list) else [datasets]
    built = [build_dataset(d) for d in datasets]
    names = {d["table_name"] for d in built}
    dash = build_dashboard(spec, names)

    if args.to_stdout or not args.repo:
        for d in built: print(f"==== dataset {d['table_name']}.yaml ====\n" + dump_yaml(d))
        print("==== dashboard manifest ====\n" + dump_yaml(dash)); return

    base = os.path.join(args.repo, "consumption", "dashboards", dash["slug"]); os.makedirs(base, exist_ok=True)
    for d in built:
        open(os.path.join(base, f"dataset_{d['table_name']}.yaml"), "w", encoding="utf-8").write(dump_yaml(d))
    open(os.path.join(base, "dashboard.yaml"), "w", encoding="utf-8").write(dump_yaml(dash))
    print(f"wrote consumption/dashboards/{dash['slug']}/ : {len(built)} dataset(s) + dashboard.yaml "
          f"({len(dash['charts'])} charts, {len(dash['alerts'])} alerts)")

if __name__ == "__main__":
    main()
