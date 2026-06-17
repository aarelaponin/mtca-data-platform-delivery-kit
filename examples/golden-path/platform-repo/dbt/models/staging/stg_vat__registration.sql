-- stg_vat__registration  (staging: 1:1 clean of one source table, no joins)
with source as (
    select * from {{ source('bronze', 'vat__registration') }}
)
select
    cast(`vat_taxref` as Int64) as `taxpayer_id`,
    `vat_no` as `vat_no`,
    cast(`vat_declared` as Decimal(38,2)) as `vat_declared`,
    cast(`vat_paid` as Decimal(38,2)) as `vat_paid`
from source
