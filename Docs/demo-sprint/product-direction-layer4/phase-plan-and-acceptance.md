# Phase plan and acceptance: from today's relay to an economic decision product

**Layer 4 companion artifact 7 · AssetOps Architect (Claude) · 16 Nov 2026 · design only**
Main narrative: `layer4-transformation-design.md` §11. Dispositions and touchpoints: `repo-reuse-and-gap-matrix.md`. Labels: [code-observed] [implementation-report] [proposed] [assumption].

This is a **sequencing design**, not a task list. Slices are sized to be reviewable pull requests or small groups of them; the Planner turns approved slices into tasks after owner review (project rule: Architect output is a feature map and causal sequencing).

## 1. Dependency reasoning

**The minimal evidence path to a credible executive decision** is: one site's money truth (commercial and plan records) + one decision with options including do-nothing + one executable safeguard + one portfolio view that compares sites. Everything else widens that path.

**What can be exposed immediately.** The Portfolio API already returns per-site headline money, short values, nodes, earnings, threads, outcome reasons and warning detail that the UI does not render (baseline §5.6) [implementation-report]. Showing them, and relabelling the last-day Optimize figure, needs no new data.

**What must be extended for economic integrity.** Commercial records (D2) and period economics (D3) are the critical path: without them, no CFO answer, no plan-vs-actual in money, and no baseline to value an option against. Typed effects and overlap groups (D4) must land with D3, not after, or the first money-in-the-books release will stack modelled and recorded figures.

**Which cross-vertical primitives pay off.** D2, D3, D4, D5, D6, D9 and D10 are vertical-neutral. Built once on mini-grid, they serve cold and EV with new reconciliations only (storage ledger; roster and tariff).

**Why mini-grid first.** It has the deepest existing analysis (dispatch-3.2, fuel-cost-1/2, reserve trial, verification, fuel balance) and the largest share of demo data. Proving the decision layer where evidence is richest de-risks cold and EV, whose analytics are thinner and whose fixes cannot reach VERIFIED today (`actions/verification_families.py:502`, `:516`) [implementation-report].

**No all-or-nothing build.** Each slice leaves the product more honest and more useful on its own.

```mermaid
flowchart LR
  S1[1 Honest labels + expose computed fields] --> S4
  S2a[2a Commercial records D2] --> S2b[2b Period economics D3 + typed effects D4]
  S2b --> S3[3 Mini-grid decision: Kobo + Kisiwa negative control D5 D6 D7]
  S3 --> S4[4 Portfolio bridge, options, allocation D9 + verification triple D10]
  S2a --> S5[5 Contract rights in repair/capital choices D8]
  S4 --> S5
  S4 --> S6c[6a Cold path]
  S4 --> S6e[6b EV path]
  S5 --> S6c
  S5 --> S6e
  S6c --> S7[7 Pilot onboarding, field validation, optional AI]
  S6e --> S7
  B[Build refactors: scoped replay, O(D) matcher, parallel sites] -.enables.-> S3
  B -.enables.-> S6c
```

Change from the brief's suggested order: none in sequence. Slice 2 is split so commercial records (2a) can start before the period read (2b), and so contract documents can be ingested for slice 5 without waiting for the portfolio work. Build refactors run as a parallel lane because every later slice's demo depends on cheap regeneration.

## 2. Slices

Each slice lists: purpose, scope, main touchpoints (detail in the matrix), test-first anchors, acceptance gate, owner checkpoint.

### Slice 1 — Stop misleading; expose what exists
- **Purpose.** Remove period/value misreadings; show computed-but-hidden fields.
- **Scope.** Optimize card states its figure is one issue's exposure on a named day; portfolio per-site table from existing `sites[].rows[].headline_money/short_value/nodes`; outcome reasons on the board; thread lines structured; claim basis shown. Frontend plus copy; no new backend computation.
- **Touchpoints.** `frontend/src/estate/PortfolioOutcomes.tsx`, `frontend/src/sites/OutcomeBoard.tsx`, `chain/vocabulary.py` (labels) [code-observed via matrix §D].
- **Tests first.** A UI test that a 30-day window's Optimize card names its day; a test that per-site money renders from the existing payload.
- **Gate.** No figure on Portfolio or board can be read as a period total unless it is one. Mock fidelity: v6.9/v7.0 elements kept; any departure labelled MOCK DEVIATION.
- **Owner checkpoint.** Copy review.

### Slice 2a — Commercial records (D2)
- **Purpose.** A store and intake for money-denominated, effective-dated source facts.
- **Scope.** `commercial_record` + revisions; kinds CHARGE, RECEIPT, SETTLEMENT, ADJUSTMENT, EXPENSE, PLAN_LINE (first); CSV upload with dry-run, raw bytes kept, source-versioned revisions, late records accepted; V2 site-bound credentials only; tenant isolation.
- **Touchpoints.** New module beside `reading_upload/` (copy dry-run/receipt, not its late-interval refusal); migration after 0061.
- **Tests first.** Idempotent re-upload (DUP-1); late settlement (LATE-SETTLE-1); cross-tenant refusal (TENANT-1); revision on a corrected row.
- **Gate.** Mto October billing, receipts, settlement and plan lines ingest from emulated CSV and read back exactly.

