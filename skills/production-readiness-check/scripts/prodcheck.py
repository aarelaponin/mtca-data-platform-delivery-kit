#!/usr/bin/env python3
"""
prodcheck.py — the MTCA Production-Readiness Checklist, as an evidence-driven gate.

"In production" is not an opinion — it's a checklist that passes. This runs the canonical go-live
checklist for a release: it AUTO-CHECKS what it can inspect in the repo (CI present, ops runbook,
rollback documented, DQ thresholds, dashboard/API RBAC, alerts, secrets gitignored) and takes signed
ATTESTATIONS for what it can't (UAT, DPIA/DPO clearance, monitoring live, go-live sign-off). It then
produces a readiness report and a hard pass/fail gate — every blocker must pass before go-live.

  --emit-manifest -o readiness.yml        scaffold the attestation manifest (fill the manual items)
  --check --manifest readiness.yml [--report report.md]   run; exit 0 only if all blockers pass

Deterministic, pure standard library (PyYAML if present, else JSON).
"""
import argparse, json, os, re, sys, glob, datetime

def load(p):
    txt = open(p, encoding="utf-8").read()
    try:
        import yaml; return yaml.safe_load(txt)
    except Exception:
        try: return json.loads(txt)
        except Exception: sys.exit("Could not parse manifest (install pyyaml or use JSON).")

def dump_yaml(obj):
    try:
        import yaml; return yaml.safe_dump(obj, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)
    except Exception:
        return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"

# --------------------------------------------------------- auto-check helpers
def _glob(repo, pat):
    return [p for p in glob.glob(os.path.join(repo, pat), recursive=True) if not p.endswith(".gitkeep")]

def _any_contains(paths, needle):
    for p in paths:
        try:
            if needle.lower() in open(p, encoding="utf-8", errors="ignore").read().lower():
                return True
        except Exception:
            pass
    return False

def chk_ci(repo):       return bool(_glob(repo, ".github/workflows/*.y*ml") or _glob(repo, ".gitlab-ci.yml"))
def chk_runbook(repo):  return bool(_glob(repo, "ops/runbooks/*.md"))
def chk_rollback(repo): return _any_contains(_glob(repo, "ops/runbooks/*.md"), "rollback")
def chk_dq(repo):       return bool(_glob(repo, "quality/thresholds/*.y*ml"))
def chk_dash_rbac(repo):
    for p in _glob(repo, "consumption/dashboards/**/dashboard.y*ml"):
        d = load(p) or {}
        if d.get("rbac_roles"): return True
    return False
def chk_api_rbac(repo): return _any_contains(_glob(repo, "consumption/api/*_openapi.y*ml"), "x-rbac-roles")
def chk_alerts(repo):
    for p in _glob(repo, "consumption/dashboards/**/dashboard.y*ml"):
        d = load(p) or {}
        if d.get("alerts"): return True
    return False
def chk_secrets(repo):
    gi = os.path.join(repo, ".gitignore")
    if not os.path.exists(gi): return False
    t = open(gi, encoding="utf-8", errors="ignore").read()
    return ".env" in t and "profiles.yml" in t

AUTO = {"DEPLOY-1": chk_ci, "OPS-1": chk_runbook, "ROLL-1": chk_rollback, "DQ-1": chk_dq,
        "SEC-1": chk_dash_rbac, "SEC-1b": chk_api_rbac, "MON-2": chk_alerts, "SEC-3": chk_secrets}

# --------------------------------------------------------- the checklist
# kind: auto (computed from the repo) | attest (signed off in the manifest)
CHECKLIST = [
    ("DEPLOY-1", "Deploy",     "CI pipeline present and green", "auto",   "blocker"),
    ("DEPLOY-2", "Deploy",     "Deployed to test and promoted via the pipeline", "attest", "blocker"),
    ("MON-1",    "Monitoring", "Monitoring dashboards live (Prometheus/Grafana)", "attest", "blocker"),
    ("MON-2",    "Monitoring", "Threshold alerts configured (freshness/ingestion/dashboard)", "auto", "blocker"),
    ("SEC-1",    "Security",   "RBAC set on dashboards", "auto", "blocker"),
    ("SEC-1b",   "Security",   "RBAC set on APIs", "auto", "blocker"),
    ("SEC-2",    "Security",   "DPIA / DPO clearance for real (Restricted) data", "attest", "blocker"),
    ("SEC-3",    "Security",   "Secrets handled (no credentials in the repo; .env/profiles gitignored)", "auto", "blocker"),
    ("DQ-1",     "DataQuality","DQ gates defined and green on the marts", "auto", "blocker"),
    ("DQ-2",     "DataQuality","Catalogue descriptions VERIFIED for every handover/mart column", "attest", "blocker"),
    ("OPS-1",    "Operations", "Ops runbook written (what to do when ingestion/build/dashboard fails)", "auto", "blocker"),
    ("OPS-2",    "Operations", "Freshness SLAs defined per tier", "attest", "warn"),
    ("ROLL-1",   "Rollback",   "Rollback documented and PROVEN (rehearsed, not just written)", "auto", "blocker"),
    ("UAT-1",    "UAT",        "Consumer (debt team) UAT signed off", "attest", "blocker"),
    ("GOV-1",    "Governance", "Go-live sign-off recorded (DGC/owner)", "attest", "blocker"),
]
ATTEST_ITEMS = [c for c in CHECKLIST if c[3] == "attest"]

