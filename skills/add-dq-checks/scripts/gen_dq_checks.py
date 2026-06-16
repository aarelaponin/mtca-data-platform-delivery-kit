#!/usr/bin/env python3
"""
gen_dq_checks.py — generate six-dimension data-quality checks for a model (per the MTCA DQF).

From a compact spec it emits, all tagged by DQF dimension so the reconciler can roll them up to
the 0-100 quality badge:
  - a dbt schema test file  <model>.dq.yml   — column + model tests (unique, not_null,
    accepted_values, range, relationships), each tagged `dq:<dimension>` + meta;
  - dbt singular tests       tests/<model>__*.sql — freshness (timeliness), zero-row / row-budget
    (completeness), and an accuracy-reconciliation stub;
  - a threshold config       quality/thresholds/<model>.yml — the per-dimension PoC/Full targets
    the reconciler scores against (DQF defaults; confirm with the Data Owners).

Dimension → DQF control mapping (see references/dq-dimension-map.md):
  Completeness→not_null/zero-row/row-budget (DQC-S2-03, S3-02, S4-05); Validity→accepted_values/
  range (DQC-S4-02); Consistency→relationships (DQC-S4-03); Uniqueness→unique@grain (DQC-S4-01);
  Timeliness→freshness vs tier SLA (DQC-S4-04); Accuracy→cross-source reconciliation (DQC-S6-01).

Deterministic, offline, pure standard library. Generated files are drafts for review + `dbt test`;
never hand-edit — change the spec and regenerate.

Usage:
  python gen_dq_checks.py --spec dq.yml --repo <repo-root>     # writes into the repo
  python gen_dq_checks.py --spec dq.yml --print                # review on stdout
"""
import argparse, json, os, sys

# Tier freshness SLAs (DQF §3 Full targets), in minutes.
TIER_SLA_MIN = {"hot": 5, "warm": 60, "cold": 1440, "archive": 10080}
# DQF proposed PoC / Full targets per dimension (placeholders to confirm with Data Owners).
DQF_TARGETS = {
    "completeness": {"poc": "≥95% mandatory fill; ≥99% rows reconciled", "full": "≥99% fill; 100% reconciled"},
    "validity":     {"poc": "≥99% rows pass validity", "full": "≥99.5%"},
    "accuracy":     {"poc": "reconciliations defined & measured", "full": "tolerance bands agreed & met"},
    "consistency":  {"poc": "≥98% cross-reference match", "full": "+ cross-DB FK ≥ agreed floor"},
    "uniqueness":   {"poc": "<1% duplicates; 100% at grain post-dedup", "full": "100%"},
    "timeliness":   {"poc": "freshness visible; tier SLAs defined", "full": "per-tier SLAs met"},
}

def load_spec(path):
    txt = open(path, encoding="utf-8").read()
    try:
        import yaml; return yaml.safe_load(txt)
    except Exception:
        try: return json.loads(txt)
        except Exception: sys.exit("Could not parse spec (install pyyaml or use JSON).")

# ---- YAML emitter: PyYAML if present, else JSON (which is valid YAML, so dbt parses it) ----
def dump_yaml(obj):
    try:
        import yaml
        return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)
    except Exception:
        return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

def cfg(dim, **extra):
    meta = {"dq_dimension": dim}; meta.update(extra)
    return {"config": {"tags": [f"dq:{dim}"], "meta": meta}}

# ---------------------------------------------------------------- schema tests
def build_schema_yml(spec, model):
    grain = spec.get("grain", [])
    mandatory = spec.get("mandatory", [])
    enums = spec.get("enums", {}) or {}
    ranges = spec.get("ranges", {}) or {}
    rels = spec.get("relationships", []) or []
    colmap = {}

    def col(name): return colmap.setdefault(name, {"name": name, "tests": []})

    for g in grain:                                   # Uniqueness + not-null on grain
        c = col(g)
        c["tests"].append({"unique": cfg("uniqueness", control="DQC-S4-01")})
        c["tests"].append({"not_null": cfg("completeness", control="DQC-S4-01")})
    for m in mandatory:                               # Completeness
        if m not in grain:
            col(m)["tests"].append({"not_null": cfg("completeness", control="DQC-S4-02")})
    for cname, vals in enums.items():                 # Validity (enum membership)
        d = cfg("validity", control="DQC-S4-02"); d["values"] = list(vals)
        col(cname)["tests"].append({"accepted_values": d})
    for cname, rng in ranges.items():                 # Validity (range; needs dbt_expectations)
        d = cfg("validity", control="DQC-S4-02")
        if "min" in rng: d["min_value"] = rng["min"]
        if "max" in rng: d["max_value"] = rng["max"]
        col(cname)["tests"].append({"dbt_expectations.expect_column_values_to_be_between": d})
    for r in rels:                                    # Consistency (referential)
        d = cfg("consistency", control="DQC-S4-03"); d["to"] = r["to"]; d["field"] = r["field"]
        col(r["column"])["tests"].append({"relationships": d})

    model_obj = {"name": model,
                 "description": spec.get("description", f"DQ checks for {model}."),
                 "columns": list(colmap.values())}
    return dump_yaml({"version": 2, "models": [model_obj]}) + "\n"

