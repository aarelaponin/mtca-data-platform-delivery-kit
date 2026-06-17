# Track A (offline) vs Track B (live stack / workstation)

Decide the track before you start. The cost of guessing wrong is a wasted round-trip or a false "done".

## Track A — runs offline (in the Cowork sandbox), data-independent

Do these here and show the result; don't hand them back:

| Task | Tool |
|---|---|
| Scaffold the repo | `repo-scaffold` (`scaffold_repo.py`) |
| Generate Bronze DDL from a schema spec | `onboard-source` (`gen_bronze_ddl.py`) |
| Profile SQL (review, `--dry-run`) | `onboard-source` (`profile_source.py --dry-run`) |
| Generate dbt sources + technical metadata + vocabularies | `import-schema-to-catalogue` |
| Generate stg_/int_/mart_ models + tests | `build-dbt-model` |
| Generate six-dimension DQ checks | `add-dq-checks` |
| Recover descriptions from PowerBuilder source | `legacy-module-to-openmetadata` |
| Ledger/gate verification (no data-arithmetic data) | `verify-catalogue-semantics` (emit-ledger/apply/gate) |
| Generate dashboard assets / API contract + SQL | `build-superset-dashboard` / `expose-api` |
| Consumer gap analysis + plan | `onboard-consumer` |
| Readiness gate (auto repo checks) | `production-readiness-check --check` |
| ADRs + principles | `mtca-architecture-principles` |
| Validate generated YAML/SQL/OpenAPI structurally | python parse / linters |

All of these are deterministic and verifiable without a database — run them and prove the output.

## Track B — must run on the workstation / live stack

Produce a cross-OS command block; the user runs it and pastes back:

| Task | Why it's Track B |
|---|---|
| `dbt build` / `dbt test` against ClickHouse | needs the warehouse + data |
| The gated source load (`profile_source` live, the extractor) | needs the source DB + ClickHouse |
| Reconciliation manifest checks | needs the manifest store (PostgreSQL `dq`) |
| OpenMetadata ingestion / push (connector, glossary) | needs the running OM + services |
| Superset dataset/dashboard import; RBAC; alerts | needs running Superset + Keycloak |
| API deploy + contract validation against the gateway | needs the API layer + Keycloak |
| Data-arithmetic verification (`verify --check-identity` on real rows) | needs the data |
| The live half of readiness (monitoring, UAT, DPIA, sign-off) | needs people + running systems |
| **Any git commit/push** | the sandbox can't delete lock files → git runs on the machine |

## The honesty rule

State which track every result is on. "Generated and validated the models (Track A); run `dbt build`
on your workstation to materialise them (Track B)." A thing that only ran in your head is not done — say
so, and give the command to finish it.

## Optional: deeper local runs

If a team member wants to run `dbt build` locally (not just generate), they can stand up a local
ClickHouse in Docker (`docker compose` with a ClickHouse image) and point `dbt/profiles.yml` at it —
then `dbt build` becomes Track A for them. That's the OS-agnostic path (containers) the platform favours
(P14); it's optional, and the default remains generate-offline / run-on-the-stack.
