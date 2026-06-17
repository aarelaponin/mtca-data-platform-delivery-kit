#!/usr/bin/env python3
"""
gen_consumer_plan.py — serve a new consumer from the platform: gap analysis -> plan + checklist.

The Data Platform is comprehensive and serves many consumers in sequence: Debt Management (low-code)
was the first; the SAS risk project is the second; compliance, refunds, customs follow. Each is
onboarded the SAME way — capture its data needs, see what Gold already serves vs what must be built,
expose the surface it consumes (dashboard / API / Gold feed), set RBAC, and gate. This skill makes
that repeatable: it diffs a consumer's needs against the current mart inventory and emits a tailored
onboarding plan (referencing the other skills) plus the consumer's Definition-of-Done checklist.

The rule it encodes: consumers pull from Gold; no consumer gets a bespoke side-pipeline. A need that
isn't served becomes a mart/int_ model in the shared platform, reused by whoever needs it next.

  --spec consumer.yml --inventory marts.yml [--repo <root> | --print]

Deterministic, offline, pure standard library (PyYAML if present, else JSON).
"""
import argparse, json, os, re, sys, datetime

def load(p):
    txt = open(p, encoding="utf-8").read()
    try:
        import yaml; return yaml.safe_load(txt)
    except Exception:
        try: return json.loads(txt)
        except Exception: sys.exit(f"Could not parse {p} (install pyyaml or use JSON).")

def dump_yaml(obj):
    try:
        import yaml; return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)
    except Exception:
        return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

def slug(s): return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')

# --------------------------------------------------------- gap analysis
def gap(spec, inventory):
    # inventory: {marts: {mart_name: [columns...]}}
    marts = inventory.get("marts", {})
    field_index = {}                       # column -> [marts that expose it]
    for m, cols in marts.items():
        for c in (cols or []):
            field_index.setdefault(c, []).append(m)
    served, missing = {}, []
    for need in spec.get("needs", []):
        ent = need.get("entity", "?")
        for item in (need.get("fields", []) + need.get("metrics", [])):
            if item in field_index:
                served[item] = field_index[item]
            else:
                missing.append({"entity": ent, "item": item})
    return served, missing, field_index

# --------------------------------------------------------- plan
def build_plan(spec, served, missing, field_index):
    c = spec["consumer"]; name = c["name"]; surface = c.get("surface", "api")
    steps = []
    n = 1
    def step(s):
        nonlocal n; steps.append(f"{n}. {s}"); n += 1

    step(f"**Capture needs** — {name}: {sum(len(need.get('fields',[]))+len(need.get('metrics',[])) for need in spec.get('needs',[]))} "
         f"required field(s)/metric(s) across {len(spec.get('needs',[]))} entity group(s); surface = **{surface}**; "
         f"freshness tier = **{c.get('freshness','warm')}**.")
    if missing:
        miss_by_ent = {}
        for m in missing: miss_by_ent.setdefault(m["entity"], []).append(m["item"])
        step("**Close the gaps** — these needs are NOT yet in Gold; build them in the shared platform "
             "(never a side-pipeline):")
        for ent, items in miss_by_ent.items():
            steps.append(f"    - `{ent}`: {', '.join('`'+i+'`' for i in items)} → "
                         f"if the source isn't in Bronze, **onboard-source**; then **build-dbt-model** "
                         f"(extend an `int_`/`mart_`), **add-dq-checks**, **import-schema-to-catalogue** + "
                         f"**verify-catalogue-semantics**.")
    else:
        step("**Gaps** — none; every need is already served by an existing Gold mart (reuse, don't rebuild).")

    if surface == "dashboard":
        step("**Expose** — **build-superset-dashboard** over the serving mart(s): dataset + metrics + charts + RBAC + alerts.")
    elif surface == "api":
        step("**Expose** — **expose-api**: OpenAPI contract + parameterized SQL over the serving mart(s).")
    elif surface == "feed":
        step("**Expose** — Gold-layer **feed**: grant the consumer read on the serving mart(s) (no copy).")
        for wb in c.get("writes_back", []) or []:
            step(f"**Write-back** — model `{wb['mart']}` ({', '.join(wb.get('fields',[]))}) as a Gold mart "
                 f"(**build-dbt-model** + **add-dq-checks** + **verify-catalogue-semantics**); the consumer writes its "
                 f"outputs here, and downstream reads them like any other Gold mart.")

    step(f"**RBAC** — grant {', '.join('`'+r+'`' for r in spec.get('rbac', [])) or '(define roles)'}; "
         f"the surface inherits the data's classification (Restricted-by-default).")
    step("**Quality & catalogue gates** — DQ green on every consumed/written mart; catalogue VERIFIED for its columns.")
    step("**Production-readiness** — run **production-readiness-check** for the consumer release; sign-off gates go-live.")
    return steps, surface

