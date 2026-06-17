{{ config(tags=['dq:completeness'], meta={'dq_dimension':'completeness','control':'DQC-S3-02'}) }}
-- Completeness: zero-row / row-budget gate — fails if the table has fewer than 1 rows.
select count(*) as n
from {{ ref('mart_debt__aged_balances') }}
having count(*) < 1
