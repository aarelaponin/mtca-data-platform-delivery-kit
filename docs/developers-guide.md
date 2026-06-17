# MTCA Data Platform — Developer's Guide

**End-to-end Blueprint implementation with the `mtca-data-platform` plugin in Claude Cowork.**
Version 0.1 · for the MTCA IT Department Data Management team.

---

## 1. What this guide is

This is the hands-on manual for building the MTCA Data Platform described in the Data Platform
Blueprint — from an empty repository to a production Debt Management slice, and then to comprehensive,
all-data coverage. It assumes you work in **Claude Desktop (Cowork)** with the **`mtca-data-platform`
plugin installed**, so the 13 delivery skills are available to you.

It is sequenced: follow it top to bottom for the first (Debt Management) slice, then reuse the same
loop for every later source, mart and consumer. Each step tells you **what to do, what to say to
Cowork, what you must prepare, what you get back, where it runs, and the gate that must pass** before
you move on.

**How to read it:** §2 prerequisites · §3 how to work in Cowork with the plugin · §4 what you're
building (the Blueprint target) · **§5 the end-to-end build, milestone by milestone (the core)** · §6
after Debt: breadth and the next consumer · §7 the cross-cutting concerns (quality, security, CI,
ops, governance) · §8 the gates · §9 daily rhythm · §10 troubleshooting · §11 quick reference.

---

## 2. Prerequisites

**Tools & access (before M0):**

- **Claude Desktop with Cowork** and the **`mtca-data-platform` plugin** installed (Settings →
  Capabilities → install the plugin; confirm the skills appear).
- A **workstation** (Windows or macOS — both are supported) with: Python 3, Git, and — for the live
  build — dbt, and Docker if you want local services. Run the toolchain check (see §3) to see what's
  missing.
- **Network & platform access** per the Blueprint: the **MAGNET ↔ Azure VPN bridge**; credentials
  (via **Keycloak** SSO) for **ClickHouse**, **dbt**, **OpenMetadata**, **Superset**; and the
  manifest store (**PostgreSQL `dq`**).
- **Test environment with real data.** MITA does not yet have an anonymisation/pseudonymisation
  capability, so the test environment you develop against holds **real, un-anonymised Restricted
  data**. This *raises* the data-protection bar, it does not lower it — see the data-handling note
  in §7. **Do not start against real data until the DPO has approved its use in the test
  environment** (the DPIA must cover test, not only production).
- **Source access** to the legacy systems you will onboard (e.g. the Informix `irdnew` estate),
  read-only, from the platform network.

**Knowledge:** you don't need to memorise the method — the skills carry it. But read the **hand-over
brief** (`docs/handover-brief.md`) and skim the **DQF** (`frameworks/`) once, and keep the **Blueprint**
open as the architecture reference.

> If any access is missing, that is itself the first task — record it; `production-readiness-check`
> will require most of it before go-live anyway.

---

## 3. How to work in Cowork with the plugin

### Invoke skills by saying what you want

The skills trigger from natural requests — you don't call them by name. Examples:

- "Onboard the ARS accounting source into Bronze." → `onboard-source`
- "Build the Taxpayer-360 golden record and the debt aged-balances mart." → `build-dbt-model`
- "Add the data-quality checks to this mart." → `add-dq-checks`
- "Verify these BOP descriptions before we use them." → `verify-catalogue-semantics`
- "Are we ready to put Debt into production?" → `production-readiness-check`

If you want a specific skill, name it ("use repo-scaffold to lay out the repo"). When in doubt, ask
Cowork "which skill should I use to …" and it will pick.

### The two-track method (this is the most important habit)

The Cowork sandbox runs Python but has **no dbt-against-ClickHouse, no database, no live data, and it
cannot delete files on your workstation**. So every task is on one of two tracks — decide which up
front:

- **Track A — generate offline.** All the skills' generators (DDL, models, tests, catalogue input,
  dashboards, API, plans, gates) run in Cowork and produce files. Do these in Cowork and review the
  output there.