### Slice 2b — Period economics and typed effects (D3, D4)
- **Purpose.** Plan vs actual in money, with coverage and drivers.
- **Scope.** `site_period_economics` as a sibling read contract that recomputes totals from lines (period read refuses stored totals, D-MONEY.3); Effect gains evidence class and overlap group, extending `estate/financials.py` overlap/CONFLICT marking; `recorded_amount@2`; MG-6 and MG-3 leave "not connected yet".
- **Tests first.** E1–E4 and N1–N3, N6, N11 from the contracts document; bridge identity for Lakeside (−852.00).
- **Gate.** Lakeside October bridge reconciles to the cent with explicit residual and 91.5% coverage; no MODELLED amount appears in a recorded total.

### Slice 3 — One complete mini-grid decision (D5, D6, D7)
- **Purpose.** Prove the decision layer: options, no-action, forward feasibility, safeguards, net value.
- **Scope.** `decisions/` package (decision, option, evaluation pipeline); D1 thread origins (rewrite `occurrence_one_source`, 0042:53, on the 0051 precedent); forward-replay adapter in `host/` over the simulator kernel; SAFEGUARD_POLICIES rows MG5_DAWN_ADEQUACY, MG4_BATTERY_WEAR, WARRANTY_OPERATING_LIMITS, P1_SERVICE_REDUNDANCY; new trial rule `stop-soc-trial-1` with a domain-Action APPLY path for the `stop-soc-threshold` CONTROL property (nothing can apply it today: the `action` table allows only reserve-trial-1) and guardrails generated per option kind (the existing `terminal_soc` guardrail would fail this trial by design); human approval principal for option selection.
- **Tests first.** Kobo: KOB-RESERVE rejected by dawn adequacy, KOB-STOPSOC recommended with net 2,916.00; Kisiwa: zero qualifying fuel options (oracle OR-MG-1, OR-MG-2); B4 sub-case refused (evening energy) — the first test that pins it; rule-3 PV-alone Candidate pinned.
- **Gate.** The C3 "candidate vs necessary diesel" scenario passes end to end; gross exposure is never presented as the option value.
- **Owner checkpoint.** Walk the Kobo decision in the UI.

### Slice 4 — Portfolio variance, alternatives, allocation, verification (D9, D10)
- **Scope.** Mto decisions (huller, welder, billing correction, meter audit) and energy-to-cash reconciliation; tenant allocation run (must-do, subset enumeration, exclusions with reasons, sensitivity); decision home, bridge, comparator, allocation and verification surfaces per the vNEXT mock-up; verification triple with field-source labels.
- **Tests first.** OR-MG-3, OR-MG-4, OR-MG-5; allocation at 5,000 and 6,430; late evidence withdraws a verdict.
- **Gate.** The Lakeside seven-minute walkthrough runs on computed data with no authored conclusion.
- **Owner checkpoint.** Mock-up-vs-product walkthrough (the mock-up is the layout spec once approved).

### Slice 5 — Contract rights in repair and capital choices (D8)
- **Scope.** CONTRACT_DOCUMENT records; AI-assisted extraction proposing obligation/condition/exception/notice/remedy rows that a person must approve; SUPPLIER_CLAIM work-case kind (change the 0027 kind checks) with typed claim events; remedy paths as options; residual cost; deadline flags; no legal determination anywhere in copy.
- **Tests first.** OR-ENT-1 (covered / expired-excluded / insufficient evidence); N5 double recovery; N6 remedy as revenue; notice-deadline flag.
- **Gate.** The three contrasting entitlement cases produce three different recommended actions from the same failure type.

### Slice 6a — Cold path; Slice 6b — EV path
- **Cold.** STORAGE_MOVEMENT records; occupancy ledger and recognised contribution; normalised energy model (per-room calibration on ≥ 60 days hourly); batch exposure with QA and contract liability; cold verification family (first one ever); CC1_TEMPERATURE_LIMIT safeguard. Gate: OR-CC-1, OR-CC-2.
- **EV.** FLEET_ROSTER and TARIFF_SCHEDULE records; session attribution by idTag; deadline-feasibility check; demand-charge only when the tariff record says so; EV verification family; EV1/EV5 safeguards; captive revenue NOT_APPLICABLE. Gate: OR-EV-1..3.
- Order between 6a and 6b decided by the first prospect's vertical (design question Q8).

### Slice 7 — Pilot onboarding, field validation, optional AI
- One real consented customer dataset through the slice-2a adapters; field-integrated provenance class; field verification of one intervention; optional explanation assistant that only cites stored computations (S10) and refuses unsupported numbers.

### Parallel lane B — Build refactors
Scoped regeneration keyed by manifest hash, per-tenant templates, matcher watermark (O(D)), parallel site builds, idle-stage skip, tiered self-check (`demo-build-cost-plan.md` §5.3). Gate: re-benchmark published (§7 of that plan).

