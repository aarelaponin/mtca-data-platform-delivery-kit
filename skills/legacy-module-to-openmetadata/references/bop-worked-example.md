# Worked example — BOP Registration (finished output)

_This is the completed, human-finished enrichment from the original experiment: 25 tables /
141 columns, recovered from `bopindex.pbl` source only. Use it as the quality bar for a
finished output — note the concrete business descriptions and the DRAFT/verification caveats._

---

# BOP Registration — OpenMetadata Semantic Enrichment

**Module:** Body of Persons (BOP) Registration · legacy PowerBuilder · Inland Revenue (`irdnew`, Informix)  
**Generated:** 2026-06-16  
**Status:** DRAFT — descriptions inferred from naming + Malta IRD domain knowledge; require Data-Owner confirmation (DQF control DQC-S1-03). Columns listed are those THIS module references, not necessarily the full table schema.

> Load as description enrichment onto the connector-ingested entities (PATCH descriptions via the OpenMetadata SDK, or use as a semantic map). The custom Informix connector supplies authoritative data types and lengths; 'inferredType' here is a hint only.

Legacy PowerBuilder module that registers and maintains Bodies of Persons (partnerships, associations and foundations treated as bodies of persons): their identity and activity, annual membership/ownership snapshots, partners, contacts and addresses, accounting periods, incentives, notes, foundation data and the taxpayer 'white file'. It reads/writes the Inland Revenue (irdnew) Informix database.

**Tables used (25):** `taxpayer`, `bop`, `bopyearmember`, `partner`, `contact`, `accountperiod`, `coincentive`, `note`, `foundation`, `whitefile`, `year`, `incentive`, `codednote`, `locality`, `street`, `country`, `category`, `subcategory`, `role`, `reason`, `return`, `taxpayerlock`, `uniquekey`, `fss_errors`, `employer`


## `taxpayer`  —  _REG_

Taxpayer master register (Inland Revenue). One row per registered taxpayer — individuals and bodies of persons — holding identity, category, registration, address references, return obligations and audit fields. The central entity the BOP module reads and links every other record to.

| Column | Inferred type | Description |
|---|---|---|
| `tax_abode` | char | Place-of-abode / residence indicator. |
| `tax_admnname` | varchar | Administrator name (for an estate / body of persons). |
| `tax_admref` | integer | Administrator reference (FK). |
| `tax_catref` | integer | Category reference (FK → category). |
| `tax_deletion` | char | Deletion / inactive flag. |
| `tax_dobirth` | datetime | Date of birth (individuals). |
| `tax_dodeath` | datetime | Date of death (individuals). |
| `tax_firstret` | varchar | First return year. |
| `tax_language` | varchar | Preferred correspondence language. |
| `tax_lastret` | varchar | Last return year. |
| `tax_rearef` | integer | Reason reference (FK → reason). |
| `tax_regdate` | datetime | Registration date. |
| `tax_retref` | integer | Return reference (FK → return; return type/obligation). |
| `tax_sect` | varchar | IRD section / office code responsible for the taxpayer. |
| `tax_security` | char | Security / access classification of the record. |
| `tax_serial` | integer | Surrogate primary key (system-generated serial). |
| `tax_strref` | integer | Street reference (FK → street; address). |
| `tax_timestamp` | datetime | Row last-modified timestamp (audit). |
| `tax_tpform` | char | Taxpayer form / type (e.g. individual, body of persons). |
| `tax_tpref` | varchar | Taxpayer reference number — the taxpayer's legal registration identifier. |
| `tax_user` | varchar | User who last modified the row (audit). |
| `tax_userid` | varchar | User who last modified the row (audit). |

## `bop`  —  _REG_

Body of Persons (BOP) registration. One row per registered Body of Persons (partnership, association or foundation treated as a body of persons), holding its name, principal activity, sub-category, VAT and the link to its taxpayer record. The module's primary entity.