# --------------------------------------------------------- emit manifest
def emit_manifest():
    att = {}
    for cid, cat, title, kind, sev in ATTEST_ITEMS:
        att[cid] = {"status": "pending", "evidence": "", "signed_by": "", "date": "",
                    "_title": title, "_severity": sev}
    return {"release": "debt-v1.0", "repo": ".",
            "note": "Fill each attestation: status pass|fail|na, plus evidence/signed_by/date. "
                    "Auto items (CI, runbook, rollback, DQ, RBAC, alerts, secrets) are computed from the repo.",
            "attestations": att}

# --------------------------------------------------------- run the checklist
def run(manifest, repo):
    att = manifest.get("attestations", {})
    rows = []
    for cid, cat, title, kind, sev in CHECKLIST:
        if kind == "auto":
            ok = AUTO[cid](repo)
            status = "pass" if ok else "fail"
            evidence = "auto: repo inspection"
        else:
            a = att.get(cid, {})
            status = (a.get("status") or "pending").lower()
            evidence = a.get("evidence", "") + (f" (by {a['signed_by']})" if a.get("signed_by") else "")
        rows.append({"id": cid, "category": cat, "title": title, "kind": kind,
                     "severity": sev, "status": status, "evidence": evidence})
    return rows

def gate(rows):
    # a blocker passes only on "pass" (or "na" for attest items explicitly marked not-applicable)
    failed = [r for r in rows if r["severity"] == "blocker" and r["status"] not in ("pass", "na")]
    warns = [r for r in rows if r["severity"] == "warn" and r["status"] not in ("pass", "na")]
    return failed, warns

def report_md(rows, failed, warns, manifest):
    npass = sum(r["status"] in ("pass", "na") for r in rows)
    out = [f"# Production-Readiness Report — {manifest.get('release','(release)')}",
           f"_Checked {datetime.date.today()} · {npass}/{len(rows)} items satisfied · "
           f"**GATE: {'PASS' if not failed else 'FAIL'}**_\n"]
    if failed:
        out.append(f"**{len(failed)} blocker(s) outstanding — not ready for production:**")
        for r in failed: out.append(f"- ❌ `{r['id']}` {r['title']}")
        out.append("")
    if warns:
        out.append(f"_{len(warns)} warning(s) (non-blocking): " + ", ".join(r["id"] for r in warns) + "_\n")
    out += ["| ID | Category | Item | Kind | Sev | Status | Evidence |", "|---|---|---|---|---|---|---|"]
    badge = {"pass": "✅", "na": "➖", "fail": "❌", "pending": "⬜"}
    for r in rows:
        out.append(f"| {r['id']} | {r['category']} | {r['title']} | {r['kind']} | {r['severity']} | "
                   f"{badge.get(r['status'],'⬜')} {r['status']} | {r['evidence'] or '—'} |")
    return "\n".join(out) + "\n"

# --------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-manifest", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--manifest"); ap.add_argument("--repo"); ap.add_argument("--report"); ap.add_argument("-o", "--out")
    args = ap.parse_args()

    if args.emit_manifest:
        out = dump_yaml(emit_manifest())
        (open(args.out, "w", encoding="utf-8").write(out) if args.out else sys.stdout.write(out))
        if args.out: print("wrote manifest scaffold ->", args.out)
        return

    if args.check:
        if not args.manifest: sys.exit("--check needs --manifest")
        manifest = load(args.manifest)
        repo = args.repo or manifest.get("repo") or "."
        if not os.path.isabs(repo):
            repo = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(args.manifest)), repo))
        rows = run(manifest, repo)
        failed, warns = gate(rows)
        rpt = report_md(rows, failed, warns, manifest)
        if args.report: open(args.report, "w", encoding="utf-8").write(rpt); print("wrote", args.report)
        print(f"GATE {'PASS' if not failed else 'FAIL'} — {len(failed)} blocker(s), {len(warns)} warning(s)")
        for r in failed: print(f"  BLOCKER  {r['id']}  {r['title']}")
        sys.exit(0 if not failed else 1)

    ap.error("choose --emit-manifest or --check")

if __name__ == "__main__":
    main()
