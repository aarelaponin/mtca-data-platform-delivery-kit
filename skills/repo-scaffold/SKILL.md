---
name: repo-scaffold
description: >-
  Lay out the MTCA Data Platform mono-repo with conventions baked in, AND own the shared,
  cross-OS, commit-on-the-workstation git mechanics that every other skill in the pack relies on.
  Use this WHENEVER the task is to start or organise the platform repository, or to do anything
  with git for the platform: "scaffold the repo", "set up the data platform project", "lay out
  the mono-repo", "initialise the repository", "where does this file go", "what's our naming
  convention", "create the dbt project structure", "set up pre-commit", "how do I branch / commit
  / open a PR here", "commit this to the repo". Trigger even when the user only says "set things
  up properly" or "get this under version control" — establishing the structured, version-controlled
  home is exactly this skill, and the other skills call into its git workflow rather than reinventing
  it. Cross-platform (Windows + macOS), pure Python, no install.
---

# Repo scaffold + the shared git workflow

## Why this exists

Two jobs in one skill, because they're the same foundation:

1. **Scaffold** the platform mono-repo so every later artefact has an obvious, conventional home —
   the five-layer dbt medallion, ingestion configs, catalogue semantics, quality rules, consumption
   surfaces, security and ops, plus the cross-OS hygiene files (`.gitignore`, pre-commit, a task
   runner). Structure the team doesn't have to invent is structure they can't get wrong.
2. **Own the git workflow** the whole skill pack shares. Every other skill ends by committing its
   output; rather than each one re-explaining branch/commit/PR (and the Cowork "git runs on the
   workstation" wrinkle), they point here. This is the canonical reference.

## A — Scaffold the repo

### 1 — Run the scaffolder

```bash
# macOS / Linux
python3 scripts/scaffold_repo.py --path "/path/to/mtca-data-platform"
```
```powershell
# Windows (PowerShell)
py -3 scripts\scaffold_repo.py --path "C:\path\to\mtca-data-platform"
```

It creates the directory tree and seed files (idempotent — existing files are left alone unless
`--force`). It deliberately does **not** run git; per the platform principle, git runs on the
workstation (step 3). Pure standard library — nothing to install.

### 2 — Review the layout

The canonical tree (see `references/repo-conventions.md` for the full map and the "where does this
file go?" rules):

```
docs/         principles · templates · checklists · ADRs
ingestion/    ingestion-service source configs (tiers, watermarks, reconciliation)
dbt/          the five-layer medallion: staging(stg_) -> intermediate(int_) -> marts(mart_<domain>__)
catalogue/    OpenMetadata semantic YAMLs (module-semantics/)
quality/      DQF thresholds & test specs
consumption/  Superset dashboards & API contracts
security/     RBAC matrices, classification register
ops/          runbooks, monitoring config
```

The conventions are encoded in the seed files: `docs/CONVENTIONS.md` (naming + the five-layer rule
+ "generated artefacts are never hand-edited"), `dbt/dbt_project.yml` (per-layer materialisation
and schemas), `.pre-commit-config.yaml` (sqlfluff for dbt SQL, ruff for Python, yaml/whitespace
hygiene), and `tasks.py` / `Makefile` (the OS-agnostic task runner).

### 3 — Initialise git on the workstation and make the first commit

This is where the platform's version-control principle becomes concrete, and where the **Cowork
wrinkle** matters: the Cowork sandbox cannot delete files on the workstation, so a git run *inside
the sandbox* strands its own lock files and the next commit fails. So **git runs on the machine** —
via Desktop Commander or a terminal — never in the sandbox. See
`references/git-on-the-workstation.md` for the cross-OS commands and the lock-cleanup fix if a
sandbox git ever left a mess. The first commit:

```bash
# macOS / Linux (run on the workstation)
cd "/path/to/mtca-data-platform" && git init && git add -A && \
  git commit -m "chore: scaffold platform repo"
```
```powershell
# Windows (run on the workstation)
cd "C:\path\to\mtca-data-platform"; git init; git add -A; `
  git commit -m "chore: scaffold platform repo"
```

### 4 — Install pre-commit

```bash
python tasks.py setup     # creates the venv, installs deps + runs `pre-commit install`
```

After this, hygiene checks run on every commit. If a hook rewrites a file, stage it and commit
again — that's the hook doing its job, not an error.

## B — The shared git workflow (every skill points here)

This is the standard change cycle the other skills reuse. Keep it boring and identical on both OSes.

**Branch → change → commit → PR.**

```bash
# macOS / Linux
git switch -c <type>/<short-topic>      # e.g. feat/debt-aged-balances
# ... a skill writes its files into the repo ...
git add -A && git commit -m "<type>: <what changed>"
git push -u origin <type>/<short-topic>  # then open a PR for review
```
```powershell
# Windows
git switch -c <type>/<short-topic>
git add -A; git commit -m "<type>: <what changed>"
git push -u origin <type>/<short-topic>
```

Commit-message convention (used pack-wide): `<area>: <imperative summary>` — e.g.
`catalogue: add BOP semantic enrichment (DRAFT)`, `dbt: add int_taxpayer__master`,
`quality: tighten completeness threshold on mart_debt__aged_balances`.

**The rule every skill obeys:** finish by committing on the workstation. An artefact that exists
but isn't committed isn't done. Open a PR if the repo uses review; never hand-edit a generated
artefact (fix the spec/generator and regenerate).

## Reference material

- `references/repo-conventions.md` — the full directory map, naming rules, the five-layer medallion
  placement, and "where does this file go?" for every artefact type.
- `references/git-on-the-workstation.md` — the cross-OS git cheat-sheet, the Cowork
  "git-runs-on-the-machine" rationale, and the one-time lock-cleanup fix if an in-sandbox git ever
  stranded `.git/*.lock` files.