| Column | Inferred type | Description |
|---|---|---|
| `bop_activity` | varchar | Principal activity / business of the Body of Persons. |
| `bop_assoctaxref` | integer | Associated taxpayer reference (e.g. parent / associated entity). |
| `bop_bop_name` | varchar | Body-of-Persons name (alternate / formatted name field). |
| `bop_name` | varchar | Registered name of the Body of Persons. |
| `bop_sbcref` | integer | Sub-category reference (FK → subcategory). |
| `bop_taxref` | varchar | Taxpayer reference of the Body of Persons (FK → taxpayer). |
| `bop_tpref` | varchar | The Body of Persons' own taxpayer reference number. |
| `bop_vat` | char | VAT registration number / VAT-registered flag. |

## `bopyearmember`  —  _REG_

Annual membership / ownership snapshot of a Body of Persons. One row per BOP per year recording paid-up members, voting members and the percentage-control test used in ownership/control assessments.

| Column | Inferred type | Description |
|---|---|---|
| `bym_paidupmem` | integer | Paid-up members (or paid-up capital members) measure. |
| `bym_perctest` | integer | Percentage-control test value (ownership / control %). |
| `bym_serial` | integer | Surrogate primary key (system-generated serial). |
| `bym_taxref` | varchar | Body of Persons reference (FK → bop / taxpayer). |
| `bym_votingmem` | integer | Voting members measure. |
| `bym_year` | integer | Year of the membership / ownership snapshot. |

## `partner`  —  _REG_

Partners of a Body of Persons. One row per partner, linking the BOP to the partner's own taxpayer record, with partner type, interest value and effective years.

| Column | Inferred type | Description |
|---|---|---|
| `par_abbr` | varchar | Abbreviation / short code for the partner. |
| `par_endyear` | varchar | Effective to (year). |
| `par_endyearr` | varchar | Effective to (year) — alternate field. |
| `par_serial` | integer | Surrogate primary key (system-generated serial). |
| `par_startyear` | varchar | Effective from (year). |
| `par_taxperson` | integer | The partner's own taxpayer reference (FK → taxpayer). |
| `par_taxref` | varchar | Body of Persons reference (FK → bop). |
| `par_timestamp` | datetime | Row last-modified timestamp (audit). |
| `par_type` | varchar | Partner type (e.g. general / limited). |
| `par_userid` | varchar | User who last modified the row (audit). |
| `par_value` | integer | Partner's share value / interest. |

## `contact`  —  _REG_

Contact details and correspondence address(es) for a taxpayer / Body of Persons — name, role, e-mail, telephone/fax and a structured address (street, locality, postcode) — with effective years.

| Column | Inferred type | Description |
|---|---|---|
| `con_email` | varchar | E-mail address. |
| `con_fax` | varchar | Fax number. |
| `con_locref` | integer | Locality reference (FK → locality). |
| `con_name` | varchar | Contact name. |
| `con_phone1` | varchar | Primary telephone number. |
| `con_phone2` | varchar | Secondary telephone number. |
| `con_postcode` | varchar | Postcode. |
| `con_rolref` | integer | Contact role reference (FK → role). |
| `con_serial` | integer | Surrogate primary key (system-generated serial). |
| `con_street` | varchar | Street (free-text address line). |
| `con_strref` | integer | Street reference (FK → street). |
| `con_taxref` | varchar | Taxpayer reference (foreign key to taxpayer). |
| `con_timestamp` | datetime | Row last-modified timestamp (audit). |
| `con_userid` | varchar | User who last modified the row (audit). |
| `con_yrfrom` | varchar | Effective from (year). |
| `con_yrto` | varchar | Effective to (year). |

## `accountperiod`  —  _COMPLIANCE_

Tax accounting periods for a taxpayer — year, period code, accounting date and permit status — with effective range and audit fields.

| Column | Inferred type | Description |
|---|---|---|
| `acc_date` | datetime | Accounting / period date. |
| `acc_period` | varchar | Period code. |
| `acc_permit` | char | Permit / approval flag. |
| `acc_serial` | integer | Surrogate primary key (system-generated serial). |
| `acc_taxref` | varchar | Taxpayer reference (foreign key to taxpayer). |
| `acc_timestamp` | datetime | Row last-modified timestamp (audit). |
| `acc_userid` | varchar | User who last modified the row (audit). |
| `acc_year` | integer | Tax year. |
| `acc_yrfrom` | varchar | Effective from (year). |
| `acc_yrto` | varchar | Effective to (year). |

