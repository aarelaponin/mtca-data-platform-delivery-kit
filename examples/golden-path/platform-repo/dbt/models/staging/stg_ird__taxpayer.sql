-- stg_ird__taxpayer  (staging: 1:1 clean of one source table, no joins)
with source as (
    select * from {{ source('bronze', 'ird__taxpayer') }}
)
select
    cast(`tax_serial` as Int64) as `taxpayer_id`,
    `tax_name` as `taxpayer_name`,
    `tax_segment` as `segment`,
    cast(`tax_balance` as Decimal(38,2)) as `balance`,
    cast(`tax_assessment` as Decimal(38,2)) as `assessment_total`
from source
