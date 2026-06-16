# MTCA Data Platform — Delivery Kit (Knowledge Product)

**Audience:** the MTCA IT Department Data Management team.
**Purpose:** structured guidance and reusable tooling to take the MTCA Data Platform from
build to **production**, starting with the no-code / low-code Debt Management vertical and
scaling to comprehensive, all-data coverage (SAS being a second consumer of the platform, not
the platform itself).

This repository is a **knowledge product**: a self-contained, version-controlled deliverable
intended to be shipped to MTCA. It is kept separate from the day-to-day working folder so that
what we hand over has a clean structure and a clear history.

Status: **v0.1 — in development.** Content design approved; skill pack in build.

---

## What's in here

```
docs/        Written guidance (the delivery-guidance content design and, later, the cookbooks)
frameworks/  Standalone framework deliverables the guidance builds on (e.g. the DQF)
skills/      Cowork skill sources — one folder per skill (SKILL.md + scripts + references)
dist/        Packaged, installable artefacts (.skill files ready to load into Cowork)
```

### docs/
- `delivery-guidance_content-design_v0.1.md` — the agreed content design for the delivery
  guidance: the competency map (Bands 1–4 + cross-cutting), the artefact taxonomy, the
  reuse-vs-new analysis (including the ARMS ports), the coverage matrix, and the Cowork
  skill-pack plan. This is the blueprint the rest of the kit is built against.

### skills/
- `legacy-module-to-openmetadata/` — **pilot skill (built & validated).** From a legacy
  PowerBuilder module's source (`.pbl`), with no database, it recovers the tables/columns the
  module uses and produces an OpenMetadata-ready semantic enrichment (YAML + review markdown).
  Proven on the BOP Registration module (25 tables / 141 columns). This is the template for the
  rest of the pack.

### frameworks/
- `data-quality-framework/` — **MTCA Data Quality Framework v0.1** (`.docx` + `.md` + the
  architecture figure). The two-tier DQF — dbt build-time contracts/gates plus OpenMetadata
  fitness-for-use monitoring, the six dimensions and their targets, the control catalogue, and
  the §5 "why no SAS for DQ" implementation case — that the guidance's data-quality dimension
  (D6) and operations/governance dimensions (D11, D13) build on.

### dist/
- `legacy-module-to-openmetadata.skill` — the packaged pilot skill, ready to install in Claude
  Desktop (Cowork): open it and choose **Save skill**.

---

## How the kit is meant to be used

The delivery guidance ships mainly as **Cowork skills** plus the written cookbooks in `docs/`.
Each skill packages a deterministic script (the repeatable, error-prone mechanics) behind a
SKILL.md that carries the judgement and the guardrails — so a team that is new to structured,
production-grade delivery gets a reliable harness rather than a blank page. The skills are pure
Python and cross-platform (Windows + macOS), so they run on the team's own machines.

**Version control is a built-in step, not an afterthought.** Every skill's final action is to
write its output into this repository and commit it. Because the Cowork sandbox cannot delete
files on the workstation (an in-sandbox `git` would strand lock files), git runs **on the machine**
— via Desktop Commander or a terminal — with the same workflow on Windows and macOS. A skill that
produces an artefact but leaves it uncommitted hasn't finished.

## Planned contents (per the content design)

A 12-skill pack mapped to the competency dimensions D0–D13 and the cross-cutting tracks, built in
sequence against the Debt Management milestones. See `docs/delivery-guidance_content-design_v0.1.md`
§6.1 for the full skill table and §7 for the sequencing decisions.

## Related MTCA deliverables (not yet folded into this kit)

These were produced alongside the kit and live elsewhere in the working folder; they can be
brought in as the kit's scope is confirmed:
- **BOP Registration semantics & source-catalogue report**
  (`05-data-platform/04-data-catalogue/_module-semantics/`) — the experiment that produced the
  pilot skill; the finished worked example is also bundled inside the skill's `references/`.

---

## Versioning

Semantic-ish: `v0.x` while in development, `v1.0` at first MTCA hand-over. Tag releases; keep
`docs/` versions in filenames (`_v0.1`) so a shipped copy is unambiguous.
