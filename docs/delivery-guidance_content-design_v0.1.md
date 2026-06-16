# Enabling No-Code / Low-Code Debt Management on the Data Platform
## Delivery Guidance — Content Design

**Version 0.1 (content design — scope, not yet sequenced) · 16 June 2026**
**Author:** Aare Lapõnin / IMF STX
**Purpose:** define *everything* the guidance must cover so the MTCA Data Management team can deliver, to production, the **Data Platform foundation** that MTCA's **no-code / low-code Debt Management** application (the DMBB building block) depends on. Debt Management itself is built on the low-code platform; it relies on the Data Platform for its data — the debt marts, the Single Taxpayer Account, risk scores, dashboards and the API it consumes.

**Important framing — a comprehensive platform; modules are its consumers, in sequence.** The Data Platform is a single, **comprehensive** foundation that ingests and catalogues *all* of MTCA's data — the full legacy estate (nine Informix databases, 5,170+ tables, tiered and described) — and serves it to many consumers. Debt Management (no-code/low-code, DMBB) is simply the **first consumer**; the **SAS project (advanced analytics / risk scoring) is the second**; compliance, refunds, revenue, Taxpayer-360, customs and the ITCAS feeds follow.

The platform build therefore has **two threads** the guidance must cover: **breadth** — bringing the whole estate into the platform (tiered ingestion + catalogue + quality across all sources); and **depth** — the per-consumer marts, dashboards and APIs. Debt Management is used as the first end-to-end production slice because it is concrete and bounded, and the cookbooks teach **repeatable patterns** — onboard *a* source, build *a* mart, expose *an* API, ship *a* dashboard — that scale from one source to the whole estate and from one consumer (Debt) to the next (SAS, then the rest). The slice is the proving ground, not the limit. This document designs the **content** of that guidance; the delivery sequence and packaging are decided afterwards (§7).

---

## 1. Who this is for, and the design stance

The Data Management team is new to structured, production-grade delivery; the Data Platform is likely their first system to reach production. The guidance therefore must **carry the structure for them** rather than assume it. Five stances shape every dimension below:

- **One vertical slice, learn by doing.** Master the whole production path once, on the bounded Debt Management slice — not an abstract methodology.
- **Structure lives in the artifacts.** Each task has a fill-in template and a Definition-of-Done checklist; discipline is a side-effect of using them.
- **Gates over judgement.** "Done when…" checklists at each step; quality and production-readiness are ticked boxes, reusing the DQF gates.
- **Shadow → pair → lead.** STX/contractor does it first (team watches), then pairs, then the team leads. The cookbooks are the script for this.
- **Both registers, always.** Every dimension ships with *Principles* (the why/rules) **and** *Cookbooks* (exact how) — the team was explicit on this.
- **Cross-platform by default (Windows + macOS).** The team works on mixed Windows and Mac workstations, so every cookbook gives commands for **both** — favour OS-agnostic tooling (containers, `uv`, a `make`/task runner, VS Code; WSL2 on Windows) and never assume a single shell or OS.
- **Version-controlled by default.** Nothing the team produces should live only in a chat, a Downloads folder, or a personal drive. Every artifact a cookbook or skill creates — a spec, a model, a description YAML, a checklist result — is written into the **versioned repository** and committed, so the platform's definitions and the evidence of its delivery have history, review and a single source of truth. Practical note for Cowork: the Cowork sandbox cannot delete files on the workstation, so **git itself runs on the machine** (via the desktop file tools / Desktop Commander, or a terminal) — the skills write files into the repo and commit them there; they never assume an in-sandbox git.

## 2. The artifact taxonomy (how every dimension is documented)

Each dimension is delivered as a consistent bundle:

| Artifact | What it is | Answers |
|---|---|---|
| **P — Principle** | Short, opinionated rules and rationale for the area | "Why, and what's the rule?" |
| **C — Cookbook** | Step-by-step procedure for one concrete task — commands, file paths, a worked example on the Debt slice | "How, exactly?" |
| **T — Template** | A fill-in-the-blanks file (spec, config, doc) that embeds the structure | "What do I produce?" |
| **Ch — Checklist** | Definition-of-Done / gate — boxes that must be ticked to pass | "Is it done / safe to ship?" |

A dimension is "covered" only when it has at least its P, its core C(s), the T it produces, and its DoD Ch.

---

## 3. The competency map — the dimensions of development

