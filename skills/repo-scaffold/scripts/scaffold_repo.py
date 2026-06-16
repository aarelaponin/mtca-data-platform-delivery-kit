#!/usr/bin/env python3
"""
scaffold_repo.py — lay out the MTCA Data Platform mono-repo with conventions baked in.

Creates the canonical directory tree and seed files (dbt five-layer medallion, ingestion,
catalogue, quality, consumption, security, ops, docs) plus the cross-OS hygiene files
(.gitignore, .pre-commit-config.yaml, .editorconfig, a Python task runner + Makefile).

It does NOT run git. Per the platform's version-control principle, git runs on the
workstation (Desktop Commander / terminal) — this script only writes files; SKILL.md drives
the commit. Idempotent: existing files are left alone unless --force.

Cross-platform, pure standard library.

Usage:
  python scaffold_repo.py --path <target-dir> [--name mtca-data-platform] [--force]
"""
import argparse, os, sys

# ----------------------------------------------------------------------------- dirs
DIRS = [
    "docs/principles", "docs/templates", "docs/checklists", "docs/adr",
    "ingestion/sources",
    "dbt/models/staging", "dbt/models/intermediate", "dbt/models/marts", "dbt/models/_sources",
    "dbt/macros", "dbt/tests",
    "catalogue/module-semantics",
    "quality/thresholds",
    "consumption/dashboards", "consumption/api",
    "security",
    "ops/runbooks",
    ".github",
]

