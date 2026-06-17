# mtca-data-platform

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
