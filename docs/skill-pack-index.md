# MTCA Data Platform — Skill Pack Index & Install Guide

The delivery guidance ships mainly as a **Cowork skill pack**: 13 installable skills that carry the
deterministic mechanics behind a SKILL.md of judgement and guardrails. This is the map and the
install/usage guide.

## Install

Each skill is a `.skill` file in `dist/`. In Claude Desktop (Cowork), open a `.skill` file and choose
**Save skill**. Install the whole pack, or just the skills for the dimension you're working on. All are
pure Python and cross-platform (Windows + macOS); `mtca-dev-workflow`'s `devcheck.py` reports what else
your workstation needs (git, dbt, …).

## The 13 skills, by band and delivery dimension

| Skill | Band / Dim | What it does |
|---|---|---|
| `mtca-architecture-principles` | Foundations · D0 | Principles register (P1–P14) + ADRs that decide by citation |
| `mtca-dev-workflow` | Foundations · D2/D8/D11 | Two-track method, cross-OS commands, commit-on-the-workstation, toolchain doctor |
| `repo-scaffold` | Foundations · D3/D5 | Scaffolds the mono-repo + owns the shared git workflow |
| `onboard-source` | Build · D4 | Profile → Bronze DDL → gated load → reconciliation manifests |
| `import-schema-to-catalogue` | Build/Catalogue · D7 | dbt `sources.yml` + OM technical metadata + reference vocabularies |
| `build-dbt-model` | Build · D5 | `stg_`/`int_`/`mart_` generator with `int_` join contracts (Taxpayer-360) |
| `add-dq-checks` | Build · D6 | Six-dimension DQ tests + thresholds, tagged for the quality badge |
| `legacy-module-to-openmetadata` | Catalogue · D7 | PowerBuilder source → draft table/column descriptions |
| `verify-catalogue-semantics` | Catalogue · D7 | DRAFT → VERIFIED gate (authoritative source / data arithmetic) |
| `build-superset-dashboard` | Ship · D9 | Superset dataset (metrics once) + dashboard manifest |
| `expose-api` | Ship · D9 | OpenAPI contract + parameterized SQL over a Gold mart |
| `production-readiness-check` | Run · D12 | Evidence-driven go-live gate (auto-checks + attestations) |
| `onboard-consumer` | Cross-cutting · X4 | Gap-analysis + plan to serve the next consumer (SAS, …) |

## The delivery loop (how they compose)

```
mtca-architecture-principles ─ decide by citation ─┐
                                                   ▼
repo-scaffold → onboard-source → import-schema-to-catalogue → build-dbt-model → add-dq-checks
                                  legacy-module-to-openmetadata → verify-catalogue-semantics
                                                   ▼
                       build-superset-dashboard / expose-api  (the consumption surfaces)
                                                   ▼
                   production-readiness-check → go-live → onboard-consumer (next consumer)
   (mtca-dev-workflow runs across all of it: generate offline, run on the stack, commit on the workstation)
```

Generate **offline** (Track A); run `dbt build`/loads/imports on the **stack/workstation** (Track B);
**commit on the workstation**. Gates compose — DQ green, catalogue VERIFIED, readiness PASS — so a
green readiness report means the slice cleared every gate with evidence.

## Standing rules the pack enforces

- **Decide by citation** (P-register); **generate, never hand-edit** (P5); **single source of truth /
  pull from Gold** (P6); **verify before publish** (P11); **reconcile every transfer** (P12);
  **version-controlled by default**, git on the workstation (P13); **cross-platform** (P14).
- **Every skill ends by committing its output** to the repo on the workstation — produced-but-uncommitted
  isn't done.

## What the team still owns (not automatable)

The skills generate and gate; people still: run the live `dbt build`/loads/imports, stand up CI and
monitoring, perform UAT, obtain the DPIA/DPO clearance, and record the go-live sign-off. The
`production-readiness-check` checklist names exactly these.

## Where to go next

- Sequencing (content-design §7): build order is D0–D3 foundations, then follow the Debt milestones
  M1→M6, pulling each skill in as the slice reaches it.
- The DQF (`frameworks/data-quality-framework/`) backs `add-dq-checks`, the readiness DQ items, and the
  verification gate.