Grouped into four capability bands plus cross-cutting. Each dimension lists: **Scope · Key topics · Artifacts · Outcome (DoD) · Reuses**.

### BAND 1 — FOUNDATIONS (how we work)

**D0. Architectural principles register**
- *Scope:* a single, numbered, **priority-ordered and citable** set of platform principles (open-source / no lock-in; classification-as-foundation; automation-first; tables-in-configuration; single source of truth; build-capability-not-dependency; technology-follows-workload; evidence-not-assertion; …), distilled from the Blueprint into one register that settles "X-or-Y / build-or-buy / now-or-later" decisions **by citation** — and is deliberately silent on tactical questions (file paths, syntax, ops).
- *Artifacts:* P (the register itself) · C (apply the principles to a decision; record an architecture decision) · T (ADR template) · Ch (decision-review checklist).
- *Outcome:* weighty decisions are made consistently and by citation — e.g. the "we already hold a SAS licence" debate becomes a one-line reference.
- *Reuses:* Blueprint (design principles); the ARMS principles register (P1–P14) as the model.

**D1. Delivery lifecycle & ways of working**
- *Scope:* what "production" means; environments (dev → test → prod); the vertical-slice method; backlog/board; tickets with acceptance criteria; cadence (daily standup, weekly review, monthly DGC); definition-of-done & gates as a concept.
- *Artifacts:* P (delivery principles) · C (run a sprint / move a ticket through the board) · T (ticket template; sprint-plan template) · Ch (Definition-of-Done master).
- *Outcome:* the team runs a visible, gated backlog with a heartbeat.
- *Reuses:* Capacity-Building Workshop (roles, cadence).

**D2. Environment, tooling & access**
- *Scope:* the stack (ClickHouse · dbt · OpenMetadata · Superset · Keycloak · ingestion service · PostgreSQL state/dq · Prometheus/Grafana); workstation setup; credentials & SSO (Keycloak); MAGNET–Azure network; the dev databases (anonymised) prerequisite.
- *Artifacts:* P (open-source, on-platform) · C (set up a workstation; connect to ClickHouse/dbt/OM; get credentials) · T (environment config / .env template) · Ch (environment-ready checklist).
- *Outcome:* every team member can build and run locally against dev.
- *Reuses:* Blueprint (architecture); Prerequisites memo (environment).

