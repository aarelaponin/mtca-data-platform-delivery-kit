#!/usr/bin/env bash
# Golden path: run the whole skill chain on the bundled fixtures to build a worked platform repo.
# Run from examples/golden-path/.  Pure Python; no DB needed (generation is offline / Track A).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SK="$HERE/../../skills"
IN="$HERE/inputs"
REPO="$HERE/platform-repo"
PB="${PB_MODULE:-$HERE/../../../../10-workstreams/pb-migration/BOP Registration/Bopindex/bopindex.pbl}"
INV="${PB_INVENTORY:-$HERE/../../../../80-reference/legacy-db/income-dw-analysis/phase1_source_tables.yaml}"

py() { python3 "$@"; }

echo "== 1. repo-scaffold =="
py "$SK/repo-scaffold/scripts/scaffold_repo.py" --path "$REPO" --name mtca-data-platform >/dev/null

echo "== 2. onboard-source: Bronze DDL (Decimal(38,s) money-widening) =="
py "$SK/onboard-source/scripts/gen_bronze_ddl.py" --schema "$IN/schema_ird.json" --out "$REPO/ingestion/ird/" >/dev/null

echo "== 3. import-schema-to-catalogue: dbt sources + technical metadata + reference vocabulary =="
py "$SK/import-schema-to-catalogue/scripts/import_schema.py" --schema "$IN/schema_ird.json" --repo "$REPO" >/dev/null
py "$SK/import-schema-to-catalogue/scripts/import_schema.py" --vocab --data "$IN/taxpayer_status.csv" \
   --code-col code --label-col label --name taxpayer_status --repo "$REPO" >/dev/null

echo "== 4. legacy-module-to-openmetadata: recover BOP semantics (DRAFT) =="
if [ -f "$PB" ]; then
  py "$SK/legacy-module-to-openmetadata/scripts/extract_pb_tables.py" \
     --source "$PB" --inventory "$INV" --out "$REPO/catalogue/module-semantics/" --module-name BOP_Registration >/dev/null
else
  echo "   (BOP .pbl not found at \$PB — skipping; set PB_MODULE to enable)"
fi

echo "== 5. build-dbt-model: stg_ -> int_ (golden record, join contract) -> mart_ =="
for spec in model_stg_ird_taxpayer model_stg_vat_registration model_int_taxpayer_master model_mart_debt_aged_balances; do
  py "$SK/build-dbt-model/scripts/gen_dbt_model.py" --spec "$IN/$spec.yml" --out "$REPO/dbt/models" >/dev/null
done

echo "== 6. add-dq-checks: six-dimension DQ on the mart =="
py "$SK/add-dq-checks/scripts/gen_dq_checks.py" --spec "$IN/dq_mart_debt.yml" --repo "$REPO" >/dev/null

echo "== 7. build-superset-dashboard + expose-api: consumption surfaces =="
py "$SK/build-superset-dashboard/scripts/gen_superset.py" --spec "$IN/dashboard_debt.yml" --repo "$REPO" >/dev/null
py "$SK/expose-api/scripts/gen_api.py" --spec "$IN/api_debt.yml" --repo "$REPO" >/dev/null

echo "== 8. onboard-consumer: SAS risk (gap analysis + plan) =="
py "$SK/onboard-consumer/scripts/gen_consumer_plan.py" --spec "$IN/consumer_sas.yml" --inventory "$IN/mart_inventory.yml" --repo "$REPO" >/dev/null

echo "== 9. production-readiness-check: add CI + runbook, then gate =="
mkdir -p "$REPO/.github/workflows" "$REPO/ops/runbooks"
printf 'name: ci\njobs:\n  test:\n    steps: [dbt test]\n' > "$REPO/.github/workflows/ci.yml"
printf '# Deploy runbook\n## Rollback\nRevert the release tag and redeploy the previous build; verify DQ gates green.\n' > "$REPO/ops/runbooks/deploy.md"
py "$SK/production-readiness-check/scripts/prodcheck.py" --emit-manifest -o "$HERE/readiness.yml" >/dev/null
# fill attestations pass (a demo "ready" release), point at the repo
python3 - "$HERE/readiness.yml" "$REPO" <<'PY'
import sys,yaml
m=yaml.safe_load(open(sys.argv[1])); m["repo"]=sys.argv[2]; m["release"]="debt-v1.0-golden-path"
for v in m["attestations"].values(): v.update(status="pass",evidence="golden-path demo",signed_by="example",date="2026-06-17")
yaml.safe_dump(m,open(sys.argv[1],"w"),sort_keys=False)
PY
py "$SK/production-readiness-check/scripts/prodcheck.py" --check --manifest "$HERE/readiness.yml" --report "$REPO/ops/readiness_report.md" || true

echo
echo "== DONE — worked platform repo at: platform-repo/ =="