- **Track B — run on the stack / your workstation.** `dbt build`/`dbt test` against ClickHouse, the
  source loads, OpenMetadata ingestion, the Superset import, **and every `git` commit** must run on
  your machine. Cowork hands you a copy-pasteable, cross-OS command block; you run it and paste back
  the result.

The `mtca-dev-workflow` skill owns this split — ask it "which track is this on?" any time you're
unsure. **Git runs on your workstation**, never in the sandbox (the sandbox strands lock files).

### Set up your workstation (run once)

Ask Cowork: *"Check my toolchain for the data platform."* It runs `mtca-dev-workflow`'s `devcheck.py`
and reports what's present/missing on your OS. Then `python tasks.py setup` (after M0 scaffolds the
repo) installs the dbt + pre-commit stack.

### Everything ends in a commit

Each skill's last step is to write its output into the repo and commit it **on your workstation**
(`git add … && git commit …`, same on Windows and macOS). An artefact that exists but isn't committed
isn't done. Never hand-edit a generated file — change the spec and regenerate.

---

## 4. What you're building (the Blueprint target)

In one paragraph: a single, comprehensive platform that ingests **all** of MTCA's data into a
ClickHouse **medallion** (Bronze → Silver → Intermediate → Gold → Published), catalogues and quality-
gates it in **OpenMetadata** + **dbt**, and serves it to many consumers — Debt Management first, the
SAS risk project second, then the rest — through **Superset** dashboards and **APIs**, all secured by
**Keycloak** and observed by **Prometheus/Grafana**.

The pieces you will build, and the skill that builds each:

| Layer | What | Skill |
|---|---|---|
| Repo & conventions | the mono-repo, git workflow | `repo-scaffold` |
| Ingestion → Bronze | gated load, reconciliation | `onboard-source` |
| Catalogue (structure) | dbt sources, technical metadata, vocabularies | `import-schema-to-catalogue` |
| Catalogue (meaning) | descriptions from legacy code; DRAFT→VERIFIED | `legacy-module-to-openmetadata`, `verify-catalogue-semantics` |
| Silver / Intermediate / Gold | the five-layer dbt models, join contracts, Taxpayer-360 | `build-dbt-model` |
| Quality | six-dimension DQ gates + badge | `add-dq-checks` |
| Consumption | dashboards, APIs | `build-superset-dashboard`, `expose-api` |
| Go-live | the production-readiness gate | `production-readiness-check` |
| Next consumer | serve SAS and beyond | `onboard-consumer` |
| Foundations | principles, the dev method | `mtca-architecture-principles`, `mtca-dev-workflow` |

**The Debt Management slice is the spine.** You build the whole production path once, end to end, on
the bounded Debt use case — debt sources → Bronze → Silver/Intermediate → the debt Gold marts
(`mart_debt__aged_balances`, `mart_debt__collection_performance`, and `int_taxpayer__master` /
Taxpayer-360) → the Debt dashboard + API → production. Then you repeat the patterns for breadth and
the next consumer.

---

## 5. The end-to-end build — milestone by milestone

The Blueprint's Debt slice runs **M0 → M6**. Each milestone below has: **Goal**, **Skill(s)**, **Say
to Cowork** (a trigger), **Prepare** (inputs you bring), **Produces**, **Run live (Track B)**, and the
**Gate / DoD** that must pass before the next milestone.

### M0 — Foundation & environment

**Goal:** a version-controlled repo and a working environment for everyone.
**Skills:** `mtca-architecture-principles`, `mtca-dev-workflow`, `repo-scaffold`.

1. **Set the ground rules.** Say: *"List the platform principles"* (`mtca-architecture-principles`).
   Skim them; you'll cite them when decisions come up. Record any big decision as an ADR:
   *"Write an ADR: we use dbt + OpenMetadata for data quality, not SAS."*
