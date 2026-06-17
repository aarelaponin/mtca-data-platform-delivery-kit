-- int_taxpayer__master  (intermediate: explicit joins / golden record; join keys are contract-tested)
with stg_ird__taxpayer as (
    select * from {{ ref('stg_ird__taxpayer') }}
),
stg_vat__registration as (
    select * from {{ ref('stg_vat__registration') }}
)
select
    stg_ird__taxpayer.taxpayer_id,
    stg_ird__taxpayer.taxpayer_name,
    stg_ird__taxpayer.segment,
    stg_ird__taxpayer.balance,
    stg_ird__taxpayer.assessment_total,
    stg_vat__registration.vat_no,
    stg_vat__registration.vat_declared,
    stg_vat__registration.vat_paid
from stg_ird__taxpayer
left join stg_vat__registration on stg_ird__taxpayer.taxpayer_id = stg_vat__registration.taxpayer_id
