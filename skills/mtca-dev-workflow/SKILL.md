---
name: mtca-dev-workflow
description: >-
  How to build, run, test, generate, deploy and verify the MTCA Data Platform reliably on a mixed
  Windows + macOS team using Claude Cowork — the two-track method (what runs offline in the sandbox vs
  what must run on the live stack/workstation), the cross-OS command discipline, commit-on-the-workstation
  git, and the end-to-end dev loop that ties the skill pack together. Use this WHENEVER work touches
  building or running the platform and you need to do it correctly the first time: "run the tests",
  "rebuild the models", "regenerate", "is it deployed", "set up my workstation", "why did dbt not run
  here", "give me the commands to run", "check my toolchain", "how do we work on Windows AND Mac". It
  exists because the Cowork sandbox has no dbt/ClickHouse/live data and can't delete files, so platform
  work needs a specific two-track, cross-OS method this skill makes dependable. Pure Python.
---

# MTCA dev workflow (two-track, cross-OS)

This captures how to execute day-to-day platform work correctly the first time, given two constraints
that are easy to forget and embarrassing to rediscover mid-task.

## The two constraints that shape everything

1. **The Cowork sandbox is a generic Linux box with Python only.** It has **no dbt-against-ClickHouse,
   no ClickHouse/PostgreSQL, no OpenMetadata, no live data**, and — critically — **it cannot delete
   files on the workstation** (so an in-sandbox `git` strands lock files). The real platform runs on the
   MTCA stack; the team drives it from their **Windows and macOS** workstations.
2. **The team is mixed-OS.** Every command must work on both PowerShell and bash; never assume one shell.

So there are exactly **two tracks**, and choosing the right one up front saves a wasted round-trip.

**Track A — do it offline (first choice when possible).** The pure-Python, data-independent work runs
in the sandbox today: running the skill-pack generators (DDL, models, tests, catalogue, dashboards,
API, plans), validating their output, parsing/linting, the readiness and verification gates that don't
need live data. If the question is "is the *logic/structure* correct?" — generate it and show the
result; don't hand it back to the user.

**Track B — hand the user exact commands for the live stack / workstation.** Anything needing dbt
against ClickHouse, the OpenMetadata connector, Superset, real/mock data, **or git** must run on the
workstation. The sandbox can't do these, so the deliverable is a **clean, copy-pasteable command block
for the user's OS** that they run and paste back. Be honest about which track a task is on — claiming
something is "done" when it only ran in your head is the failure mode to avoid.

## Cross-OS command discipline

Every command block handed over follows these rules (mixed Windows + macOS):

- **Give both shells** when it matters: a `# macOS / Linux` bash block and a `# Windows (PowerShell)`
  block. Prefer OS-agnostic entry points so you often don't have to: `python tasks.py <target>`,
  `docker compose`, `uv`.
- **Quote paths** — workstation paths contain spaces and backslashes; quote them, and use the OS's
  separator (`/` vs `\`).
- **One command per line**, so a failure points at the exact step.
- **No inline `#` comments inside an interactive block** — put explanation in prose outside it.
- **Python is `python` on Windows, `python3` on macOS/Linux** — `devcheck.py` reports which you have.

## Git runs on the workstation (never in the sandbox)

Because the sandbox can't delete lock files, **git runs on the machine** — via Desktop Commander or a
terminal — same workflow on Windows and macOS. The skills write files into the repo; the commit happens
on the workstation. See `repo-scaffold/references/git-on-the-workstation.md` for the cross-OS cheat-sheet
and the lock-cleanup fix. This is P13 (version-controlled) made operational under the Cowork constraint.

## Set up a workstation

```bash
python3 scripts/devcheck.py        # macOS / Linux — what's installed, what's missing
```
```powershell
py -3 scripts\devcheck.py          # Windows
```
It probes git, dbt, uv, pre-commit, docker, clickhouse-client and reports present/missing (exit non-zero
if a required tool is missing). Then `python tasks.py setup` (from `repo-scaffold`) installs the dbt +
pre-commit stack into a venv. See `references/local-vs-server.md` for the full per-task track split.

## The end-to-end dev loop (how the skills compose)

```
repo-scaffold ──▶ onboard-source ──▶ import-schema-to-catalogue ──▶ build-dbt-model ──▶ add-dq-checks
   (Track A: scaffold)   (B: profile+load)    (A: sources+vocab)        (A: stg_/int_/mart_)   (A: DQ tests)
        │                                                                                          │
        ▼                                                                                          ▼
   legacy-module-to-openmetadata ──▶ verify-catalogue-semantics ──▶ build-superset-dashboard / expose-api
        (A: draft descriptions)         (A: gate DRAFT→VERIFIED)          (A: consumption surfaces)
                                                                                  │
                                                                                  ▼
                                            production-readiness-check ──▶ (go-live)   onboard-consumer (next consumer)
                                               (A: gate; B: attest live)
```
- **Generate offline (Track A), run live (Track B).** Each generator runs in the sandbox; `dbt build`/
  `dbt test`, OM ingestion, Superset import and the load run on the workstation/stack.
- **Gates compose:** the DQ gate, the catalogue verify gate, and the readiness gate each fail loudly;
  a green readiness report means the slice passed them all (P10 evidence-not-assertion).
- **Nothing is hand-edited** (P5): fix the spec/skill and regenerate.

See `references/commands.md` for the concrete cross-OS command blocks per activity.

## Default behaviour when asked to "do" something

1. **Decide the track.** Verifiable with Python/generators alone? → Track A: do it and show the result.
   Needs the live stack, real data, or git? → Track B: produce the cross-OS command block.
2. **Generate, don't hand-edit.** Reach for the matching skill; change specs, regenerate.
3. **Finish on the workstation:** run the live step, then commit (Track B), then report honestly what ran
   where.

## Scripts & references

- `scripts/devcheck.py` — cross-OS toolchain doctor (`--json` for machine output).
- `references/commands.md` — per-activity command blocks (Windows + macOS): setup, build/test, load,
  catalogue ingest, dashboard import, readiness.
- `references/local-vs-server.md` — the precise Track A / Track B split for every platform task.
