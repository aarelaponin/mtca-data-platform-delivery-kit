---
name: production-readiness-check
description: >-
  Run the MTCA Production-Readiness Checklist as an evidence-driven go-live gate — auto-check what the
  repo proves (CI, ops runbook, rollback, DQ gates, dashboard/API RBAC, alerts, secrets) and take
  signed attestations for the rest (UAT, DPIA/DPO clearance, monitoring live, sign-off), then return a
  hard pass/fail. Use this WHENEVER the question is "are we ready for production": "run the go-live
  checklist", "is this ready to ship", "production readiness", "can we cut over", "pre-launch check",
  "what's blocking go-live", "sign off the release". Trigger at the end of a delivery slice before
  cutover, and any time someone claims something is "in production" — this turns that claim into a
  checklist that either passes or names exactly what's missing. The centrepiece of the Run band.
  Cross-platform, pure Python.
---

# Production-readiness check (the go-live gate)

"In production" is a checklist that passes, not an opinion. This skill runs the canonical MTCA
go-live checklist for a release and returns a **gate**: every blocker must pass before cutover, or it
names exactly what's outstanding. It splits the work honestly:

- **Auto-checks** — what the repository can prove: CI present, ops runbook written, rollback
  documented, DQ thresholds defined, dashboard RBAC, API RBAC, alerts configured, secrets gitignored.
  Computed by inspecting the repo; no attestation can fake them.
- **Attestations** — what a person must sign: deployed-and-promoted, monitoring live, DPIA/DPO
  clearance for Restricted data, catalogue descriptions VERIFIED, consumer (debt-team) UAT, go-live
  sign-off. Recorded with evidence, who signed, and when.

## Workflow

### 1 — Scaffold the attestation manifest

```bash
python3 scripts/prodcheck.py --emit-manifest -o readiness.yml
```
Lists every attestation item as `pending`, for the team to fill (`status: pass|fail|na`, plus
`evidence`, `signed_by`, `date`). Set `repo:` to the platform repo root and `release:` to the release.

### 2 — Run the gate

```bash
python3 scripts/prodcheck.py --check --manifest readiness.yml --report readiness_report.md
```
It auto-checks the repo, merges the attestations, writes a readiness report (the full checklist with
✅/❌/⬜ and evidence per item), prints the gate result, and **exits non-zero if any blocker is
outstanding**. Wire that exit code into the cutover step so go-live can't proceed on an amber board.

### 3 — Close the gaps, re-run, sign off

For each ❌: do the work (add CI, write the runbook, prove the rollback, verify the catalogue, get the
UAT sign-off…) and re-run until the gate is green. Keep the green report as the release evidence.

### 4 — Commit the evidence

Commit on the workstation (`repo-scaffold` git workflow): `release: debt-v1.0 production-readiness PASS`
with the report attached.

## What's on the checklist (and how each is checked)

| ID | Item | How |
|---|---|---|
| DEPLOY-1 | CI pipeline present and green | auto (`.github/workflows/*` or `.gitlab-ci.yml`) |
| DEPLOY-2 | Deployed to test and promoted via the pipeline | attest |
| MON-1 | Monitoring dashboards live (Prometheus/Grafana) | attest |
| MON-2 | Threshold alerts configured | auto (a dashboard manifest with `alerts`) |
| SEC-1 / SEC-1b | RBAC on dashboards / APIs | auto (`rbac_roles` / `x-rbac-roles`) |
| SEC-2 | DPIA / DPO clearance for Restricted data | attest |
| SEC-3 | Secrets handled (no creds in repo) | auto (`.env`/`profiles.yml` gitignored) |
| DQ-1 | DQ gates defined & green on the marts | auto (`quality/thresholds/*`) + attest green |
| DQ-2 | Catalogue descriptions VERIFIED for handover/mart columns | attest (`verify-catalogue-semantics` gate) |
| OPS-1 | Ops runbook written | auto (`ops/runbooks/*.md`) |
| OPS-2 | Freshness SLAs defined per tier | attest (warn) |
| ROLL-1 | Rollback documented **and proven** | auto (runbook mentions rollback) + attest rehearsed |
| UAT-1 | Consumer (debt team) UAT signed off | attest |
| GOV-1 | Go-live sign-off recorded | attest |

The auto-checks are necessary, not sufficient: e.g. ROLL-1 auto-confirms a rollback is *documented*,
but the attestation is what says it was *rehearsed*. DQ-1 confirms thresholds exist; the attestation
says the latest run was green. Both must hold.

## Rules baked in

- **A blocker passes only on `pass`** (or an explicit `na` for genuinely not-applicable attest items).
  `pending` is a fail — silence is not readiness.
- **Auto-checks can't be attested away.** If the repo doesn't prove it, it's not done — write the CI,
  the runbook, the RBAC.
- **Rollback must be proven, not just written.** A rollback nobody has rehearsed is a hope, not a plan.
- **The report is the evidence.** Keep the green report with the release; it's what governance reads.

## Scripts & references

- `scripts/prodcheck.py` — `--emit-manifest` and `--check` (report + gate exit code).
- `references/readiness-criteria.md` — each criterion in full, what counts as evidence, and how this
  gate relates to the DQF handover gate and the deploy/observability dimensions.
