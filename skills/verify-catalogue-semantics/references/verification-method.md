# Verification method — evidence, ledger, and the gate

## Why this gate exists (the ARMS lesson)

On the sister project, a catalogue stub described a declaration box as "tax payable" when it was the
**refund-claim** box. A risk indicator was built on that stub — and produced a wrong risk score for
every affected taxpayer. The description was never verified against the form. That is the whole
reason DRAFT meaning may not drive a mart or a handover: **a wrong description becomes a wrong
number**, and the further downstream it's caught, the more expensive it is.

## Evidence hierarchy (what makes a description VERIFIED)

Use in this order; record which one in the ledger `evidence` field.

1. **Authoritative document or code.** The official form + filling instructions, the system/spec
   document, or the application source that defines the field. For legacy modules, the PowerBuilder
   source (the `legacy-module-to-openmetadata` input) is strong evidence of *use*; the form/spec is
   evidence of *meaning*. Quote the specific field/section.
2. **Data arithmetic.** A stated identity tested on real rows — a total equals the sum of its parts,
   a flag is mutually exclusive, a code is always within a reference set. Use `--check-identity`.
   ≥99% hold → VERIFIED; 90–99% → WEAK (investigate the exceptions before trusting it); <90% → the
   stated meaning is wrong, fix it.
3. **Onboarding profile.** Fill rate, constancy, value range (from `onboard-source`). Empirical, not
   semantic — it tells you a column is e.g. always null or constant (which itself can disprove a
   stated meaning), but it doesn't by itself confirm meaning.

A description with none of these is `to_confirm`, not `verified`. Never invent meaning to clear a row.

## The ledger format

`--emit-ledger` scaffolds one item per table and column:

```yaml
source_yaml: BOP_Registration_OpenMetadata.yaml
items:
  - ref: taxpayer                 # table
    kind: table
    status: verified              # verified | to_confirm | draft
    evidence: "BOP registration form, taxpayer block; Data-Owner sign-off"
    verified_by: jdoe
    date: 2026-06-18
  - ref: taxpayer.tax_vatno       # <table>.<column>
    kind: column
    status: verified
    evidence: "official form field 'VAT No'"
    verified_by: jdoe
    date: 2026-06-18
  - ref: bopyearmember.bym_perctest
    kind: column
    status: to_confirm
    evidence: "meaning unclear — query the Data Owner"
    verified_by: ""
    date: ""
```

`--apply` merges this onto the enrichment, writing a `status` and a `verification` block onto each
entity and stamping `_meta.verification` (coverage %, gate PASS/OPEN).

## Worked example — data arithmetic

A declaration form states box 18 is the sum of boxes 13, 15, 16, 17. Test it on a Bronze sample:

```bash
python3 scripts/verify_semantics.py --check-identity --data declarations_sample.csv \
  --identity "box18 = box13 + box15 + box16 + box17" --tol 0.01
```

- ~100% hold → the box map is VERIFIED; record "data arithmetic: 18=13+15+16+17 holds 99.9% (n=…)".
- A few percent fail → look at the failing rows before trusting it (rounding? a sign? a special
  regime?). Don't mark VERIFIED on a WEAK result.
- Many fail → the stated identity (hence the description) is wrong; fix the meaning, not the data.

The expression is evaluated per row with column names as variables; only arithmetic
(`+ - * / ( )`) is allowed, so it's safe to run on arbitrary specs.

## Wiring the gate

`--gate` exits non-zero if anything is not VERIFIED. Wire it into:

- **the handover build** — the DcP3 package build runs `--gate` on each module's verified enrichment;
  a non-VERIFIED entity blocks the package (DQC-S5-02).
- **the catalogue publish** — publish only the verified YAML; the gate is the pre-publish check.
- **CI** — optionally gate on PRs that touch an enrichment, so DRAFT meaning can't merge into the
  catalogue source.

Default is strict (only `verified` passes). `--allow-to-confirm` is an explicit, logged relaxation
for a partial handover agreed with the steward — use it deliberately, not as the default.

## Relationship to the other catalogue skills

- `legacy-module-to-openmetadata` **produces** the DRAFT enrichment (tables/columns/descriptions).
- `import-schema-to-catalogue` brings the **technical** metadata + reference vocabularies from DDL.
- **this skill** turns DRAFT business meaning into VERIFIED and gates it.
- All three land their output in the repo and commit via the `repo-scaffold` git workflow; the
  catalogue (OpenMetadata) is the published system of record.
