# Consumer onboarding plan — sas-risk
_SAS VIYA risk scoring — the platform's second consumer._

Generated 2026-06-17 · surface **feed** · served **4** / missing **0** need(s).

## Coverage

| Need | Status | Served by |
|---|---|---|
| `taxpayer_id` | ✅ served | `mart_debt__aged_balances`, `int_taxpayer__master` |
| `taxpayer_name` | ✅ served | `mart_debt__aged_balances`, `int_taxpayer__master` |
| `segment` | ✅ served | `int_taxpayer__master` |
| `vat_paid` | ✅ served | `int_taxpayer__master` |

## Plan

1. **Capture needs** — sas-risk: 4 required field(s)/metric(s) across 2 entity group(s); surface = **feed**; freshness tier = **warm**.
2. **Gaps** — none; every need is already served by an existing Gold mart (reuse, don't rebuild).
3. **Expose** — Gold-layer **feed**: grant the consumer read on the serving mart(s) (no copy).
4. **Write-back** — model `mart_risk__scores` (taxpayer_id, risk_score, risk_band) as a Gold mart (**build-dbt-model** + **add-dq-checks** + **verify-catalogue-semantics**); the consumer writes its outputs here, and downstream reads them like any other Gold mart.
5. **RBAC** — grant `sas_analyst`, `risk_modeller`; the surface inherits the data's classification (Restricted-by-default).
6. **Quality & catalogue gates** — DQ green on every consumed/written mart; catalogue VERIFIED for its columns.
7. **Production-readiness** — run **production-readiness-check** for the consumer release; sign-off gates go-live.

## Definition of Done (consumer gate)

| ID | Item | Status |
|---|---|---|
| needs-captured | Consumer data needs captured (entities, fields, metrics, surface, freshness) | ✅ pass |
| gaps-resolved | No gaps — all needs served by existing Gold marts | ✅ pass |
| surface-exposed | Consumption surface exposed (feed) | ⬜ pending |
| writeback-wired | Write-back mart(s) modelled, DQ'd and verified | ⬜ pending |
| rbac-set | RBAC roles granted; classification inherited | ⬜ pending |
| dq-green | DQ gates green on every consumed/written mart | ⬜ pending |
| catalogue-verified | Catalogue VERIFIED for the consumed/written columns | ⬜ pending |
| readiness | production-readiness-check PASS for the consumer release | ⬜ pending |
| sign-off | Consumer sign-off recorded | ⬜ pending |
