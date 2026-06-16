#!/usr/bin/env python3
"""
verify_semantics.py — drive a catalogue semantic enrichment from DRAFT to VERIFIED.

The catalogue gate (DQF §S5, the R401-M lesson): a description is DRAFT until VERIFIED against an
authoritative source (the official form/spec, the application code, or data arithmetic that
reconciles on real rows) or explicitly marked TO-CONFIRM. Only VERIFIED descriptions may drive a
mart or the DcP3 handover. A wrong description becomes a wrong number.

This tool operationalises that gate over a semantic YAML (the shape produced by the
`legacy-module-to-openmetadata` skill: an `application` + `tables[]` each with `columns[]`):

  --emit-ledger SEM.yaml -o ledger.yml
        scaffold a verification ledger listing every table & column as `draft`, for the reviewer
        to fill (status / evidence / verified_by / date).

  --apply SEM.yaml --ledger ledger.yml -o verified.yaml --log verify_log.md
        merge the ledger onto the enrichment (writes per-entity status + verification block),
        emit the verified YAML + a verification log, and print coverage.

  --gate verified.yaml [--allow-to-confirm]
        exit non-zero if anything destined for handover is not VERIFIED (the gate).

  --check-identity --data rows.csv --identity "box18 = box13 + box15 + box16 + box17" [--tol 0.01]
        data arithmetic: report the fraction of rows on which a stated identity holds (the
        strongest verification — a map that survives this is VERIFIED).

Pure standard library (uses PyYAML — install with `pip install pyyaml` if missing).
"""
import argparse, csv, json, os, re, sys, datetime

def need_yaml():
    try:
        import yaml; return yaml
    except Exception:
        sys.exit("This mode needs PyYAML: pip install pyyaml")

def load(path):
    yaml = need_yaml()
    return yaml.safe_load(open(path, encoding="utf-8"))

def dump(obj):
    yaml = need_yaml()
    return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)

STATUSES = ("verified", "to_confirm", "draft")

# --------------------------------------------------------------- iterate entities
def entities(sem):
    """Yield (ref, kind, node) for every table and column in the enrichment."""
    for t in sem.get("tables", []):
        yield t["name"], "table", t
        cols = t.get("columns")
        if isinstance(cols, list):
            for c in cols:
                yield f"{t['name']}.{c['name']}", "column", c

# --------------------------------------------------------------- emit ledger
def emit_ledger(sem, src_name):
    items = []
    for ref, kind, node in entities(sem):
        items.append({"ref": ref, "kind": kind,
                      "status": "draft",          # reviewer changes to verified | to_confirm
                      "evidence": "",             # e.g. "official BOP form field 'VAT No'" / "data arithmetic: 18=13+15+16+17 holds 99.9%"
                      "verified_by": "", "date": ""})
    return {"source_yaml": src_name,
            "instructions": "Set status to verified|to_confirm and fill evidence/verified_by/date. "
                            "VERIFIED requires an authoritative source (form/spec/app code) or data arithmetic.",
            "items": items}

# --------------------------------------------------------------- apply ledger
def apply_ledger(sem, ledger):
    index = {it["ref"]: it for it in ledger.get("items", [])}
    rows, counts = [], {"table": [0, 0], "column": [0, 0]}   # [verified, total]
    for ref, kind, node in entities(sem):
        it = index.get(ref, {})
        status = (it.get("status") or "draft").lower()
        if status not in STATUSES:
            status = "draft"
        node["status"] = status
        if it.get("evidence") or status != "draft":
            node["verification"] = {k: it.get(k, "") for k in ("evidence", "verified_by", "date")}
        counts[kind][1] += 1
        counts[kind][0] += (status == "verified")
        rows.append((ref, kind, status, it.get("evidence", "")))
    # stamp the gate state at the top
    total = counts["table"][1] + counts["column"][1]
    ver = counts["table"][0] + counts["column"][0]
    sem.setdefault("_meta", {})
    sem["_meta"]["verification"] = {
        "verified": ver, "total": total,
        "coverage_pct": round(100 * ver / total, 1) if total else 0.0,
        "gate": "PASS" if ver == total else "OPEN",
        "checked": str(datetime.date.today()),
    }
    return rows, counts

