# Production-readiness criteria — in full

Each criterion, what "satisfied" means, and what counts as evidence. Blockers gate go-live; warnings
are advisory.

## Deploy
- **DEPLOY-1 — CI present & green (auto, blocker).** A CI pipeline runs `dbt test` (and the hygiene
  hooks) on every change. Evidence: a workflow file under `.github/workflows/` (or `.gitlab-ci.yml`).
  Necessary; the attestation that the *latest* run is green is part of DEPLOY-2.
- **DEPLOY-2 — Deployed to test & promoted (attest, blocker).** The release went through dev → test →
  prod via the pipeline, not by hand. Evidence: the promotion record / release notes.

## Monitoring
- **MON-1 — Monitoring live (attest, blocker).** Prometheus/Grafana dashboards show ingestion, build,
  and freshness health for this release. Evidence: the dashboard URL + a screenshot/owner.
- **MON-2 — Alerts configured (auto, blocker).** Threshold alerts exist (freshness, ingestion failure,
  the ageing-shift watch). Evidence: a dashboard manifest carrying `alerts`. Wire them in the
  monitoring stack too (the attestation in MON-1 covers "live").

## Security & data protection
- **SEC-1 / SEC-1b — RBAC on dashboards / APIs (auto, blocker).** Consumption surfaces are
  Restricted-by-default. Evidence: `rbac_roles` on the dashboard manifest, `x-rbac-roles` on the
  OpenAPI contract; enforce them in Superset / the gateway.
- **SEC-2 — DPIA / DPO clearance (attest, blocker).** Real (Restricted) data may not be processed
  until the DPO's DPIA clears it (GDPR Art. 35; MITA AI-10/SEC-02). Evidence: the DPIA reference and
  the DPO sign-off. **Note for MTCA:** there is no anonymisation capability yet, so real data is used in
  the **test** environment too — the DPIA must cover test as well as production, with least-privilege
  access and audit logging as compensating controls, and the arrangement recorded as a constraint with
  anonymisation as the remediation. Confirm the DPO has approved test-environment use before any real
  data is touched.
- **SEC-3 — Secrets handled (auto, blocker).** No credentials in the repo. Evidence: `.env` and
  `profiles.yml` gitignored; a secret-scan (gitleaks) in CI.

## Data quality
- **DQ-1 — DQ gates green (auto + attest, blocker).** The marts carry the six-dimension gates and the
  latest run is green. Evidence: `quality/thresholds/*` present (auto) + the green `dbt test` /
  reconciler badge (attest).
- **DQ-2 — Catalogue VERIFIED (attest, blocker).** Every column that drives a mart or the handover is
  VERIFIED (not DRAFT/TO-CONFIRM). Evidence: the `verify-catalogue-semantics --gate` pass for the
  module(s). A wrong description becomes a wrong number — this is non-negotiable for go-live.

## Operations
- **OPS-1 — Ops runbook (auto, blocker).** A runbook says what to do when ingestion/build/dashboard
  fails. Evidence: `ops/runbooks/*.md`.
- **OPS-2 — Freshness SLAs per tier (attest, warn).** The tier SLAs (Hot 5 min … Archive 7 d) are
  defined and agreed. Advisory at go-live; should be in place.

## Rollback
- **ROLL-1 — Rollback documented AND proven (auto + attest, blocker).** Evidence: the runbook's
  rollback section (auto) **and** an attestation that it was rehearsed against this release. A
  rollback nobody has run is not a rollback.

## UAT & governance
- **UAT-1 — Consumer UAT signed (attest, blocker).** The debt team ran UAT against the dashboard/API
  and signed off. Evidence: the UAT script result + sign-off.
- **GOV-1 — Go-live sign-off (attest, blocker).** The DGC / data owner recorded the go-live decision.
  Evidence: the minute / decision-log entry.

## How this relates to the other gates

This is the **final** gate; it composes the earlier ones rather than re-implementing them:
- the **DQF handover gate** (DQC-S5-02) → DQ-1/DQ-2 here;
- the **catalogue verification gate** (`verify-catalogue-semantics`) → DQ-2;
- the **deploy** and **observability** dimensions → DEPLOY-* / MON-* / OPS-*;
- the **security/DPIA** gate → SEC-2.

So a green production-readiness report means the slice passed every gate along the path, with evidence
— which is exactly what governance needs to authorise go-live.

## Status semantics

- `pass` — satisfied, with evidence.
- `na` — genuinely not applicable to this release (use sparingly, with a reason in `evidence`).
- `fail` / `pending` — not satisfied; a blocker in this state fails the gate. `pending` is treated as a
  fail on purpose: an unanswered item is not readiness.