# --------------------------------------------------------- checklist
def build_checklist(spec, missing):
    c = spec["consumer"]
    items = [
        ("needs-captured", "Consumer data needs captured (entities, fields, metrics, surface, freshness)", "pass"),
        ("gaps-resolved", f"All gaps resolved — {len(missing)} need(s) built into Gold" if missing
                          else "No gaps — all needs served by existing Gold marts",
         "pending" if missing else "pass"),
        ("surface-exposed", f"Consumption surface exposed ({c.get('surface','api')})", "pending"),
        ("writeback-wired", "Write-back mart(s) modelled, DQ'd and verified" if c.get("writes_back")
                            else "No write-back required", "pending" if c.get("writes_back") else "na"),
        ("rbac-set", "RBAC roles granted; classification inherited", "pending"),
        ("dq-green", "DQ gates green on every consumed/written mart", "pending"),
        ("catalogue-verified", "Catalogue VERIFIED for the consumed/written columns", "pending"),
        ("readiness", "production-readiness-check PASS for the consumer release", "pending"),
        ("sign-off", "Consumer sign-off recorded", "pending"),
    ]
    return [{"id": i, "item": t, "status": s} for i, t, s in items]

# --------------------------------------------------------- render
def render_md(spec, served, missing, steps, checklist):
    c = spec["consumer"]
    out = [f"# Consumer onboarding plan — {c['name']}",
           f"_{c.get('description','')}_\n",
           f"Generated {datetime.date.today()} · surface **{c.get('surface','api')}** · "
           f"served **{len(served)}** / missing **{len(missing)}** need(s).\n",
           "## Coverage", "", "| Need | Status | Served by |", "|---|---|---|"]
    for need in spec.get("needs", []):
        for item in need.get("fields", []) + need.get("metrics", []):
            if item in served:
                out.append(f"| `{item}` | ✅ served | {', '.join('`'+m+'`' for m in served[item])} |")
            else:
                out.append(f"| `{item}` | ❌ missing | _build it_ |")
    out += ["", "## Plan", ""] + steps
    out += ["", "## Definition of Done (consumer gate)", "", "| ID | Item | Status |", "|---|---|---|"]
    badge = {"pass": "✅", "na": "➖", "pending": "⬜"}
    for ci in checklist:
        out.append(f"| {ci['id']} | {ci['item']} | {badge.get(ci['status'],'⬜')} {ci['status']} |")
    return "\n".join(out) + "\n"

# --------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--inventory", required=True, help="YAML: marts: {name: [columns]}")
    ap.add_argument("--repo"); ap.add_argument("--print", action="store_true", dest="to_stdout")
    args = ap.parse_args()
    spec = load(args.spec); inventory = load(args.inventory)
    if "consumer" not in spec or "needs" not in spec:
        sys.exit("spec needs 'consumer' and 'needs'")
    served, missing, fidx = gap(spec, inventory)
    steps, surface = build_plan(spec, served, missing, fidx)
    checklist = build_checklist(spec, missing)
    md = render_md(spec, served, missing, steps, checklist)
    gapdoc = {"consumer": spec["consumer"]["name"], "served": served,
              "missing": missing, "surface": surface,
              "checklist": checklist, "generated": str(datetime.date.today())}

    name = slug(spec["consumer"]["name"])
    if args.to_stdout or not args.repo:
        sys.stdout.write(md)
        print("\n---- gap.json ----\n" + json.dumps(gapdoc, indent=1)); return
    d = os.path.join(args.repo, "consumption", "consumers", name); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "onboarding_plan.md"), "w", encoding="utf-8").write(md)
    open(os.path.join(d, "gap.json"), "w", encoding="utf-8").write(json.dumps(gapdoc, indent=1))
    print(f"wrote consumption/consumers/{name}/onboarding_plan.md + gap.json "
          f"(served {len(served)}, missing {len(missing)})")

if __name__ == "__main__":
    main()