## `coincentive`  —  _INCENTIVES_

Tax incentives granted to a taxpayer (company/co-operative incentives). Links a taxpayer to an incentive type with details and an effective year.

| Column | Inferred type | Description |
|---|---|---|
| `cin_details` | varchar | Free-text details of the incentive grant. |
| `cin_incref` | integer | Incentive reference (FK → incentive). |
| `cin_serial` | integer | Surrogate primary key (system-generated serial). |
| `cin_taxref` | varchar | Taxpayer reference (foreign key to taxpayer). |
| `cin_timestamp` | datetime | Row last-modified timestamp (audit). |
| `cin_userid` | varchar | User who last modified the row (audit). |
| `cin_yrfrom` | varchar | Effective from (year). |

## `note`  —  _REG_

Notes attached to a taxpayer — a coded note type plus free text and document references — scoped by IRD section and effective years.

| Column | Inferred type | Description |
|---|---|---|
| `not_codref` | integer | Coded-note reference (FK → codednote; note type). |
| `not_docs` | char | Document / attachment reference. |
| `not_freetext` | varchar | Free-text note content. |
| `not_irdsect` | varchar | IRD section the note is scoped to. |
| `not_serial` | integer | Surrogate primary key (system-generated serial). |
| `not_taxref` | varchar | Taxpayer reference (foreign key to taxpayer). |
| `not_timestamp` | datetime | Row last-modified timestamp (audit). |
| `not_userid` | varchar | User who last modified the row (audit). |
| `not_yrfrom` | varchar | Effective from (year). |
| `not_yrto` | varchar | Effective to (year). |

## `foundation`  —  _REG_

Foundation-specific registration data for Bodies of Persons that are foundations — provisional/registration number, voluntary-organisation number and first-administrator date.

| Column | Inferred type | Description |
|---|---|---|
| `fou_firstadmindate` | datetime | Date of the first administrator. |
| `fou_prno` | integer | Provisional / registration number. |
| `fou_serial` | integer | Surrogate primary key (system-generated serial). |
| `fou_taxref` | varchar | Taxpayer / BOP reference (FK → taxpayer). |
| `fou_vono` | integer | Voluntary-organisation (VO) number. |

## `whitefile`  —  _REG_

The taxpayer 'white file' — the physical/registration file number assigned to a taxpayer.

| Column | Inferred type | Description |
|---|---|---|
| `wfl_number` | integer | White-file (physical file) number. |
| `wfl_serial` | integer | Surrogate primary key (system-generated serial). |
| `wfl_taxref` | varchar | Taxpayer reference (FK → taxpayer). |

## `year`  —  _REG_

Per-taxpayer year record used for year-level record locking (locking user and lock time), preventing concurrent edits of a taxpayer's year.

| Column | Inferred type | Description |
|---|---|---|
| `yea_locktime` | datetime | Lock timestamp (when the year was locked for editing). |
| `yea_lockuser` | varchar | User holding the lock. |
| `yea_taxref` | varchar | Taxpayer reference (FK → taxpayer). |
| `yea_year` | integer | Tax / account year. |

## `incentive`  —  _REFERENCE_

Reference list of incentive types (description, applicability scope).

| Column | Inferred type | Description |
|---|---|---|
| `inc_desc` | varchar | Description / display text. |
| `inc_scope` | varchar | Applicability scope of the reference value. |
| `inc_serial` | integer | Surrogate primary key (system-generated serial). |

## `codednote`  —  _REFERENCE_

Reference list of coded note types / templates (note text, parameter, scope).

| Column | Inferred type | Description |
|---|---|---|
| `cdn_note` | varchar | Coded-note text / label. |
| `cdn_parameter` | varchar | Parameter for the coded note. |
| `cdn_scope` | varchar | Applicability scope of the reference value. |
| `cdn_serial` | integer | Surrogate primary key (system-generated serial). |

## `locality`  —  _REFERENCE_

Reference list of localities (towns/villages), linked to country.