def write_log(rows, counts, src):
    ver = counts["table"][0] + counts["column"][0]
    tot = counts["table"][1] + counts["column"][1]
    out = [f"# Verification log — {src}",
           f"_Checked {datetime.date.today()} · {ver}/{tot} entities VERIFIED "
           f"({round(100*ver/tot,1) if tot else 0}%)._\n",
           f"Tables: {counts['table'][0]}/{counts['table'][1]} · "
           f"Columns: {counts['column'][0]}/{counts['column'][1]}\n",
           "| Entity | Kind | Status | Evidence |", "|---|---|---|---|"]
    for ref, kind, status, ev in rows:
        badge = {"verified": "✅", "to_confirm": "🟡", "draft": "⬜"}.get(status, "⬜")
        out.append(f"| `{ref}` | {kind} | {badge} {status} | {ev or '—'} |")
    unver = [r for r in rows if r[2] != "verified"]
    if unver:
        out.append(f"\n**{len(unver)} not yet VERIFIED** — these may not drive a mart or the DcP3 handover.")
    return "\n".join(out) + "\n"

# --------------------------------------------------------------- gate
def gate(sem, allow_to_confirm=False):
    ok = {"verified"} | ({"to_confirm"} if allow_to_confirm else set())
    bad = [(ref, node.get("status", "draft")) for ref, kind, node in entities(sem)
           if node.get("status", "draft") not in ok]
    return bad

# --------------------------------------------------------------- data arithmetic
SAFE = re.compile(r'^[A-Za-z0-9_+\-*/(). ]+$')

def check_identity(data_path, identity, tol):
    if "=" not in identity:
        sys.exit("identity must be 'LHS = RHS', e.g. \"box18 = box13 + box15\"")
    lhs, rhs = [s.strip() for s in identity.split("=", 1)]
    for side in (lhs, rhs):
        if not SAFE.match(side):
            sys.exit(f"unsafe/invalid expression: {side!r}")
    n = held = skipped = 0
    with open(data_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                env = {k: float(v) for k, v in row.items() if v not in (None, "")}
                l = eval(lhs, {"__builtins__": {}}, env)   # noqa: S307 — guarded by SAFE regex
                r = eval(rhs, {"__builtins__": {}}, env)
            except Exception:
                skipped += 1; continue
            n += 1; held += (abs(l - r) <= tol)
    pct = round(100 * held / n, 2) if n else 0.0
    return n, held, skipped, pct

# --------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-ledger"); ap.add_argument("--apply"); ap.add_argument("--ledger")
    ap.add_argument("--gate"); ap.add_argument("--allow-to-confirm", action="store_true")
    ap.add_argument("--check-identity", action="store_true")
    ap.add_argument("--data"); ap.add_argument("--identity"); ap.add_argument("--tol", type=float, default=0.01)
    ap.add_argument("-o", "--out"); ap.add_argument("--log")
    args = ap.parse_args()

    if args.emit_ledger:
        sem = load(args.emit_ledger)
        led = emit_ledger(sem, os.path.basename(args.emit_ledger))
        (open(args.out, "w", encoding="utf-8").write(dump(led)) if args.out else sys.stdout.write(dump(led)))
        if args.out: print(f"wrote ledger with {len(led['items'])} entities -> {args.out}")
        return

    if args.apply:
        sem = load(args.apply); led = load(args.ledger) if args.ledger else {"items": []}
        rows, counts = apply_ledger(sem, led)
        if args.out: open(args.out, "w", encoding="utf-8").write(dump(sem)); print("wrote", args.out)
        if args.log: open(args.log, "w", encoding="utf-8").write(write_log(rows, counts, args.apply)); print("wrote", args.log)
        m = sem["_meta"]["verification"]
        print(f"coverage: {m['verified']}/{m['total']} verified ({m['coverage_pct']}%) — gate {m['gate']}")
        return

    if args.gate:
        sem = load(args.gate); bad = gate(sem, args.allow_to_confirm)
        if bad:
            print(f"GATE FAIL — {len(bad)} entity(ies) not VERIFIED:")
            for ref, st in bad[:50]: print(f"  {st:11s} {ref}")
            sys.exit(1)
        print("GATE PASS — all entities VERIFIED."); return

    if args.check_identity:
        if not (args.data and args.identity): sys.exit("--check-identity needs --data and --identity")
        n, held, skipped, pct = check_identity(args.data, args.identity, args.tol)
        verdict = "VERIFIED" if pct >= 99.0 else ("WEAK" if pct >= 90 else "FAILS")
        print(f"identity '{args.identity}': holds on {held}/{n} rows ({pct}%)"
              f"{f', {skipped} skipped' if skipped else ''} -> {verdict} (tol={args.tol})")
        sys.exit(0 if pct >= 99.0 else 2)

    ap.error("choose a mode: --emit-ledger | --apply | --gate | --check-identity")

if __name__ == "__main__":
    main()
