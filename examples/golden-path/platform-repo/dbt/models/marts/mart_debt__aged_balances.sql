-- mart_debt__aged_balances  (mart: consumer-facing; composes from int_, does not re-join raw sources)
with base as (
    select * from {{ ref('int_taxpayer__master') }}
)
select
    taxpayer_id,
    taxpayer_name,
    balance,
    assessment_total
from base
