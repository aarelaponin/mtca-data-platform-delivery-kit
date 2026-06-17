#!/usr/bin/env python3
"""
principles.py — the MTCA architectural principles register, and ADRs that cite it.

Weighty decisions (X-or-Y, build-or-buy, now-or-later) are settled by CITATION to a numbered,
priority-ordered register — not re-argued each time. This tool lists the register and turns a
decision into an Architecture Decision Record that cites the relevant principle(s), validating that
every cited principle exists (so an ADR can't lean on a principle that isn't in the register).

  --list                                  print the register (id · title · statement)
  --new-adr --spec decision.yml [--number 0007] -o adr.md
                                          render a numbered ADR; fails if it cites an unknown principle
  --check --spec decision.yml             ensure a decision cites at least one valid principle (gate)

The register is data: references/principles-register.yaml — edit it (with the DGC) to evolve the
principles; this tool reads it.

Pure standard library (PyYAML if present, else JSON).
"""
import argparse, json, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTER = os.path.normpath(os.path.join(HERE, "..", "references", "principles-register.yaml"))

def load(path):
    txt = open(path, encoding="utf-8").read()
    try:
        import yaml; return yaml.safe_load(txt)
    except Exception:
        try: return json.loads(txt)
        except Exception: sys.exit(f"Could not parse {path} (install pyyaml or use JSON).")

def register():
    reg = load(REGISTER)
    return {p["id"]: p for p in reg["principles"]}, reg.get("version", "?")

def cmd_list():
    reg, ver = register()
    print(f"MTCA Architectural Principles Register v{ver} — {len(reg)} principles\n")
    for pid, p in reg.items():
        print(f"{pid}. {p['title']}\n    {p['statement'].strip()}\n")

def validate_cites(spec, reg):
    cited = [c.strip() for c in (spec.get("principles") or [])]
    unknown = [c for c in cited if c not in reg]
    return cited, unknown

def cmd_new_adr(spec_path, number, out):
    reg, _ = register()
    spec = load(spec_path)
    cited, unknown = validate_cites(spec, reg)
    if unknown:
        sys.exit(f"ADR cites unknown principle(s): {', '.join(unknown)} "
                 f"(known: {', '.join(reg)})")
    if not cited:
        sys.exit("ADR must cite at least one principle (add a 'principles:' list).")
    num = number or "XXXX"
    lines = [f"# ADR-{num}: {spec['title']}",
             f"\n_Status: {spec.get('status','Proposed')} · {datetime.date.today()}_\n",
             "## Context", spec.get("context", "TODO").strip(), "",
             "## Options considered"]
    for o in spec.get("options", []):
        if isinstance(o, dict):
            lines.append(f"- **{o.get('name','?')}** — {o.get('note','')}")
        else:
            lines.append(f"- {o}")
    lines += ["", "## Decision", spec.get("decision", "TODO").strip(), "",
              "## Principles cited"]
    for c in cited:
        p = reg[c]
        lines.append(f"- **{c} {p['title']}** — {p['statement'].strip()}")
    lines += ["", "## Consequences", spec.get("consequences", "TODO").strip(), ""]
    doc = "\n".join(lines) + "\n"
    if out:
        open(out, "w", encoding="utf-8").write(doc); print("wrote", out)
    else:
        sys.stdout.write(doc)

def cmd_check(spec_path):
    reg, _ = register()
    spec = load(spec_path)
    cited, unknown = validate_cites(spec, reg)
    if unknown:
        print("FAIL — unknown principle(s):", ", ".join(unknown)); sys.exit(1)
    if not cited:
        print("FAIL — decision cites no principle (decisions must be made by citation)."); sys.exit(1)
    print("OK — cites", ", ".join(cited)); sys.exit(0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--new-adr", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--spec"); ap.add_argument("--number"); ap.add_argument("-o", "--out")
    args = ap.parse_args()
    if args.list: cmd_list()
    elif args.new_adr:
        if not args.spec: sys.exit("--new-adr needs --spec")
        cmd_new_adr(args.spec, args.number, args.out)
    elif args.check:
        if not args.spec: sys.exit("--check needs --spec")
        cmd_check(args.spec)
    else:
        ap.error("choose --list | --new-adr | --check")

if __name__ == "__main__":
    main()
