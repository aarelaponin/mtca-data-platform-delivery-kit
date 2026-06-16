---
name: verify-catalogue-semantics
description: >-
  Drive a catalogue semantic enrichment from DRAFT to VERIFIED and enforce the catalogue gate — a
  description is DRAFT until verified against an authoritative source (the official form/spec, the
  application code, or data arithmetic that reconciles on real rows) or explicitly marked TO-CONFIRM,
  and only VERIFIED descriptions may drive a mart or the DcP3 handover. Use this WHENEVER the work is
  to confirm, verify, sign off, or gate table/column descriptions: "verify these descriptions",
  "is this column meaning confirmed", "check the semantics before the handover", "DRAFT to VERIFIED",
  "gate the catalogue", "did the box total reconcile", "sign off the data dictionary". Trigger right
  after `legacy-module-to-openmetadata` produces DRAFT descriptions, and before any spec, mart, or
  handover references a column whose meaning is unconfirmed. Ported from ARMS, where a skipped check
  (Box 22 = refund, not tax-due) became a wrong risk score. Cross-platform, pure Python.
---

# Verify catalogue semantics (the DRAFT → VERIFIED gate)

The catalogue is the quality framework's presentation plane and the source of meaning the marts and
the DcP3 handover read. The rule (DQF §S5): **every description is DRAFT until VERIFIED**, and a
wrong description doesn't stay in the catalogue — it becomes a wrong number downstream. This skill
makes that gate concrete and enforceable.

It works on the semantic YAML shape produced by `legacy-module-to-openmetadata` (an `application`
plus `tables[]` each with `columns[]`), but applies to any enrichment of that shape.

## Source-of-truth hierarchy (verify in this order)

1. **The authoritative document** — the official form, the filling instructions, the system spec, or
   the application source code that defines what the field *is*. This is the primary evidence.
2. **Data arithmetic** — verify a stated identity against real rows (e.g. a declaration total equals
   the sum of its component boxes on ~all rows). A meaning that survives the data is VERIFIED; one
   that can't be tested is marked `to_confirm`, not `verified`.
3. **Onboarding profile** — fill rates, constant columns, value ranges give empirical column facts
   (from the `onboard-source` profile).

Never invent meaning. An unclear column gets `to_confirm` with a note, not a confident guess.

## Workflow

### 1 — Scaffold a verification ledger from the DRAFT enrichment

```bash
python3 scripts/verify_semantics.py --emit-ledger <Module>_OpenMetadata.yaml -o ledger.yml
```
The ledger lists every table and column as `draft`, with empty `evidence` / `verified_by` / `date`
for the reviewer to fill. This is the worksheet the Data Owner / steward signs off against.

### 2 — Verify each entity, recording the evidence

For each entity, set `status` to `verified` or `to_confirm` and fill `evidence` (where the meaning
was confirmed — the form field, the spec section, the app code, or the data-arithmetic result),
`verified_by`, and `date`. Use the data-arithmetic helper for identities:

```bash
python3 scripts/verify_semantics.py --check-identity --data rows.csv \
  --identity "box18 = box13 + box15 + box16 + box17" [--tol 0.01]
```
It reports the fraction of rows on which the identity holds: ≥99% → VERIFIED (exit 0), 90–99% → WEAK,
below → FAILS (exit 2). Put the result in the ledger evidence ("data arithmetic: 18=13+15+16+17 holds
99.9%").

### 3 — Apply the ledger → verified YAML + log + coverage

```bash
python3 scripts/verify_semantics.py --apply <Module>_OpenMetadata.yaml --ledger ledger.yml \
  -o <Module>_OpenMetadata.verified.yaml --log verify_log.md
```
This writes a per-entity `status` + `verification` block onto the enrichment, stamps `_meta.verification`
(coverage %, gate PASS/OPEN), and produces a verification log (a signed-off table of every entity with
its status and evidence). Coverage prints to the console.

### 4 — Gate before the meaning drives anything

```bash
python3 scripts/verify_semantics.py --gate <Module>_OpenMetadata.verified.yaml
```
Exits non-zero and lists the offenders if anything is still `draft`/`to_confirm` — wire this into the
handover build and the catalogue publish so **un-VERIFIED meaning cannot reach a mart or the DcP3
package**. (`--allow-to-confirm` relaxes the gate to let TO-CONFIRM through where a partial handover is
explicitly agreed; default is strict — only VERIFIED passes.)

### 5 — Publish and commit

Push the VERIFIED enrichment to OpenMetadata (the catalogue is the system of record), mirror any
descriptions the dbt chain consumes into the model-side `sources.yml`, and commit on the workstation
(the `repo-scaffold` git workflow): `catalogue: verify <Module> semantics (NN/NN VERIFIED)`. Keep the
verification log in the repo as the audit evidence.

## Rules baked in

- **DRAFT is not publishable to a mart or handover.** The gate enforces it; don't bypass it.
- **Evidence is required for VERIFIED.** A status of `verified` with no evidence is not a verification
  — record the form field, spec, app code, or data-arithmetic result.
- **Data arithmetic beats assertion.** If an identity can be tested, test it; ≥99% hold = VERIFIED.
- **Unclear → `to_confirm`, never a guess.** An honest gap is safe; a confident wrong meaning is the
  failure mode this skill exists to prevent.

## Scripts & references

- `scripts/verify_semantics.py` — emit-ledger / apply / gate / check-identity.
- `references/verification-method.md` — the evidence hierarchy in detail, worked examples (form-field
  map, box-total arithmetic), the ledger format, and how the gate wires into handover/publish.