# ---------------------------------------------------------------- singular tests
def singular_freshness(spec, model):
    tier = (spec.get("tier") or "warm").lower()
    sla = TIER_SLA_MIN.get(tier, 60)
    col = (spec.get("freshness") or {}).get("column", "_extracted_at")
    return (f"{{{{ config(tags=['dq:timeliness'], meta={{'dq_dimension':'timeliness','control':'DQC-S4-04','tier':'{tier}'}}) }}}}\n"
            f"-- Timeliness: fails if the freshest row is older than the {tier} SLA ({sla} min).\n"
            f"select max(`{col}`) as freshest\n"
            f"from {{{{ ref('{model}') }}}}\n"
            f"having now() - max(`{col}`) > interval {sla} minute\n")

def singular_rowbudget(spec, model):
    min_rows = (spec.get("row_budget") or {}).get("min_rows", 1)
    return (f"{{{{ config(tags=['dq:completeness'], meta={{'dq_dimension':'completeness','control':'DQC-S3-02'}}) }}}}\n"
            f"-- Completeness: zero-row / row-budget gate — fails if the table has fewer than {min_rows} rows.\n"
            f"select count(*) as n\n"
            f"from {{{{ ref('{model}') }}}}\n"
            f"having count(*) < {min_rows}\n")

def singular_accuracy(spec, model, acc):
    name = acc["name"]
    return (f"{{{{ config(tags=['dq:accuracy'], meta={{'dq_dimension':'accuracy','control':'DQC-S6-01','recon':'{name}'}}) }}}}\n"
            f"-- Accuracy reconciliation: {acc.get('description','TODO')}\n"
            f"-- TODO: replace with the real cross-source comparison (declared vs authoritative aggregate,\n"
            f"--       within an agreed tolerance). Until then this is an OPEN control, not a green check.\n"
            f"-- Track it in quality/thresholds/{model}.yml (accuracy: not_implemented).\n"
            f"select 1 as failing\nwhere 1 = 0   -- <- placeholder; implement the reconciliation\n")

# ---------------------------------------------------------------- thresholds config
def build_thresholds(spec, model):
    dims = {}
    for d, t in DQF_TARGETS.items():
        dims[d] = {"poc_target": t["poc"], "full_target": t["full"]}
    if spec.get("accuracy"):
        dims["accuracy"]["status"] = "not_implemented (reconciliation stub generated)"
    obj = {"model": model, "tier": (spec.get("tier") or "warm"),
           "note": "DQF proposed targets — CONFIRM with Data Owners & DGC.",
           "dimensions": dims}
    return dump_yaml(obj) + "\n"

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--repo", help="repo root: writes dbt/models/_dq, dbt/tests, quality/thresholds")
    ap.add_argument("--print", action="store_true", dest="to_stdout", help="print everything to stdout")
    args = ap.parse_args()
    spec = load_spec(args.spec)
    model = spec.get("model") or sys.exit("spec needs a 'model' field")

    schema = build_schema_yml(spec, model)
    singulars = {f"{model}__freshness.sql": singular_freshness(spec, model),
                 f"{model}__row_budget.sql": singular_rowbudget(spec, model)}
    for acc in spec.get("accuracy", []) or []:
        singulars[f"{model}__accuracy_{acc['name']}.sql"] = singular_accuracy(spec, model, acc)
    thresholds = build_thresholds(spec, model)

    if args.to_stdout or not args.repo:
        print("==== %s.dq.yml ====\n%s" % (model, schema))
        for n, s in singulars.items(): print("==== tests/%s ====\n%s" % (n, s))
        print("==== quality/thresholds/%s.yml ====\n%s" % (model, thresholds))
        return

    md = os.path.join(args.repo, "dbt", "models", "_dq"); os.makedirs(md, exist_ok=True)
    td = os.path.join(args.repo, "dbt", "tests"); os.makedirs(td, exist_ok=True)
    qd = os.path.join(args.repo, "quality", "thresholds"); os.makedirs(qd, exist_ok=True)
    open(os.path.join(md, f"{model}.dq.yml"), "w", encoding="utf-8", newline="\n").write(schema)
    for n, s in singulars.items():
        open(os.path.join(td, n), "w", encoding="utf-8", newline="\n").write(s)
    open(os.path.join(qd, f"{model}.yml"), "w", encoding="utf-8", newline="\n").write(thresholds)
    print(f"wrote dbt/models/_dq/{model}.dq.yml, {len(singulars)} singular tests, quality/thresholds/{model}.yml")

if __name__ == "__main__":
    main()