**D3. Version control & collaboration (Git)**
- *Scope:* Git basics; the mono-repo layout; branching; pull requests & review; baseline-as-code; commit hygiene; never hand-edit generated artefacts. **Cross-OS + Cowork git mechanics:** the same git workflow on Windows and macOS; and — because the Cowork sandbox cannot delete files on the workstation (so in-sandbox `git` strands lock files) — **git runs on the machine**: skills/cookbooks write outputs into the repo, then commit via Desktop Commander (or a terminal) on the workstation. **Every skill ends by committing its output here** — version control is the last step of every cookbook, not a separate dimension.
- *Artifacts:* P (everything-as-code, PR-reviewed; commit-on-the-workstation) · C (branch → commit → PR → merge; review a PR; **commit a skill's output to the repo on Windows/macOS**) · T (PR template; commit-message convention) · Ch (PR-ready checklist).
- *Outcome:* all platform definitions and delivery evidence live in Git, reviewed; every skill writes through to a commit.

### BAND 2 — BUILD (turn legacy data into trusted models)

**D4. Source onboarding & ingestion**
- *Scope:* profile a source *before* DDL; the mystery-table A/B/C triage; design Bronze DDL (Informix→ClickHouse types, money-widening); ingestion-service config (Hot/Warm/Cold/Archive tiers, watermarks, 60-sec Hot for debt); run a load; manifests + reconciliation gates; troubleshoot a failed/partial load.
- *Artifacts:* P (every custody transfer reconciled; no silent fallback) · C (onboard a source end-to-end; configure a tier; rerun a failed load) · T (source-onboarding spec; Bronze DDL template; ingestion config) · Ch (onboarding gate; load DoD).
- *Outcome:* the debt source tables land in Bronze, reconciled, tiered, catalogued.
- *Reuses:* DQF (S1/S2 controls); Catalogue/Visual-Expert column work.

**D5. Data modelling & transformation (dbt) — the five-layer medallion**
- *Scope:* the **five-layer medallion** — Bronze → Silver (`stg_`) → **Intermediate (`int_`)** → Gold (`mart_`) → Published. **Silver `stg_`** = one model per source table, types/cleaning only, *no joins*. **Intermediate `int_`** = the explicit **cross-source join layer and golden-record hub** — joins are declared *as dbt models*, documented in `_int__models.yml`, with the join **contract enforced by dbt tests** (not-null join keys, `relationships`); hand-authored `int_` joins coexist with any generated models. The **Taxpayer-360 / Single Taxpayer Account is the canonical `int_` golden-record model** (joining across the nine databases on TIN), and the **debt marts compose from `int_` objects — never re-joining raw sources**. Plus: persisted-intermediate materialisation, incremental models, macros, in-model docs, `dbt build`/`dbt test`.
- *Artifacts:* P (the five-layer rule, set once; Silver = one model per source table; **`int_` owns all cross-source joins**; marts compose from `int_`; naming `stg_/int_/mart_<domain>__<desc>`; persist expensive joins) · C (write a staging model; **build an `int_` join / golden-record model with a contract test**; build a Gold mart) · T (model spec; `int_` join spec; schema.yml template) · Ch (model DoD; **join-contract gate**; PR gate).
- *Outcome:* Silver, the `int_` join layer (incl. Taxpayer-360) and the debt Gold marts build and pass tests.
- *Reuses:* ARMS Intermediate-layer convention (`int_taxpayer__master`, contracted joins); DQF tooling analysis; Blueprint (marts, Taxpayer-360).

**D6. Data quality in practice (the DQF, applied)**
- *Scope:* build-time contracts (dbt tests) vs fitness monitoring (OpenMetadata); the six dimensions & per-table gates; quality thresholds (block/warn/accept); reconciliation; the reconciler/badge; raising and closing an incident.
- *Artifacts:* P (the nine DQ principles) · C (write a dbt test; add an OM test; investigate an incident) · T (quality-threshold schedule; test spec) · Ch (quality gate per mart).
- *Outcome:* the debt marts carry green quality badges and gated tests.
- *Reuses:* **MTCA Data Quality Framework v0.1** (the whole thing).

**D7. Data catalogue & metadata (OpenMetadata) — with a verification gate**
- *Scope:* catalogue a table/columns; technical metadata + **reference-data vocabularies** from the source DDL; draft descriptions (the PowerBuilder-source method); **the verification gate — a description is DRAFT until VERIFIED against an authoritative source (the official form/spec, the application code, or data arithmetic — e.g. a stated total reconciles on the real rows) or explicitly marked TO-CONFIRM; only VERIFIED descriptions may drive marts or the DcP3 handover**; business glossary; lineage; classification/tags; ownership; assemble the handover package.
- *Artifacts:* P (metadata lands on the entity; **describe → verify → publish; never ship an unverified stub — a wrong description becomes a wrong number**) · C (catalogue & describe a table; **verify a description against the authoritative source / by data arithmetic**; import DDL + vocabularies; push a semantic YAML; record lineage) · T (table/column description YAML — the BOP example; verification log) · Ch (catalogue-entry DoD; **verification gate**; EA-11 fields present).
- *Outcome:* every debt table/column is described, **verified** and owned in the catalogue.
- *Reuses:* BOP semantic enrichment; PowerBuilder-source report; ARMS verified-semantics gate (the "verified box map" / R401-M lesson) + DDL-to-catalogue import; catalogue plan.

### BAND 3 — SHIP (get it safely into production)

**D8. CI/CD & deployment**
- *Scope:* CI runs dbt tests on every change; promotion dev → test → prod; deploying models, dashboards and config; the deployment runbook; rollback; release notes.
- *Artifacts:* P (a failing test blocks promotion; reproducible deploys) · C (set up CI; promote a change to prod; roll back) · T (release-notes template; deployment runbook template) · Ch (release gate / go-no-go).
- *Outcome:* changes reach prod through a repeatable, gated pipeline.

**D9. Consumption — dashboards & APIs**
- *Scope:* build the Superset **Debt Management Dashboard** (aged balances, risk-ranked debtor list, collection tracking, instalment monitoring); the semantic layer & calculated metrics (ageing bands, debt-to-assessment ratio, risk bands); RBAC on dashboards; threshold alerts (ageing shift); expose an API endpoint for the DMBB/Joget workflow; the **Gold-layer feed the SAS project (the platform's second consumer) reads for risk analytics**, with risk scores written back to Gold; WCAG 2.1 AA accessibility. The dashboard/API/consumer-feed patterns are written to be reused by every later consumer.
- *Artifacts:* P (one semantic definition, reused everywhere; accessible by default) · C (build a dashboard; define a metric; publish an API endpoint; set an alert) · T (dashboard spec; API contract template) · Ch (dashboard DoD; API DoD; accessibility check).
- *Outcome:* the debt team and the DMBB workflow consume live debt data.
- *Reuses:* Blueprint (Debt dashboard, Taxpayer-360, API gateway).

**D10. Security, classification & data protection**
- *Scope:* Restricted-by-default; classification & access via Keycloak RBAC; the DPO/DPIA gate; using anonymised data in dev; MITA policy (AI-10/SEC-02); audit logging; secrets handling.
- *Artifacts:* P (classification cascades; least privilege; DPIA gates real data) · C (set RBAC for a dashboard/role; classify a dataset; handle secrets) · T (access-control matrix; classification register) · Ch (security gate before prod data).
- *Outcome:* debt data is access-controlled, classified and DPIA-cleared.
- *Reuses:* DQF (§7 DPO gate); Blueprint (classification).

### BAND 4 — RUN (operate and sustain)

**D11. Observability & operations**
- *Scope:* monitoring (Prometheus/Grafana); freshness SLAs (debt <5 min); alerting; the ops runbook (what to do when ingestion/build/dashboard fails); triage & on-call; capacity/cost; by-partition profiling off-peak.
- *Artifacts:* P (you build it, you run it; evidence not assertion) · C (read the dashboards; respond to a freshness/ingestion alert; run the daily health check) · T (ops runbook template; on-call rota) · Ch (operational-readiness checklist).
- *Outcome:* the team can detect and resolve a debt-platform incident.
- *Reuses:* DQF (incident process); Blueprint (monitoring, tiers).

**D12. Production readiness & go-live**
- *Scope:* the **Production-Readiness Checklist** (deploy tested, monitoring+alerts live, RBAC set, DQ gates green, ops runbook written, rollback proven, debt-team UAT signed); cutover; hypercare; "what 'in production' means."
- *Artifacts:* P (definition of production) · C (run a go-live; conduct UAT with the debt team) · T (UAT script; cutover plan; hypercare log) · **Ch — the Production-Readiness Checklist (the centrepiece)**.
- *Outcome:* Debt Management goes live with sign-off and a safety net.

**D13. Governance, evidence & reporting**
- *Scope:* reporting to the DGC; the monthly scorecard & KPIs; decision/issue logs; change control; audit evidence (manifests, test history, sign-offs).
- *Artifacts:* P (evidence is the governance currency) · C (produce the monthly scorecard; log a decision; raise a change) · T (scorecard; decision log; change request) · Ch (reporting cadence checklist).
- *Outcome:* delivery is visible and auditable to the DGC/Commissioner.
- *Reuses:* DQF (§7 scorecard/KPIs); Workshop (KPIs).

### CROSS-CUTTING

**X1. Capability building (shadow → pair → lead)**
- *Scope:* the learning path across D1–D13; the pairing protocol; per-skill "graduation" criteria; how contractors transfer knowledge; an individual skills matrix.
- *Artifacts:* P (build capability, not dependency) · C (run a shadow-pair-lead cycle) · T (skills matrix; pairing log) · Ch (graduation criteria per skill).
- *Outcome:* the team progressively owns each dimension.
- *Reuses:* Empowerment Case / R2; Workshop.

**X2. The Debt Management vertical slice (the worked spine)**
- *Scope:* the one end-to-end example threaded through every cookbook — sources (ARS Accounting, Income Tax Core, VAT; payments/assessments/taxpayer) → Bronze (Hot, 60 s) → Silver (payments, assessments, taxpayer, compliance_status) → Gold (`mart_debt__aged_balances`, `mart_debt__collection_performance`, Taxpayer-360, KPI) → Superset Debt Dashboard + API + alerts → production.
- *Artifacts:* a single **worked-example narrative** that each dimension's cookbook references, so the team builds *this* while learning.
- *Outcome:* the guidance and the first production deliverable are the same effort.
- *Reuses:* Blueprint (debt marts, freshness, Taxpayer-360); DM Requirements; DMBB.

**X3. Comprehensive estate coverage (the breadth thread)**
- *Scope:* bring the *whole* estate into the platform over time — all nine databases / 5,170+ tables — not just the debt sources: prioritised tiering (Hot/Warm/Cold/Archive), the catalogue's three-layer enrichment (45/25/20/10), the mystery-table A/B/C triage at scale, and a coverage backlog. Each consumer slice (Debt, then SAS, then the rest) pulls from this growing, governed base rather than re-ingesting its own copy.
- *Artifacts:* P (one comprehensive platform; ingest once, serve many; prioritised coverage) · C (onboard the next source/domain at scale; expand the catalogue) · T (estate coverage backlog/tracker) · Ch (coverage milestone gate).
- *Outcome:* the platform progressively holds all MTCA data — tiered, described, quality-scored — ready for any consumer.
- *Reuses:* Catalogue plan; DQF (S1); PowerBuilder-source method; Blueprint (tiers, ingestion).

**X4. Onboarding a new consumer (the depth pattern, generalised)**
- *Scope:* the repeatable way a *new* consumer is served — capture its data needs, build/extend the Gold marts it requires, expose the dashboard/API/feed it consumes, set its RBAC, and sign off. Debt Management (low-code) is the first run of this pattern; the **SAS project** is the second (Gold-layer feed + risk-score write-back); future modules follow.
- *Artifacts:* P (consumers pull from Gold; no bespoke side-pipelines) · C (onboard a new consumer end-to-end) · T (consumer-needs spec; consumer onboarding checklist) · Ch (consumer go-live gate).
- *Outcome:* a documented, repeatable path so each new module/consumer is onboarded the same way, fast.
- *Reuses:* Blueprint (consumer integration, API gateway, SAS as Gold consumer); DQF.

---

## 4. Coverage matrix (nothing missed)

| Dimension | P | C | T | Ch | Debt milestone |
|---|:--:|:--:|:--:|:--:|---|
| D0 Architectural principles register | ✓ | ✓ | ✓ | ✓ | all |
| D1 Lifecycle & ways of working | ✓ | ✓ | ✓ | ✓ | all |
| D2 Environment & access | ✓ | ✓ | ✓ | ✓ | M0 |
| D3 Git & collaboration | ✓ | ✓ | ✓ | ✓ | all |
| D4 Source onboarding & ingestion | ✓ | ✓ | ✓ | ✓ | M1 |
| D5 dbt modelling | ✓ | ✓ | ✓ | ✓ | M2–M3 |
| D6 Data quality (DQF) | ✓ | ✓ | ✓ | ✓ | M2–M3 |
| D7 Catalogue & metadata | ✓ | ✓ | ✓ | ✓ | M1–M3 |
| D8 CI/CD & deployment | ✓ | ✓ | ✓ | ✓ | M2–M6 |
| D9 Dashboards & APIs | ✓ | ✓ | ✓ | ✓ | M4–M5 |
| D10 Security & data protection | ✓ | ✓ | ✓ | ✓ | M5–M6 |
| D11 Observability & operations | ✓ | ✓ | ✓ | ✓ | M6 |
| D12 Production readiness & go-live | ✓ | ✓ | ✓ | ✓ | M6 |
| D13 Governance & evidence | ✓ | ✓ | ✓ | ✓ | all |
| X1 Capability building | ✓ | ✓ | ✓ | ✓ | all |
| X2 Debt vertical slice | — | (spine) | ✓ | — | M0–M6 |
| X3 Comprehensive estate coverage (breadth) | ✓ | ✓ | ✓ | ✓ | ongoing |
| X4 Onboarding a new consumer (depth pattern) | ✓ | ✓ | ✓ | ✓ | Debt→SAS→… |

Milestones (Debt, the first slice): **M0** environment/access · **M1** debt sources in Bronze (reconciled, catalogued) · **M2** Silver + tests · **M3** debt Gold marts · **M4** Superset dashboard · **M5** API + alerts · **M6** production hardening + go-live. The breadth thread (X3) and the next consumer — the SAS project (X4) — run in parallel once the patterns are proven.

## 5. What already exists vs what is new

- **Reuse (already written, MTCA):** Data Quality Framework v0.1 (→ D6, D11, D13); BOP semantic enrichment + PowerBuilder-source method (→ D7); Capacity-Building Workshop (→ D1, X1); Blueprint (→ D0, D2, D5, D9, X2).
- **Port from the ARMS (Moldova) project — proven patterns to adapt, not reinvent:** the numbered principles register (→ D0); the Intermediate `int_` join-layer convention (→ D5); the verified-semantics gate (→ D7); the profile-before-DDL onboarding gate + reconciliation manifests (→ D4); DDL-to-catalogue + reference-data vocabularies (→ D7); the two-track dev method + command-block / cross-OS discipline (→ D2, D8, D11); the repo scaffold + naming conventions + pre-commit (→ D3, D5).
- **New to write:** the cookbooks (D0–D12), the templates and checklists per dimension, the Production-Readiness Checklist (D12), and the Debt worked-example narrative (X2).

## 6. Tone & format per audience

- **Cookbooks:** imperative, numbered, with exact commands, paths and a worked Debt example; "if it fails, do this" troubleshooting.
- **Cross-OS:** every command block is given for **Windows (PowerShell / WSL2) and macOS-Linux**; prefer OS-agnostic tooling (containers, `uv`, a task runner, VS Code) so the same steps work on any workstation.
- **Principles:** one page each, opinionated, rule-first.
- **Templates/Checklists:** copy-ready files the team fills in.

## 6.1 Delivery vehicle — most cookbooks ship as Cowork skills

The team works in **Claude Cowork**, so the *how-to* (Layer C) is best delivered as **Cowork Skills** — a skill is the cookbook that triggers and runs itself, carrying the scripts, conventions and guardrails. Principles, Templates and Checklists stay as documents; the cookbooks become an installable **"MTCA Data Platform" skill pack** (versioned in Git). Skills *guide* the work; the Data-Owner sign-offs and DoD checklists still *gate* it. Cross-checked against the proven ARMS skill set:

**A standing rule for every skill in the pack — write through to a commit.** Each skill's final step is to save its output into the versioned repository and commit it on the workstation (Desktop Commander / terminal — never an in-sandbox git, which the Cowork sandbox can't clean up), with a clear message and the cross-OS commands. A skill that produces an artifact but leaves it uncommitted has not finished. The `repo-scaffold` and `mtca-dev-workflow` skills own the shared git mechanics (clone/branch/commit/PR on Windows + macOS); the others call into that convention.

| Skill | Origin | Dimension | Automates |
|---|---|---|---|
| `mtca-architecture-principles` | port `arms-principles` | D0 | apply the principles register to a decision |
| `mtca-dev-workflow` | port `arms-dev-workflow` | D2/D8/D11 | build/run/test/dbt/deploy/verify — two-track, **cross-OS** command blocks; **commit-on-the-workstation git** |
| `repo-scaffold` | port | D3/D5 | lay out the repo with conventions + pre-commit; **the shared clone/branch/commit/PR mechanics every skill calls** |
| `onboard-source` | port `arms-source-onboarding` | D4 | profile → Bronze DDL → gated extractor → reconciliation manifests |
| `import-schema-to-catalogue` | port `dc-import-schema` | D7 | source DDL → catalogue + reference-data vocabularies + dbt `sources.yml` |
| `legacy-module-to-openmetadata` | **NEW (Malta)** | D7 | PowerBuilder source → app→table lineage + draft descriptions (pilot) |
| `verify-catalogue-semantics` | port `arms-catalogue-semantics` | D7 | draft → **VERIFIED** descriptions (authoritative source + data check) |
| `build-dbt-model` | new | D5 | scaffold `stg_/int_/mart_` + tests — **incl. the `int_` join / golden-record** |
| `add-dq-checks` | from DQF | D6 | dbt + OpenMetadata tests for the six dimensions |
| `build-superset-dashboard` / `expose-api` | new | D9 | the consumer surfaces (Debt first, SAS next) |
| `production-readiness-check` | **NEW (Malta)** | D12 | run the go-live checklist |
| `onboard-consumer` | new | X4 | the repeatable "serve a new consumer" path |

## 7. Decisions for the sequencing stage (next, not now)

1. Packaging: **direction set** — cookbooks as a Cowork **skill pack**; Principles/Templates/Checklists as docs (repo `/docs`). To confirm: marketplace/distribution to the team.
2. Order of build (proposal: D1–D3 foundations first, then follow the Debt milestones M1→M6, pulling each dimension in as the slice reaches it).
3. Depth per dimension for v1 (full vs "minimum to ship Debt").
4. Who authors/pairs on each (STX vs contractor vs team).
5. Where it lives (repo `/docs`, the catalogue, a shared drive).

---

*This is the content scope. Review/adjust the dimensions and artifact bundles; sequencing and packaging follow.*
