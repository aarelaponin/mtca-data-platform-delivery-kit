# Production-Readiness Report — debt-v1.0-golden-path
_Checked 2026-06-17 · 15/15 items satisfied · **GATE: PASS**_

| ID | Category | Item | Kind | Sev | Status | Evidence |
|---|---|---|---|---|---|---|
| DEPLOY-1 | Deploy | CI pipeline present and green | auto | blocker | ✅ pass | auto: repo inspection |
| DEPLOY-2 | Deploy | Deployed to test and promoted via the pipeline | attest | blocker | ✅ pass | golden-path demo (by example) |
| MON-1 | Monitoring | Monitoring dashboards live (Prometheus/Grafana) | attest | blocker | ✅ pass | golden-path demo (by example) |
| MON-2 | Monitoring | Threshold alerts configured (freshness/ingestion/dashboard) | auto | blocker | ✅ pass | auto: repo inspection |
| SEC-1 | Security | RBAC set on dashboards | auto | blocker | ✅ pass | auto: repo inspection |
| SEC-1b | Security | RBAC set on APIs | auto | blocker | ✅ pass | auto: repo inspection |
| SEC-2 | Security | DPIA / DPO clearance for real (Restricted) data | attest | blocker | ✅ pass | golden-path demo (by example) |
| SEC-3 | Security | Secrets handled (no credentials in the repo; .env/profiles gitignored) | auto | blocker | ✅ pass | auto: repo inspection |
| DQ-1 | DataQuality | DQ gates defined and green on the marts | auto | blocker | ✅ pass | auto: repo inspection |
| DQ-2 | DataQuality | Catalogue descriptions VERIFIED for every handover/mart column | attest | blocker | ✅ pass | golden-path demo (by example) |
| OPS-1 | Operations | Ops runbook written (what to do when ingestion/build/dashboard fails) | auto | blocker | ✅ pass | auto: repo inspection |
| OPS-2 | Operations | Freshness SLAs defined per tier | attest | warn | ✅ pass | golden-path demo (by example) |
| ROLL-1 | Rollback | Rollback documented and PROVEN (rehearsed, not just written) | auto | blocker | ✅ pass | auto: repo inspection |
| UAT-1 | UAT | Consumer (debt team) UAT signed off | attest | blocker | ✅ pass | golden-path demo (by example) |
| GOV-1 | Governance | Go-live sign-off recorded (DGC/owner) | attest | blocker | ✅ pass | golden-path demo (by example) |
