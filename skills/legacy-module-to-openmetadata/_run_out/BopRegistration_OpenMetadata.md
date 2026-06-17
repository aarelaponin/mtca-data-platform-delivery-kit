# BopRegistration — OpenMetadata Semantic Enrichment (DRAFT scaffold)

_Generated 2026-06-17 · Static analysis of bopindex.pbl (DataWindow + embedded SQL)._

> DRAFT SCAFFOLD — table/business-column descriptions are TODO; complete them from naming + domain, then VERIFY against an authoritative source before publishing (catalogue control). Authoritative data types come from the catalogue connector; 'inferredType' is a hint only.

**Tables used (13):** `accountperiod`, `bop`, `bopyearmember`, `coincentive`, `contact`, `country`, `fss_errors`, `partner`, `street`, `taxpayer`, `taxpayerlock`, `uniquekey`, `whitefile`

**Unmapped column prefixes (assign to a table):** `adm_*`, `bym_*`, `cat_*`, `cdn_*`, `cin_*`, `em_*`, `fou_*`, `fsse_*`, `inc_*`, `ird_*`, `loc_*`, `not_*`, `note_*`, `rea_*`, `ret_*`, `rol_*`, `sbc_*`, `tax_*`, `wfl_*`, `yea_*`


## `accountperiod`

| Column | Inferred type | Description |
|---|---|---|
| `acc_date` | datetime | (to confirm with the Data Owner) |
| `acc_period` | varchar | (to confirm with the Data Owner) |
| `acc_permit` | char | (to confirm with the Data Owner) |
| `acc_serial` | integer | Surrogate primary key (system-generated serial). |
| `acc_taxref` | varchar | Taxpayer reference (foreign key to the taxpayer table). |
| `acc_timestamp` | datetime | Row last-modified timestamp (audit). |
| `acc_userid` | varchar | User who last modified the row (audit). |
| `acc_year` | integer | Year. |
| `acc_yrfrom` | varchar | Effective from (year). |
| `acc_yrto` | varchar | Effective to (year). |

## `bop`

| Column | Inferred type | Description |
|---|---|---|
| `bop_activity` | varchar | (to confirm with the Data Owner) |
| `bop_assoctaxref` | varchar | (to confirm with the Data Owner) |
| `bop_bop_name` | varchar | Name. |
| `bop_name` | varchar | Name. |
| `bop_sbcref` | integer | (to confirm with the Data Owner) |
| `bop_taxref` | varchar | Taxpayer reference (foreign key to the taxpayer table). |
| `bop_tpref` | varchar | (to confirm with the Data Owner) |
| `bop_vat` | char | (to confirm with the Data Owner) |

## `bopyearmember`

_(no columns resolved — confirm from the connector)_


## `coincentive`

_(no columns resolved — confirm from the connector)_


## `contact`

| Column | Inferred type | Description |
|---|---|---|
| `con_email` | varchar | (to confirm with the Data Owner) |
| `con_fax` | varchar | (to confirm with the Data Owner) |
| `con_locref` | integer | (to confirm with the Data Owner) |
| `con_name` | varchar | Name. |
| `con_phone1` | varchar | (to confirm with the Data Owner) |
| `con_phone2` | varchar | (to confirm with the Data Owner) |
| `con_postcode` | varchar | (to confirm with the Data Owner) |
| `con_rolref` | integer | (to confirm with the Data Owner) |
| `con_serial` | integer | Surrogate primary key (system-generated serial). |
| `con_street` | varchar | (to confirm with the Data Owner) |
| `con_strref` | integer | (to confirm with the Data Owner) |
| `con_taxref` | varchar | Taxpayer reference (foreign key to the taxpayer table). |
| `con_timestamp` | datetime | Row last-modified timestamp (audit). |
| `con_userid` | varchar | User who last modified the row (audit). |
| `con_yrfrom` | varchar | Effective from (year). |
| `con_yrto` | varchar | Effective to (year). |

## `country`

| Column | Inferred type | Description |
|---|---|---|
| `cou_name` | varchar | Name. |
| `cou_serial` | integer | Surrogate primary key (system-generated serial). |

## `fss_errors`

| Column | Inferred type | Description |
|---|---|---|
| `fss_errors` | varchar | (to confirm with the Data Owner) |

## `partner`

| Column | Inferred type | Description |
|---|---|---|
| `par_abbr` | varchar | (to confirm with the Data Owner) |
| `par_endyear` | varchar | (to confirm with the Data Owner) |
| `par_endyearr` | varchar | (to confirm with the Data Owner) |
| `par_serial` | integer | Surrogate primary key (system-generated serial). |
| `par_startyear` | varchar | (to confirm with the Data Owner) |
| `par_taxperson` | integer | (to confirm with the Data Owner) |
| `par_taxref` | varchar | Taxpayer reference (foreign key to the taxpayer table). |
| `par_timestamp` | datetime | Row last-modified timestamp (audit). |
| `par_type` | varchar | (to confirm with the Data Owner) |
| `par_userid` | varchar | User who last modified the row (audit). |
| `par_value` | integer | (to confirm with the Data Owner) |

## `street`

| Column | Inferred type | Description |
|---|---|---|
| `str_locref` | integer | (to confirm with the Data Owner) |
| `str_name1` | varchar | (to confirm with the Data Owner) |
| `str_name2` | varchar | (to confirm with the Data Owner) |
| `str_postcode` | varchar | (to confirm with the Data Owner) |
| `str_serial` | integer | Surrogate primary key (system-generated serial). |

## `taxpayer`

_(no columns resolved — confirm from the connector)_


## `taxpayerlock`

_(no columns resolved — confirm from the connector)_


## `uniquekey`

| Column | Inferred type | Description |
|---|---|---|
| `uni_desc` | varchar | Description / display text. |
| `uni_value` | integer | (to confirm with the Data Owner) |

## `whitefile`

_(no columns resolved — confirm from the connector)_