2. **Check the toolchain.** Say: *"Check my workstation toolchain."* Install whatever's missing.
3. **Scaffold the repo.** Say: *"Scaffold the platform repo."* (`repo-scaffold`) — produces the
   mono-repo (dbt project, `ingestion/`, `catalogue/`, `quality/`, `consumption/`, `security/`,
   `ops/`, conventions, pre-commit, the cross-OS task runner).
   - **Run live:** on your workstation — `git init && git add -A && git commit -m "chore: scaffold
     platform repo"`, then `python tasks.py setup` (installs dbt + pre-commit). Push to your remote.
- **Gate / DoD:** repo exists and is committed; every team member can clone it and `devcheck.py`
  passes; the principles register is in `docs/`.

### M1 — Debt sources into Bronze, catalogued

**Goal:** the debt source tables land in Bronze, reconciled, tiered and catalogued.
**Skills:** `onboard-source` → `import-schema-to-catalogue` → (`legacy-module-to-openmetadata`) →
`verify-catalogue-semantics`.

1. **Profile before any DDL.** Say: *"Onboard the <debt source> into Bronze."* (`onboard-source`)
   It first **profiles** the source (fill rates, constant columns, real date coverage) and gives you a
   review report — the **human gate**. Decide the load set and the **tier** (debt sources are **Hot**,
   ~60-second freshness). **Prepare:** source host/db/user (password via env var), and the legacy
   inventory if you have one.
2. **Generate Bronze DDL & load.** The skill generates the ClickHouse Bronze DDL (money widened to
   `Decimal(38,s)`). **Run live (Track B):** apply the DDL, configure `ingestion/sources/<src>.yml`,
   run the gated load, and **verify the reconciliation manifests** (one SUCCESS row per table,
   `reconciled = true`, count equal to source).
3. **Register the structure for dbt + the catalogue.** Say: *"Import the <src> schema into the
   catalogue."* (`import-schema-to-catalogue`) — produces `dbt/models/_sources/<src>__sources.yml`,
   the OpenMetadata technical metadata, and reference-data **vocabularies** (code→label) for any
   lookup tables.
4. **Recover meaning (if legacy code exists).** For a legacy PowerBuilder module, say: *"Document the
   tables this module uses for the catalogue."* (`legacy-module-to-openmetadata`) — produces DRAFT
   table/column descriptions from the source.
5. **Verify the meaning.** Say: *"Verify these descriptions before we use them."*
   (`verify-catalogue-semantics`) — drive each description DRAFT → VERIFIED against the form/spec/code
   or by data arithmetic; the gate blocks anything still DRAFT from driving a mart or the hand-over.
- **Gate / DoD:** debt source tables in Bronze with passing **reconciliation manifests**; sources +
  technical metadata + vocabularies in the repo; descriptions for the columns you'll model are
  **VERIFIED**. Commit everything.

### M2 — Silver + the Intermediate join layer, tested

**Goal:** clean staging models and the cross-source join layer (incl. Taxpayer-360) build and pass.
**Skills:** `build-dbt-model`, `add-dq-checks`.

1. **Staging (1:1, no joins).** Say: *"Create the staging models for the debt source tables."*
   (`build-dbt-model`, `kind: staging`) — one `stg_<src>__<entity>` per source table, types/cleaning
   only.
2. **Intermediate (joins + golden record).** Say: *"Build int_taxpayer__master joining IRD identity
   and VAT on TIN."* (`build-dbt-model`, `kind: intermediate`) — the explicit join is a named model,
   and its join keys get **not-null + relationships tests (the join contract)**. Taxpayer-360 is the
   canonical `int_` golden record; later marts compose from it.
3. **Quality on what you've built.** Say: *"Add the DQ checks to these models."* (`add-dq-checks`) —
   six-dimension, dimension-tagged tests + thresholds.
   - **Run live (Track B):** `python tasks.py dbt-build && python tasks.py dbt-test`. The join-contract
     and DQ tests must be green.
