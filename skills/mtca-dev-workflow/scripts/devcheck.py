#!/usr/bin/env python3
"""
devcheck.py — workstation toolchain doctor for the MTCA Data Platform (Windows + macOS/Linux).

Before building anything, confirm the local toolchain is present. This probes the tools the platform
work needs and prints a clear present/missing report, so a team member on a fresh Windows or Mac
workstation knows exactly what to install — rather than discovering it mid-task.

It only runs version probes (no network, no system changes). Exit code is non-zero if any REQUIRED
tool is missing, so it can gate a setup step.

  python devcheck.py            # full report
  python devcheck.py --json     # machine-readable

Pure standard library; works the same on PowerShell and bash.
"""
import argparse, json, shutil, subprocess, sys, platform

# (command, version-args, required?, what-for)
TOOLS = [
    ("python3", ["--version"], False, "Python 3 (skills + dbt). On Windows it's usually 'python'."),
    ("python",  ["--version"], False, "Python 3 (Windows spelling)."),
    ("git",     ["--version"], True,  "version control — runs on the workstation, not the sandbox."),
    ("uv",      ["--version"], False, "fast Python env/dep manager (recommended; via 'pip install uv')."),
    ("dbt",     ["--version"], True,  "dbt — build/test the medallion."),
    ("pre-commit", ["--version"], False, "commit hygiene hooks."),
    ("docker",  ["--version"], False, "containers (OS-agnostic local services)."),
    ("clickhouse-client", ["--version"], False, "ClickHouse CLI (only if you query CH locally)."),
]

def probe(cmd, args):
    path = shutil.which(cmd)
    if not path:
        return None, None
    try:
        out = subprocess.run([cmd] + args, capture_output=True, text=True, timeout=15)
        ver = (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else ""
        return path, ver
    except Exception as e:
        return path, f"(found, but version probe failed: {e})"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = []
    py_ok = False
    for cmd, vargs, required, what in TOOLS:
        path, ver = probe(cmd, vargs)
        present = path is not None
        if cmd in ("python3", "python") and present:
            py_ok = True
        results.append({"tool": cmd, "present": present, "version": ver or "",
                        "required": required, "what_for": what, "path": path or ""})

    # python is required, but either spelling satisfies it
    missing_required = [r for r in results
                        if r["required"] and not r["present"]]
    if not py_ok:
        missing_required.append({"tool": "python3|python", "what_for": "Python 3 runtime"})

    if args.json:
        print(json.dumps({"os": platform.system(), "results": results,
                          "missing_required": [m["tool"] for m in missing_required]}, indent=2))
        sys.exit(0 if not missing_required else 1)

    print(f"MTCA workstation toolchain — {platform.system()} {platform.release()}\n")
    for r in results:
        mark = "OK  " if r["present"] else ("MISS" if r["required"] else "opt ")
        ver = f" — {r['version']}" if r["version"] else ""
        print(f"  [{mark}] {r['tool']:<18}{ver}")
        if not r["present"]:
            print(f"          ({'required' if r['required'] else 'optional'}) {r['what_for']}")
    print()
    py_note = "" if py_ok else "  - Python 3 (install from python.org / brew / your package manager)\n"
    if missing_required or not py_ok:
        print("MISSING REQUIRED:")
        sys.stdout.write(py_note)
        for m in missing_required:
            if m.get("tool") != "python3|python":
                print(f"  - {m['tool']}: {m['what_for']}")
        print("\nInstall the missing required tools, then re-run.  (`python tasks.py setup` installs the dbt/pre-commit stack.)")
        sys.exit(1)
    print("All required tools present. You're ready to build.")
    sys.exit(0)

if __name__ == "__main__":
    main()