| Column | Inferred type | Description |
|---|---|---|
| `loc_couref` | integer | Country reference (FK → country). |
| `loc_name` | varchar | Name. |
| `loc_serial` | integer | Surrogate primary key (system-generated serial). |
| `loc_taxref` | varchar | Taxpayer reference (foreign key to taxpayer). |
| `loc_timestamp` | datetime | Row last-modified timestamp (audit). |
| `loc_userid` | varchar | User who last modified the row (audit). |

## `street`  —  _REFERENCE_

Reference list of streets (two name lines and postcode), linked to locality.

| Column | Inferred type | Description |
|---|---|---|
| `str_locref` | integer | Locality reference (FK → locality). |
| `str_name1` | varchar | Street name — line 1. |
| `str_name2` | varchar | Street name — line 2. |
| `str_postcode` | varchar | Postcode. |
| `str_serial` | integer | Surrogate primary key (system-generated serial). |

## `country`  —  _REFERENCE_

Reference list of countries (code, name).

| Column | Inferred type | Description |
|---|---|---|
| `cou_name` | varchar | Name. |
| `cou_serial` | integer | Surrogate primary key (system-generated serial). |

## `category`  —  _REFERENCE_

Reference list of taxpayer categories (code prefix, description, scope).

| Column | Inferred type | Description |
|---|---|---|
| `cat_desc` | varchar | Description / display text. |
| `cat_prefix` | varchar | Code prefix used in numbering. |
| `cat_scope` | varchar | Applicability scope of the reference value. |
| `cat_serial` | integer | Surrogate primary key (system-generated serial). |

## `subcategory`  —  _REFERENCE_

Reference list of taxpayer sub-categories, each under a parent category.

| Column | Inferred type | Description |
|---|---|---|
| `sbc_catref` | integer | Parent category reference (FK → category). |
| `sbc_desc` | varchar | Description / display text. |
| `sbc_serial` | integer | Surrogate primary key (system-generated serial). |

## `role`  —  _REFERENCE_

Reference list of contact roles.

| Column | Inferred type | Description |
|---|---|---|
| `rol_desc` | varchar | Description / display text. |
| `rol_scope` | varchar | Applicability scope of the reference value. |
| `rol_serial` | integer | Surrogate primary key (system-generated serial). |

## `reason`  —  _REFERENCE_

Reference list of reasons (e.g., registration / status reasons).

| Column | Inferred type | Description |
|---|---|---|
| `rea_desc` | varchar | Description / display text. |
| `rea_scope` | varchar | Applicability scope of the reference value. |
| `rea_serial` | integer | Surrogate primary key (system-generated serial). |

## `return`  —  _REFERENCE_

Reference list of return types / obligations.

| Column | Inferred type | Description |
|---|---|---|
| `ret_desc` | varchar | Description / display text. |
| `ret_scope` | varchar | Applicability scope of the reference value. |
| `ret_serial` | integer | Surrogate primary key (system-generated serial). |

## `taxpayerlock`  —  _REG_

Concurrency-control table — records which taxpayer is currently locked for editing, by which user and since when. Rows are inserted, updated and deleted as users open and close records.

_(columns not resolvable from static analysis — confirm from the Informix catalogue)_


## `uniquekey`  —  _REFERENCE_

Sequence / key generator — supplies the next surrogate-key value used for inserts across the application.

| Column | Inferred type | Description |
|---|---|---|
| `uni_value` | integer | Next surrogate-key value to assign. |

## `fss_errors`  —  _FSS_

Error log for the FSS (Final Settlement System / employer PAYE) interface — validation and processing errors raised during FSS handling.

_(columns not resolvable from static analysis — confirm from the Informix catalogue)_


## `employer`  —  _FSS_

Employer register link — an employer reference keyed to a taxpayer reference, used where a Body of Persons is also an employer (the FSS path).

| Column | Inferred type | Description |
|---|---|---|
| `em_empr_ref` | integer | Employer reference. |
| `em_tp_ref` | integer | Taxpayer reference (FK → taxpayer). |

---
### Caveats

- The module also calls shared libraries (ird_dataaccess, ird_common, ird_search) not analysed here — the running app may touch more tables/columns.
- DataWindow display/edit suffixes (_t, __t__f) were stripped; verify a few columns against the Informix catalogue.