# ----------------------------------------------------------------------------- seed files
def files(name):
    return {
".gitignore": """\
# Python
__pycache__/
*.pyc
.venv/
venv/
.uv/

# dbt
dbt/target/
dbt/dbt_packages/
dbt/logs/

# secrets & env — example files are tracked, real ones never are
.env
*.env
dbt/profiles.yml
!dbt/profiles.example.yml

# OS / editor
.DS_Store
Thumbs.db
*~
.idea/
.vscode/*
!.vscode/extensions.json
""",

".editorconfig": """\
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[*.md]
trim_trailing_whitespace = false
""",

".pre-commit-config.yaml": """\
# Runs on every commit so generated artefacts and hand edits stay clean and consistent.
# Install once per clone:  pre-commit install   (see SKILL.md / git-on-the-workstation.md)
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ["--maxkb=5000"]
      - id: check-merge-conflict
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 3.1.0
    hooks:
      - id: sqlfluff-lint
        files: ^dbt/models/.*\\.sql$
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.4
    hooks:
      - id: ruff
""",

"README.md": f"""\
# {name}

The MTCA Data Platform mono-repo. Everything-as-code: ingestion config, dbt models, catalogue
semantics, quality rules, consumption surfaces, security and ops all live here, reviewed via
pull request.

## Layout
- `docs/` — principles, templates, checklists, ADRs (the *why* and the *what-to-produce*).
- `ingestion/` — ingestion-service source configs (tiers, watermarks, reconciliation).
- `dbt/` — the **five-layer medallion**: Bronze → `staging/` (`stg_`) → `intermediate/` (`int_`)
  → `marts/` (`mart_<domain>__<desc>`) → Published.
- `catalogue/` — OpenMetadata semantic YAMLs (`module-semantics/`).
- `quality/` — Data Quality Framework thresholds & test specs.
- `consumption/` — Superset dashboards & API contracts (the consumer surfaces).
- `security/` — RBAC matrices, classification register.
- `ops/` — runbooks, monitoring config.

See `docs/CONVENTIONS.md` for naming and the "where does this file go?" map.

## Quick start
```
python tasks.py setup       # create venv, install deps + pre-commit
python tasks.py dbt-build    # dbt build (staging -> intermediate -> marts)
python tasks.py dbt-test     # dbt test
python tasks.py lint         # pre-commit on all files
```
On Unix you can use `make setup` / `make dbt-build` instead — same targets.

## Version control
Git runs on your workstation (Windows or macOS), same workflow on both. See
`docs/git-on-the-workstation.md` for the branch → commit → PR cheat-sheet and the Cowork note.
""",

"docs/CONVENTIONS.md": """\
# Conventions — where things go, and what to name them

## Naming
- dbt staging:      `stg_<source>__<entity>`        (one model per source table; types/cleaning only, NO joins)
- dbt intermediate: `int_<domain>__<concept>`       (ALL cross-source joins + golden records live here)
- dbt marts:        `mart_<domain>__<description>`   (compose from `int_`, never re-join raw sources)
- catalogue YAML:   `<Module>_OpenMetadata.yaml`     (in `catalogue/module-semantics/`)
- ingestion source: `ingestion/sources/<source>.yml`

## The five-layer medallion (the rule, set once)
Bronze (raw, as-ingested) → Silver `stg_` (1:1 clean) → **Intermediate `int_`** (joins +
golden records, e.g. Taxpayer-360) → Gold `mart_` (consumer-facing) → Published. Marts compose
from `int_`; they do not re-join raw sources. Join contracts are enforced by dbt tests.

## Generated artefacts are never hand-edited
If a model/config was generated by a skill, fix the spec or the generator and regenerate —
do not patch the output. Hand edits are silently lost on the next regeneration.

## Everything-as-code, PR-reviewed
No definition lives only in someone's chat or drive. It lands in this repo and is reviewed.
""",

"dbt/dbt_project.yml": """\
name: 'mtca_platform'
version: '1.0.0'
config-version: 2
profile: 'mtca_platform'

model-paths: ["models"]
macro-paths: ["macros"]
test-paths: ["tests"]
target-path: "target"
clean-targets: ["target", "dbt_packages"]

models:
  mtca_platform:
    staging:
      +materialized: view
      +schema: silver
    intermediate:
      +materialized: table
      +schema: intermediate
    marts:
      +materialized: table
      +schema: gold
""",

"dbt/profiles.example.yml": """\
# Copy to dbt/profiles.yml (gitignored) and fill in real credentials, or point DBT_PROFILES_DIR here.
mtca_platform:
  target: dev
  outputs:
    dev:
      type: clickhouse
      host: "{{ env_var('CLICKHOUSE_HOST', 'localhost') }}"
      port: 9000
      user: "{{ env_var('CLICKHOUSE_USER', 'default') }}"
      password: "{{ env_var('CLICKHOUSE_PASSWORD', '') }}"
      schema: dev
      secure: false
""",

"dbt/models/_sources/sources.example.yml": """\
# Declare each ingested source so staging models can ref() it and lineage is captured.
version: 2
sources:
  - name: bronze
    schema: bronze
    description: "Raw, as-ingested layer (Informix -> ClickHouse)."
    tables:
      - name: example_source_table
        description: "TODO: describe; one staging model (stg_) per source table."
""",

"dbt/models/staging/.gitkeep": "",
"dbt/models/intermediate/.gitkeep": "",
"dbt/models/marts/.gitkeep": "",
"dbt/macros/.gitkeep": "",
"dbt/tests/.gitkeep": "",
"ingestion/sources/.gitkeep": "",
"catalogue/module-semantics/.gitkeep": "",
"quality/thresholds/.gitkeep": "",
"consumption/dashboards/.gitkeep": "",
"consumption/api/.gitkeep": "",
"security/.gitkeep": "",
"ops/runbooks/.gitkeep": "",
"docs/principles/.gitkeep": "",
"docs/templates/.gitkeep": "",
"docs/checklists/.gitkeep": "",
"docs/adr/.gitkeep": "",

".github/pull_request_template.md": """\
## What & why
<!-- one or two sentences -->

## Definition of Done
- [ ] Tests pass (`dbt test` / pre-commit) and CI is green
- [ ] Generated artefacts regenerated (not hand-edited)
- [ ] Catalogue descriptions updated and VERIFIED where they drive a mart/handover
- [ ] Data-Owner / reviewer sign-off where required
""",

"Makefile": """\
# Unix convenience wrapper around tasks.py (Windows users: run `python tasks.py <target>`).
.PHONY: setup dbt-build dbt-test lint
setup:      ; python3 tasks.py setup
dbt-build:  ; python3 tasks.py dbt-build
dbt-test:   ; python3 tasks.py dbt-test
lint:       ; python3 tasks.py lint
""",

"tasks.py": """\
#!/usr/bin/env python3
\"\"\"OS-agnostic task runner (works identically on Windows and macOS/Linux).
Usage: python tasks.py <setup|dbt-build|dbt-test|lint>\"\"\"
import subprocess, sys

def sh(cmd): print("+", cmd); raise SystemExit(subprocess.call(cmd, shell=True))

TASKS = {
    "setup":     "python -m pip install -U uv && uv venv && uv pip install dbt-clickhouse pre-commit sqlfluff ruff && pre-commit install",
    "dbt-build": "cd dbt && dbt build",
    "dbt-test":  "cd dbt && dbt test",
    "lint":      "pre-commit run --all-files",
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in TASKS:
        print("tasks:", ", ".join(TASKS)); raise SystemExit(2)
    sh(TASKS[sys.argv[1]])
""",
}

# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="target directory for the repo")
    ap.add_argument("--name", default="mtca-data-platform", help="repo name (README title)")
    ap.add_argument("--force", action="store_true", help="overwrite existing seed files")
    args = ap.parse_args()

    root = os.path.abspath(args.path)
    os.makedirs(root, exist_ok=True)
    for d in DIRS:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    created, skipped = [], []
    for rel, content in files(args.name).items():
        dest = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest) and not args.force:
            skipped.append(rel); continue
        with open(dest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        created.append(rel)

    print(f"Scaffolded '{args.name}' at {root}")
    print(f"  dirs ensured : {len(DIRS)}")
    print(f"  files created: {len(created)}")
    if skipped:
        print(f"  files skipped (exist; use --force): {len(skipped)}")
    print("\nNEXT: initialise git ON THE WORKSTATION and make the first commit.")
    print("  see SKILL.md step 3 / references/git-on-the-workstation.md (cross-OS).")

if __name__ == "__main__":
    main()
