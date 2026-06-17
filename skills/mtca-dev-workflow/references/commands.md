# Command blocks — per activity, Windows + macOS

Prefer the OS-agnostic entry points (`python tasks.py …`, `docker compose`, `uv`) so one block works
everywhere. Where the shell matters, both are given. On Windows, Python is usually `python` / `py -3`;
on macOS/Linux it's `python3`.

## Workstation setup
```bash
# macOS / Linux
python3 skills/mtca-dev-workflow/scripts/devcheck.py
python tasks.py setup        # venv + dbt + pre-commit (from repo-scaffold)
```
```powershell
# Windows (PowerShell)
py -3 skills\mtca-dev-workflow\scripts\devcheck.py
python tasks.py setup
```

## Generate (Track A — same on every OS)
```bash
python3 skills/onboard-source/scripts/gen_bronze_ddl.py --schema schema_ird.json --out ingestion/ird/
python3 skills/build-dbt-model/scripts/gen_dbt_model.py --spec model.yml --out dbt/models
python3 skills/add-dq-checks/scripts/gen_dq_checks.py --spec dq.yml --repo .
```
(Windows: same commands with `py -3` and `\` paths.)

## Build & test the medallion (Track B — on the workstation/stack)
```bash
# macOS / Linux
python tasks.py dbt-build
python tasks.py dbt-test
```
```powershell
# Windows
python tasks.py dbt-build
python tasks.py dbt-test
```
`tasks.py` wraps `cd dbt && dbt build|test`, so it's identical on both shells.

## Load a source (Track B)
```bash
# macOS / Linux — password via env var, never on the command line
SRC_DB_PASSWORD=... python3 skills/onboard-source/scripts/profile_source.py --dialect informix \
  --host <host> --db <db> --user <user> --emit-schema schema_<src>.json --out profile_<src>.md
# then run the gated extractor / ingestion service per onboard-source
```
```powershell
# Windows (PowerShell) — set the env var for the session
$env:SRC_DB_PASSWORD = "..."
py -3 skills\onboard-source\scripts\profile_source.py --dialect informix `
  --host <host> --db <db> --user <user> --emit-schema schema_<src>.json --out profile_<src>.md
```

## Verify catalogue semantics (gate is Track A; data-arithmetic is Track B)
```bash
python3 skills/verify-catalogue-semantics/scripts/verify_semantics.py --gate <Module>_OpenMetadata.verified.yaml
# data arithmetic needs real rows (Track B):
python3 skills/verify-catalogue-semantics/scripts/verify_semantics.py --check-identity --data rows.csv --identity "box18 = box13 + box15"
```

## Readiness gate
```bash
python3 skills/production-readiness-check/scripts/prodcheck.py --check --manifest readiness.yml --report readiness_report.md
```

## Commit (Track B — git on the workstation, not the sandbox)
```bash
# macOS / Linux
git add -A && git commit -m "<area>: <summary>" && git push
```
```powershell
# Windows
git add -A; git commit -m "<area>: <summary>"; git push
```
If a sandbox git ever stranded locks, clean them on the workstation:
`rm -f .git/index.lock .git/HEAD.lock` (macOS) / `Remove-Item .git\index.lock,.git\HEAD.lock -ErrorAction SilentlyContinue` (Windows).
See `repo-scaffold/references/git-on-the-workstation.md`.

## Local services (optional, OS-agnostic)
```bash
docker compose up -d        # e.g. a local ClickHouse for Track-A dbt runs
```
Same command on Windows (Docker Desktop) and macOS — containers are the cross-OS leveller (P14).
