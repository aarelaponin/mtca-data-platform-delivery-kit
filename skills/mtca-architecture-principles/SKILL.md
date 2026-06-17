---
name: mtca-architecture-principles
description: >-
  Settle MTCA Data Platform design decisions by CITATION to a numbered, priority-ordered principles
  register (open-source/no lock-in, comprehensive platform, classification-first, single-source-of-truth,
  verify-before-publish, reconcile-every-transfer, version-controlled, cross-platform, …) and record
  the decision as an ADR that cites the principle(s). Use this WHENEVER a weighty X-or-Y / build-or-buy
  / now-or-later question comes up: "should we use SAS or dbt for X", "build or buy this", "why
  open-source", "is this the right architecture", "record this decision", "write an ADR", "which
  principle applies", "justify this choice to the DGC". Trigger even when the user just debates an
  approach — turning the debate into a one-line citation (and an ADR) is the method, and it's what
  stops the same argument being re-litigated every mission. Distilled from the Blueprint + DQF, modelled
  on the ARMS principles register. Cross-platform, pure Python.
---

# MTCA architectural principles (decide by citation)

Big decisions on this platform shouldn't be re-argued from scratch each time. This skill holds a
**numbered, priority-ordered, citable** register of the platform's architectural principles, and turns
a decision into an **ADR** that cites the relevant principle(s). A debate that maps to P1 becomes a
one-line reference, not a fresh argument; a decision that cites no principle is a flag to stop and think.

The register is deliberately about the *weighty* questions (X-or-Y, build-or-buy, now-or-later) and
silent on tactical ones (file paths, syntax, ops). It lives as data in
`references/principles-register.yaml` — evolve it with the DGC; the tool reads it.

## The register (v0.1, 14 principles)

P1 open-source/no lock-in · P2 one comprehensive platform (ingest once, serve many) · P3
classification-first / Restricted-by-default / DPIA gates real data · P4 automation-first · P5
generated artefacts never hand-edited · P6 single source of truth / pull-from-Gold · P7 tables & rules
in configuration · P8 build capability not dependency · P9 technology follows workload · P10 evidence
not assertion · P11 verify before publish · P12 reconcile every custody transfer · P13
version-controlled by default · P14 cross-platform by default.

Read `references/principles-register.yaml` for each principle's full statement, rationale, citation and
a worked example.

## Workflow

### List the principles

```bash
python3 scripts/principles.py --list
```

### Record a decision as an ADR (citing principles)

Write a short decision spec:
```yaml
title: Data-quality tooling — dbt + OpenMetadata, not SAS
status: Accepted
context: A SAS licence is held; some proposed SAS as the data-quality tool.
options:
  - {name: SAS as DQ tool, note: reuses an existing licence}
  - {name: dbt + OpenMetadata, note: open-source, on-platform; SAS remains a Gold consumer}
decision: Data quality is owned by dbt contracts + OpenMetadata monitoring; SAS consumes Gold.
principles: [P1, P9, P6]
consequences: One DQ system of record; SAS onboarded as a consumer.
```
```bash
python3 scripts/principles.py --new-adr --spec decision.yml --number 0007 -o docs/adr/0007-dq-tooling.md
```
It validates that every cited principle exists (an ADR can't lean on a principle that isn't in the
register) and renders a numbered ADR with the cited principles spelled out. Save it under `docs/adr/`.

### Gate a decision (must cite a principle)

```bash
python3 scripts/principles.py --check --spec decision.yml
```
Exits non-zero if the decision cites an unknown principle or none at all. Useful in review: a weighty
decision that cites no principle isn't ready.

### Commit

Commit the ADR on the workstation (`repo-scaffold` git workflow): `docs: ADR-0007 DQ tooling`.

## How to use it in practice

- When a build-or-buy / X-or-Y question arises, **find the principle first**. Most are already settled:
  "we own a SAS licence" → P1 + P9 (licence is a cost fact, not an architecture reason; SAS is a Gold
  consumer). "Each team wants its own copy of the data" → P2 + P6 (one platform, pull from Gold).
- If **no principle fits**, that's a signal: either it's a genuinely new architectural question (write
  the ADR and propose a new principle to the DGC), or it's a tactical question the register correctly
  stays silent on (just decide).
- The register is **priority-ordered** — when principles tension (e.g. speed vs evidence), the
  lower-numbered one generally wins; record the trade-off in the ADR's consequences.

## Rules baked in

- **Decide by citation, not by re-argument.** The register exists so settled questions stay settled.
- **An ADR cites a real principle.** The tool enforces it; a citation to a non-existent principle fails.
- **The register is data, governed by the DGC.** Change principles deliberately (in the YAML, reviewed),
  not by quietly reinterpreting them.

## Scripts & references

- `scripts/principles.py` — `--list`, `--new-adr` (validated), `--check`.
- `references/principles-register.yaml` — the register itself (id, title, statement, rationale, cites,
  example), the editable source of truth.