## 3. Readiness by capability

| Capability | Today | After slice | Blocker |
|---|---|---|---|
| S1 portfolio economics and coverage | estimates only | 2b | commercial records |
| S2 variance bridge | none | 2b | plan lines |
| S3 qualified opportunities | one rule | 3 | forward replay |
| S4 competing interventions | none | 3 | decision package |
| S5 safeguards before recommendation | hard-coded, partly post-hoc | 3 | policy registry |
| S6 resource and capital prioritisation | none | 4 | allocation run |
| S7 evidence drill-through | partial ("Why?" text) | 4 | commercial record refs |
| S8 action and verification | mini trials, simulated only | 4 (mini), 6 (cold, EV) | verification families |
| S9 pilot onboarding | readings CSV only | 2a, 7 | consented data |
| S10 executive assistant | none | 7 (optional) | stored computations |
| S12 entitlement-aware decisions | mock only | 5 | contract documents + review step |
| MG-C1..C6 | C1 partial | 3, 4, 5 | — |
| CC-C1..C6 | exposure in degree-minutes only | 6a | storage ledger |
| EV-C1..C6 | sessions and faults only | 6b | roster, tariff |

## 4. Resource and generation-cost estimates [assumption]

Effort is stated in the project's existing "units" convention only as relative size, because the brief asks for product priorities, not engineering estimates: slice 1 small; 2a medium; 2b medium; 3 large; 4 large; 5 medium; 6a medium; 6b medium; 7 depends on the pilot. Generation cost per hero: `demo-build-cost-plan.md` §6 (targets until re-benchmarked).

## 5. API and UI migration

- New reads are additive (`/api/estate/economics`, `/api/sites/{code}/economics`, `/api/decisions/...`, `/api/allocations/...`) [proposed]; existing Portfolio and board payloads keep their shape. The vNEXT decision home is a new route; the current Portfolio stays as the operations view until the owner decides otherwise (design question Q2).
- Route caches (`chain_response`) are keyed by inputs digest; period economics and decisions add their own digests so late records invalidate precisely.

## 6. Snapshot reproducibility

Every decision evaluation stores its inputs digest (period economics revision, Finding revisions, forward-replay projection hash, policy versions). A decision screen can always show "evaluated on <date> from these records"; re-evaluation creates a new revision and keeps the old one.

## 7. End-to-end release tests

| Id | Covers | Pass condition |
|---|---|---|
| R1 Economic identities | E1–E6 | all identities exact for all 9 manifest sites |
| R2 Source coverage | N1, GAP-1 | estimated and missing lines named; coverage shown |
| R3 Negative controls | OR-MG-2, Mwea, CH-R7 | no option or Finding beyond expectation |
| R4 Third-party remedy conditionality | OR-ENT-1, N5, N6 | potential rights never booked; three cases differ |
| R5 Constraint-protected recommendations | KOB-RESERVE, EMB-CHEAPEST | rejected before recommendation, with reason |
| R6 Cross-tenant isolation | TENANT-1 | refused at ingest and at every read |
| R7 Integration disorder | DUP-1, OOO-1, LATE-SETTLE-1, MAP-1, FX-1, CLOCK-1 | expected behaviour per manifest |
| R8 Front-end interaction | vNEXT walkthroughs | every walkthrough click path works on computed data; WCAG 2.2 AA spot checks; 390 px |
| R9 Mock-up change log | CHANGE-REGISTER.md | every changed screen accounted for and approved by the owner |
| R10 Verification integrity | D10 | operation, money and cause verdicts separate; supplier repair, credit and cash distinct |

## 8. Commercial validation (no fabricated benchmarks)

Observe, per prospect demo: (1) demo completed to the convert step; (2) prospect names the issue as theirs ("we have that"), recorded verbatim; (3) which decision they want investigated on their own portfolio; (4) data-access feasibility per manifest source category (yes / with effort / no); (5) paid diagnostic accepted, declined or deferred, with reason. Record in a simple sheet; no conversion rate is claimed until there are real observations.

**Customer-facing diagnostic offer (template).** *Three-site economic diagnostic, about four weeks from data receipt.* You provide: site and asset list, 60–90 days of controller exports, four months of billing and receipts, meter change log, fuel or storage or roster records, your monthly plan, and your three most important equipment contracts. You receive: a reconciled actual-vs-plan bridge per site with coverage; the three highest-value decisions with do-nothing compared and the options we would reject and why; contract rights at risk with deadlines; a verification plan for the first change. Agreed validation: figures reconcile to your books within a stated tolerance; your operations lead confirms each recommended change is feasible. We do not promise savings; we show how they would be proven.

## 9. Owner approval checkpoints

1. This design pack (direction, D1–D10, demo worlds).
2. The vNEXT mock-up (separate gate; not approved until inspected).
3. After slice 3: Kobo decision walkthrough.
4. After slice 4: Lakeside seven-minute demo on computed data.
5. After slice 5: entitlement copy and the "not a legal decision" boundary.
6. Before slice 7: pilot consent, data protection and integration rights.