- **Gate / DoD:** Silver + `int_` (incl. Taxpayer-360) build and pass tests; a fan-out or orphaned key
  fails a test (it must). Commit.

### M3 — The debt Gold marts

**Goal:** the consumer-facing debt marts build, pass DQ, and are catalogued/verified.
**Skills:** `build-dbt-model`, `add-dq-checks`, `verify-catalogue-semantics`.

1. **Build the marts.** Say: *"Build mart_debt__aged_balances and mart_debt__collection_performance
   from the intermediate layer."* (`build-dbt-model`, `kind: mart`) — marts **compose from `int_`,
   never re-join raw sources**.
2. **Gate their quality.** Say: *"Add six-dimension DQ checks to the debt marts."* (`add-dq-checks`) —
   including the freshness test at the **Hot** SLA and the accuracy reconciliation (implement the real
   reconciliation; the stub is an open control, not a pass).
3. **Verify their columns.** Ensure every mart column's meaning is VERIFIED (`verify-catalogue-
   semantics --gate`).
   - **Run live:** `dbt build`/`dbt test` green; the quality badge shows green in OpenMetadata.
- **Gate / DoD:** debt Gold marts build, carry green DQ gates, and every column is VERIFIED. Commit.

### M4 — The Debt Management dashboard

**Goal:** the debt team sees live debt data in Superset.
**Skill:** `build-superset-dashboard`.

1. Say: *"Build the Debt Management dashboard over the debt marts."* — produces the Superset
   **dataset** (with metrics defined once: `total_outstanding`, `debt_to_assessment`, ageing bands)
   and the **dashboard manifest** (charts: aged balances by band, risk-ranked debtors, collection
   tracking, instalment monitoring; RBAC roles; alerts).
   - **Run live (Track B):** import the dataset into Superset (set the real database connection), build
     the charts from the manifest, apply the **Keycloak RBAC** roles (Restricted-by-default), and wire
     the alerts.
- **Gate / DoD:** the dashboard renders live debt data, is role-restricted, and its alerts are live.

### M5 — The API + alerts (the DMBB/workflow surface)

**Goal:** the no-code/low-code Debt Management (DMBB/Joget) workflow reads debt data over an API.
**Skill:** `expose-api`.

1. Say: *"Expose the debt aged-balances mart as an API for the workflow."* — produces the **OpenAPI
   3.0 contract** + **parameterized SQL**, with Keycloak bearer auth and RBAC.
   - **Run live:** implement the endpoint against the contract, enforce auth/roles at the gateway,
     validate the contract, and connect the DMBB workflow.
- **Gate / DoD:** the workflow consumes the API; contract and served fields match; alerts (e.g. the
  90+ ageing-band growth) fire.

### M6 — Production readiness & go-live

**Goal:** Debt Management goes live with sign-off and a safety net.
**Skill:** `production-readiness-check`.

1. Say: *"Run the go-live checklist for the Debt release."* — it **auto-checks** the repo (CI, ops
   runbook, rollback, DQ gates, dashboard/API RBAC, alerts, secrets) and takes **attestations** for
   the rest (deployed/promoted, monitoring live, **DPIA/DPO clearance for real data**, UAT sign-off,
   go-live sign-off), and returns a hard **pass/fail**.
2. Close every ❌: stand up CI, write and **rehearse** the rollback, get the debt-team UAT and the DGC
   sign-off. (The DPIA covering real data — used in both test and production — should already be
   approved per §7; confirm it here.)
   - **Run live:** promote dev → test → prod through the pipeline; cut over; hypercare.
- **Gate / DoD:** `production-readiness-check` returns **GATE PASS**; keep the green report as the
  release evidence. **You are in production.**

> A complete worked run of M0→M6 (generation only, on sample data) is in `examples/golden-path/` — run
> `bash run_golden_path.sh` to see exactly what each milestone produces.

---

## 6. After Debt — breadth and the next consumer

The Debt slice proved the patterns. Two threads continue in parallel:

**Breadth (the whole estate).** Bring the rest of the legacy estate into Bronze + catalogue over time
— all nine databases / 5,170+ tables — using the **same M1 loop** per source: profile → load →
reconcile → catalogue structure → recover & verify meaning. Tier each source (Hot/Warm/Cold/Archive),
run the **mystery-table A/B/C triage** as a scope gate, and keep a coverage backlog. Every source you
add is reusable by any consumer.

**The next consumer (depth).** When a new consumer needs data, say: *"Onboard the SAS risk project as
a consumer."* (`onboard-consumer`) — it diffs the consumer's needs against the current Gold marts and
produces a **gap analysis + onboarding plan + a Definition-of-Done**. Close the gaps by building into
**shared Gold** (never a side-pipeline), expose the surface (a dashboard, an API, or a Gold **feed**),
set RBAC, and gate. **SAS** is the second consumer: it reads Gold for risk analytics and **writes risk
scores back** as a Gold mart (`mart_risk__scores`) — modelled, DQ'd and verified like any other, so the
dashboard and API can read the scores too. (SAS runs under the **AI-10 Restricted-data** rules — the
DPIA gate applies.)

The platform gets richer with each consumer: the first is the hardest; every later one is mostly reuse.

---

## 7. Cross-cutting concerns (apply throughout, not at the end)

- **Data quality (DQF).** Every mart carries the six-dimension gates from `add-dq-checks`, tagged so
  the reconciler rolls them into the 0–100 **quality badge** in OpenMetadata (the headline score the
  programme tracks to ~90% by Q4 2026). dbt tests are **gates** (fail the build); the OpenMetadata
  profiler does fitness **monitoring** (incidents). See `frameworks/data-quality-framework/`.
- **Security & data protection — real data in test (read this).** Restricted-by-default;
  classification cascades; access via Keycloak RBAC. Because MITA has no anonymisation capability yet,
  the **test environment holds real, un-anonymised Restricted data**, so it must be treated with the
  **same protection as production from day one**, with these compensating controls:
    - **DPO approval first.** The **DPIA must explicitly cover the test/development environment** and
      the residual risk of using production-grade personal data outside production; the DPO signs off
      *before* the team touches real data (GDPR Art. 35; MITA AI-10/SEC-02).
    - **Named, least-privilege access** via Keycloak — only authorised DP-team members, no shared
      accounts; **audit logging** of access and queries on from the start.
    - **The environment is Restricted:** encrypted at rest/in transit, on the MAGNET/secured network,
      **no copying data to laptops, email, external drives, screenshots or chat tools**, and secure
      disposal of any extract.
    - **Record it as a known constraint** (an ADR via `mtca-architecture-principles`): real data is
      used in test *pending* an anonymisation/pseudonymisation capability at MITA, which is the agreed
      remediation; revisit when the tool exists.
  This is still a hard go-live gate (`production-readiness-check` SEC-2) — now covering test as well as
  production.
- **Version control & CI.** Everything-as-code, committed and PR-reviewed; git runs on the
  workstation. Stand up CI to run `dbt test` and the hygiene hooks on every change (a failing test
  blocks promotion). Never hand-edit a generated artefact — fix the spec and regenerate.
- **Observability & operations.** Prometheus/Grafana monitoring; freshness SLAs per tier (Hot < 5 min);
  an ops runbook for ingestion/build/dashboard failures; alerts wired. "You build it, you run it."
- **Governance & evidence.** Report to the DGC with the monthly scorecard/KPIs; keep manifests, test
  history, the readiness report and sign-offs as audit evidence. Evidence — not assertion — is the
  governance currency, and it's what the **DcP3 hand-over** to the ITCAS vendor reads from the
  catalogue (only VERIFIED columns ship).

---

## 8. The gates (nothing ships amber)

The platform is a sequence of gates that compose. A green production-readiness report means the slice
cleared all of them, with evidence:

| Gate | Owner skill | "Pass" means |
|---|---|---|
| Onboarding profile reviewed | `onboard-source` | the load set + tier were decided from real profile data |
| Reconciliation manifest | `onboard-source` | loaded count == source count, one SUCCESS row per table |
| Join contract | `build-dbt-model` | `int_` join keys pass not-null + relationships tests |
| Six-dimension DQ | `add-dq-checks` | the mart's dimension-tagged tests are green |
| Catalogue verification | `verify-catalogue-semantics` | every mart/hand-over column is VERIFIED, not DRAFT |
| RBAC | `build-superset-dashboard` / `expose-api` | the surface is role-restricted (Restricted-by-default) |
| DPIA / DPO | (attested) | real Restricted data is cleared for use |
| Production readiness | `production-readiness-check` | all blockers pass; report is green |

---

## 9. Working as a team of three (and the daily rhythm)

Three developers can work in parallel without the outputs diverging — **because the skills, the
conventions and the gates enforce consistency for you**. Three people using the same skills produce
uniform work by construction: `repo-scaffold` fixes the layout and naming; the generators are
deterministic; `mtca-architecture-principles` settles design choices by citation; and the `int_` join
contracts, the DQ gates and the verification gate catch divergence automatically. So the job is to
**split work so people don't collide, and review each other** — not to make everyone do the same thing.

**Keep your domain ownership — own a domain end-to-end.** The team already splits responsibility by
**domain** (e.g. one developer for income tax / IRD, one for VAT, one for customs/excise), and that is
the right model — keep it. Each developer carries their domain through the **whole loop**: onboard its
sources → model `stg_`/`int_`/`mart_` → DQ → catalogue & verify → expose the surface → gate. Vertical,
end-to-end ownership means few hand-offs and one clear owner per slice — far better than splitting by
layer ("all staging" vs "all marts"), which creates wait-chains and blurred ownership.

- **Build the first Debt slice together first.** Before splitting fully, build one slice as a team —
  one developer drives, the other two review, **rotating the keyboard per milestone** (M1 ingestion →
  M2/M3 modelling → M4/M5 consumption → M6 go-live). Everyone sees the whole path once; this is the
  shadow → pair → lead start, and it sets the patterns each domain then copies.
- **Then run domains in parallel** — each owner builds their domain with the same skills, conventions
  and gates, so the outputs match by construction.

**The real consistency risk with a domain split is the shared, cross-domain core — give it one owner.**
Some things are not owned by any single domain because every domain uses them: the **Taxpayer-360
golden record** (`int_taxpayer__master`, which joins identity across domains on TIN), the **shared
metric definitions** (e.g. `total_outstanding`, ageing bands), the shared **reference vocabularies**,
the **naming conventions**, and the **`main`** branch. Appoint **one rotating "platform steward"** to own
these. **Domain owners compose from them and request changes by PR — they never fork or redefine them**
(P6: one definition per fact, pull from Gold). A cross-domain mart (e.g. one joining debt + VAT) is built
from the domain `int_` models, with the steward reviewing the join. This single rule prevents the classic
failure of three domains each inventing their own "taxpayer".

**Git is the consistency backbone** (this is where parallel work converges):

- Branch per task (`feat/debt-aged-balances`); keep PRs small.
- **Every PR is reviewed by another developer before merge** — peer review is where consistency is
  actually enforced.
- `main` is **protected**, and **CI runs `dbt test` + the pre-commit hooks on every PR** — a red test
  blocks the merge.
- **One artefact, one owner at a time** — don't let two people edit the same model/spec; the board
  shows who owns what.

**Cadence:** a 15-minute daily standup (who's on what, blockers, who needs whose output); a shared
backlog/board with clear owners (the coverage and `onboard-consumer` backlogs feed it); a weekly
integration + a short design huddle for any cross-cutting decision (**record it as an ADR** via
`mtca-architecture-principles`). **Definition of Done = the gates are green** (DQ, verify, readiness).

The four rules that keep three people aligned: **decide by citation** (principles/ADRs), **generate —
never hand-edit**, **one definition per fact** (pull from Gold), and **peer-reviewed PRs through CI**.
Rotate the roles so all three can do every part by the end.

### Daily rhythm

- **Pick the next slice** (a source, a mart, a dashboard) from the backlog.
- **Decide the track**: generate in Cowork (Track A); run dbt/loads/imports and commit on your
  workstation (Track B). Ask `mtca-dev-workflow` if unsure.
- **Use the skill, don't free-hand**: say what you want; review the generated spec/output; fill any
  `TODO`/DRAFT; run it live; **commit**.
- **Pair**: shadow → pair → lead. The first time on each skill, pair with the STX/contractor; then the
  team leads. The skill is the script for this.
- **Close the loop**: run the relevant gate (DQ, verify, readiness) before calling it done.

---

## 10. Troubleshooting & FAQ

- **"dbt didn't run in Cowork."** Correct — that's Track B. Cowork *generates* the models; you run
  `dbt build` on your workstation/stack. (`mtca-dev-workflow`.)
- **"git says `index.lock` exists / can't commit."** A git command was run inside the Cowork sandbox,
  which can't clean up its lock files. Run git **on your workstation**; if locks are stranded, delete
  `.git/index.lock` (see `repo-scaffold/references/git-on-the-workstation.md`).
- **"The script left files inside the skill folder."** Point `--out`/`--repo` at your repo's workspace
  (e.g. `catalogue/module-semantics/`), not the skill directory.
- **"A YAML-spec skill says 'install pyyaml'."** Install PyYAML (`pip install pyyaml`, or
  `python tasks.py setup`). The spec-reading skills need it.
- **"The accuracy DQ test passes but we never wrote the reconciliation."** That's the deliberate
  stub — accuracy is an **open control** until you implement the real cross-source check; don't read
  the green as done.
- **"A description is unclear."** Mark it `to_confirm` (not a guess) and resolve it with the Data
  Owner; the verify gate keeps DRAFT meaning out of marts.
- **"Should we use <held licence / tool X> for Y?"** Ask `mtca-architecture-principles` — most such
  questions are already settled by a principle; record the decision as an ADR.

---

## 11. Quick reference

**The 13 skills**

| Skill | Use it to… |
|---|---|
| `mtca-architecture-principles` | decide by citation; write ADRs |
| `mtca-dev-workflow` | pick the track; cross-OS commands; commit on the workstation |
| `repo-scaffold` | scaffold the repo + the shared git workflow |
| `onboard-source` | profile → Bronze DDL → gated load → reconcile |
| `import-schema-to-catalogue` | dbt sources + technical metadata + vocabularies |
| `legacy-module-to-openmetadata` | recover meaning from legacy PowerBuilder code |
| `verify-catalogue-semantics` | DRAFT → VERIFIED gate |
| `build-dbt-model` | stg_ / int_ (join contracts, Taxpayer-360) / mart_ |
| `add-dq-checks` | six-dimension DQ + the quality badge |
| `build-superset-dashboard` | the dashboard (dataset + metrics + RBAC + alerts) |
| `expose-api` | the OpenAPI contract + SQL for a consumer |
| `production-readiness-check` | the go-live gate |
| `onboard-consumer` | serve the next consumer (gap analysis + plan) |

**Where things live (in this kit)**

- Install: `dist/mtca-data-platform.plugin` · skills source: `skills/`
- This guide + the brief + the install index: `docs/`
- The Data Quality Framework: `frameworks/data-quality-framework/`
- A full worked run of the loop: `examples/golden-path/`

**The milestones:** M0 environment · M1 Bronze + catalogue · M2 Silver + Intermediate · M3 debt Gold
marts · M4 dashboard · M5 API + alerts · M6 production. Breadth (whole estate) and the next consumer
(SAS) follow once the patterns are proven.

---

_This guide describes the method; the live build-out is yours. Start at M0, keep each gate green, and
the Debt slice — then the platform — reaches production with evidence behind it._


