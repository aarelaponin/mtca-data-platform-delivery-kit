{{ config(tags=['dq:timeliness'], meta={'dq_dimension':'timeliness','control':'DQC-S4-04','tier':'hot'}) }}
-- Timeliness: fails if the freshest row is older than the hot SLA (5 min).
select max(`_extracted_at`) as freshest
from {{ ref('mart_debt__aged_balances') }}
having now() - max(`_extracted_at`) > interval 5 minute
