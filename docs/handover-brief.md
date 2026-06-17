# MTCA Data Platform Delivery Kit — Hand-over Brief

**For:** the MTCA IT Department Data Management team (and the DGC).
**What this is:** a structured way to take the Data Platform to production — guidance plus 13
installable Cowork skills — so the team can deliver a first production slice (no-code/low-code Debt
Management) and then repeat the same path for every source, mart and consumer.

## Why it exists

The Data Platform is likely the team's first system to reach production. Rather than a methodology to
read and remember, the kit **carries the structure for you**: each task is a skill that runs a
deterministic script behind a short guide of judgement and guardrails, ending by committing its output
to version control. You run it, review it, and move on — the discipline is built into the tools.

## What you get

- **One installable plugin** — `mtca-data-platform.plugin` (in `dist/`). Install it once in Claude
  Desktop (Cowork) and all 13 skills are available; they trigger from plain requests like "onboard the
  ARS source", "build the debt mart", "verify these descriptions", "are we ready for production".
- **The Data Quality Framework** (`frameworks/`) the quality work builds on.
- **A worked end-to-end example** (`examples/golden-path/`) — the whole chain run on real data, so you
  can see what a finished Debt slice looks like before building your own.

## The delivery loop (what the skills do, in order)

1. **Decide & set up** — `mtca-architecture-principles`, `mtca-dev-workflow`, `repo-scaffold`.
2. **Build** — `onboard-source` → `import-schema-to-catalogue` → `build-dbt-model` → `add-dq-checks`.
3. **Catalogue** — `legacy-module-to-openmetadata` → `verify-catalogue-semantics`.
4. **Ship** — `build-superset-dashboard`, `expose-api`.
5. **Go live & grow** — `production-readiness-check`, then `onboard-consumer` for the next consumer
   (Debt is first; the SAS risk project is second).

Generate **offline** on your laptop; run the live `dbt build` / loads / imports on the platform stack;
**commit on your workstation**. The skills work on both Windows and macOS.

## How we work (the rules the kit enforces)

- **Decide by citation** — settled architecture questions (e.g. open-source vs a held licence) are a
  one-line reference, not a fresh debate.
- **Generate, never hand-edit** — fix the spec and regenerate; hand edits are lost on the next run.
- **One source of truth** — one taxpayer record, one metric definition; consumers pull from Gold, never
  a private copy.
- **Verify before publish** — a description is DRAFT until confirmed against the form/spec/code or the
  data itself; only verified meaning drives a mart or the DcP3 hand-over.
- **Reconcile every transfer; evidence, not assertion** — a load isn't done without a matching count; a
  release isn't ready without a green readiness report.
- **Version-controlled by default** — everything-as-code, committed and reviewed.

## What's automated vs what the team owns

The skills generate the artefacts and run the gates. **People still** run the live builds and loads,
stand up CI and monitoring, perform UAT, obtain the DPIA/DPO clearance for real data, and record the
go-live sign-off. The `production-readiness-check` skill lists exactly these as the go-live checklist —
so nothing is forgotten, and "in production" means the checklist passed.

## Getting started (first week)

1. Install the plugin; run `mtca-dev-workflow`'s toolchain check on each workstation.
2. Scaffold the platform repo (`repo-scaffold`); make the first commit.
3. Walk through `examples/golden-path/` together to see the whole loop.
4. Pick the first Debt source and run `onboard-source` → … → the first mart, paired with the STX.
5. Work toward `production-readiness-check` PASS for the Debt slice.

## Where things are

- Skills (source) — `skills/`; installable bundle — `dist/mtca-data-platform.plugin`.
- Install guide + delivery-loop map — `docs/skill-pack-index.md`.
- Content design (the full competency map) — `docs/delivery-guidance_content-design_v0.1.md`.
- DQF — `frameworks/data-quality-framework/`; worked example — `examples/golden-path/`.

_Version 0.1 — the pack is built, validated and packaged; the live build-out is the team's next step._
