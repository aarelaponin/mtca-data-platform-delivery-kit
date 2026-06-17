# BOP_Registration — OpenMetadata Semantic Enrichment (DRAFT scaffold)

_Generated 2026-06-17 · Static analysis of bopindex.pbl (DataWindow + embedded SQL)._

> DRAFT SCAFFOLD — table/business-column descriptions are TODO; complete them from naming + domain, then VERIFY against an authoritative source before publishing (catalogue control). Authoritative data types come from the catalogue connector; 'inferredType' is a hint only.

**Tables used (27):** `accountperiod`, `administrator`, `application`, `bop`, `category`, `codednote`, `coincentive`, `contact`, `country`, `foundation`, `incentive`, `list`, `locality`, `note`, `parameter`, `reason`, `return`, `sect`, `std_message`, `street`, `taxpayer`, `bopyearmember`, `fss_errors`, `partner`, `taxpayerlock`, `uniquekey`, `whitefile`

**Unmapped column prefixes (assign to a table):** `bym_*`, `cdn_*`, `cin_*`, `em_*`, `fsse_*`, `ird_*`, `par_*`, `rol_*`, `sbc_*`, `tax_*`, `wfl_*`, `yea_*`


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

## `administrator`

| Column | Inferred type | Description |
|---|---|---|
| `adm_desc` | varchar | Description / display text. |
| `adm_serial` | integer | Surrogate primary key (system-generated serial). |

## `application`

_(no columns resolved — confirm from the connector)_


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

## `category`

| Column | Inferred type | Description |
|---|---|---|
| `cat_desc` | varchar | Description / display text. |
| `cat_prefix` | varchar | Code prefix used in numbering. |
| `cat_scope` | varchar | Applicability scope of the reference value. |
| `cat_serial` | integer | Surrogate primary key (system-generated serial). |

## `codednote`

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

## `foundation`

| Column | Inferred type | Description |
|---|---|---|
| `fou_firstadmindate` | datetime | (to confirm with the Data Owner) |
| `fou_prno` | integer | (to confirm with the Data Owner) |
| `fou_serial` | integer | Surrogate primary key (system-generated serial). |
| `fou_taxref` | varchar | Taxpayer reference (foreign key to the taxpayer table). |
| `fou_vono` | integer | (to confirm with the Data Owner) |

## `incentive`

| Column | Inferred type | Description |
|---|---|---|
| `inc_desc` | varchar | Description / display text. |
| `inc_scope` | varchar | Applicability scope of the reference value. |
| `inc_serial` | integer | Surrogate primary key (system-generated serial). |

## `list`

_(no columns resolved — confirm from the connector)_


## `locality`

| Column | Inferred type | Description |
|---|---|---|
| `loc_couref` | integer | (to confirm with the Data Owner) |
| `loc_name` | varchar | Name. |
| `loc_serial` | integer | Surrogate primary key (system-generated serial). |
| `loc_taxref` | varchar | Taxpayer reference (foreign key to the taxpayer table). |
| `loc_timestamp` | datetime | Row last-modified timestamp (audit). |
| `loc_userid` | varchar | User who last modified the row (audit). |

## `note`

| Column | Inferred type | Description |
|---|---|---|
| `not_codref` | integer | (to confirm with the Data Owner) |
| `not_docs` | char | (to confirm with the Data Owner) |
| `not_freetext` | varchar | (to confirm with the Data Owner) |
| `not_irdsect` | varchar | (to confirm with the Data Owner) |
| `not_serial` | integer | Surrogate primary key (system-generated serial). |
| `not_taxref` | varchar | Taxpayer reference (foreign key to the taxpayer table). |
| `not_timestamp` | datetime | Row last-modified timestamp (audit). |
| `not_userid` | varchar | User who last modified the row (audit). |
| `not_yrfrom` | varchar | Effective from (year). |
| `not_yrto` | varchar | Effective to (year). |
| `note_not_docs` | char | (to confirm with the Data Owner) |
| `note_not_userid` | varchar | User who last modified the row (audit). |
| `note_not_yrfrom` | varchar | Effective from (year). |
| `note_not_yrto` | varchar | Effective to (year). |
| `note_serial` | integer | Surrogate primary key (system-generated serial). |

## `parameter`

_(no columns resolved — confirm from the connector)_


## `reason`

| Column | Inferred type | Description |
|---|---|---|
| `rea_desc` | varchar | Description / display text. |
| `rea_scope` | varchar | Applicability scope of the reference value. |
| `rea_serial` | integer | Surrogate primary key (system-generated serial). |

## `return`

| Column | Inferred type | Description |
|---|---|---|
| `ret_desc` | varchar | Description / display text. |
| `ret_scope` | varchar | Applicability scope of the reference value. |
| `ret_serial` | integer | Surrogate primary key (system-generated serial). |

## `sect`

_(no columns resolved — confirm from the connector)_


## `std_message`

| Column | Inferred type | Description |
|---|---|---|
| `std_message` | varchar | (to confirm with the Data Owner) |

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


## `bopyearmember`  _(via DML; not in inventory — confirm)_

_(no columns resolved — confirm from the connector)_


## `fss_errors`  _(via DML; not in inventory — confirm)_

| Column | Inferred type | Description |
|---|---|---|
| `fss_errors` | varchar | (to confirm with the Data Owner) |

## `partner`  _(via DML; not in inventory — confirm)_

_(no columns resolved — confirm from the connector)_


## `taxpayerlock`  _(via DML; not in inventory — confirm)_

_(no columns resolved — confirm from the connector)_


## `uniquekey`  _(via DML; not in inventory — confirm)_

| Column | Inferred type | Description |
|---|---|---|
| `uni_desc` | varchar | Description / display text. |
| `uni_value` | integer | (to confirm with the Data Owner) |

## `whitefile`  _(via DML; not in inventory — confirm)_

_(no columns resolved — confirm from the connector)_
