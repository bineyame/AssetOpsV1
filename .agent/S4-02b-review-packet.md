# S4-02b review packet: bounded fuel consequence and repricing (phases 1, 2a, 2b)

Task `tasks/S4-02b-fuel-consequence.md`; branch `task/S4-02b-fuel-consequence` from main `14ad5ef`. USER_REVIEW_REQUIRED: true (S4-02 owner checkpoint after a fresh review). Governing: `D-2026-10-13-s4-bounded-financial-basis` + addendum, `.agent/architect-S4-02-answers.md`, owner ruling `.agent/owner-S4-02b-money-demo-2026-10-14.md`.

## Outcome delivered

From one exact SUPPORTED FindingRevision, Site Financials shows a modelled, assumption-conditioned potential fuel-cost exposure "0.00 to X" only for a CURRENT PRICED consequence, with the quantity → price → amount bridge, the exact price version and lineage in a disclosure, and every no-amount state typed and worded: QUANTITY_UNAVAILABLE (specific reason), UNPRICED, PENDING, STALE, HISTORICAL, AUDIT_ONLY (closed source), UNAVAILABLE. A backdated SYSTEM correction (v4) appends a new consequence over the same FindingRevision and fuel amount; old versions stay inspectable by ID and survive reload.

## Phases and commits

| Phase | Commits | Review |
| --- | --- | --- |
| 1 `fuel-cost-1` + store | `7cbdef7`..`bc88a0e` | `.agent/S4-02b-phase-1-review.md` ACCEPT with carries |
| 2a read + recompute | `5d400d6`..`7c21931` | `.agent/S4-02b-phase-2a-review.md` ACCEPT with carries (M1, M2, L1-L4) |
| 2b UI, walkthrough, evidence | `dbaba10`..HEAD | this packet; fresh review next |

## Files materially changed in 2b

- Backend: `financials/consequence_read.py` (`source_open`, `AUDIT_ONLY`), `finding_api.py` (gate passed to read and bridge; STALE wording from pending work; `demonstration`), new `demonstration_label.py`.
- Tests: `test_s4_assumption_read_api.py` (L1, M1 gate passing, L4 wording, demonstration label), `test_s4_consequence_recompute_postgres.py` (M1 route, M2 HISTORICAL, L3 x2, L4 scope), `test_s4_consequence_store_postgres.py` (L2).
- Frontend: new `sites/FindingConsequence.tsx`; `sites/financialsClient.ts`, `sites/SiteFinancials.tsx`, `shell/SiteAnalyticsFrames.tsx`, `shell/operatorSiteRoutes.ts`, `test/settled.ts`, `sites/__tests__/siteFinancials.test.tsx`.
- Tools: `tools/s402b_fuel_cost_walkthrough.py`, `tools/s402b-fuel-cost-evidence.mjs`.

## Carries (2a review) status

| Carry | Status | Proof |
| --- | --- | --- |
| M1 closed source | Done | `AUDIT_ONLY`/`SOURCE_CLOSED`; route test `test_m1_a_closed_source_gate_never_presents_an_amount_as_current`; unit gate-passing test |
| M2 HISTORICAL | Done | `test_m2_a_superseded_finding_revision_reads_historical_with_no_current_amount` (superseded via test-scoped model upgrade) |
| L1 401/403/503 | Done | `TestConsequenceRouteCarries` |
| L2 completeness trigger | Done | UNPRICED clone in store test, matched on its own message |
| L3 latest filter, skip | Done | `TestPhase2bCarries::test_l3_*` |
| L4 STALE wording, scope | Done | `recalculation_queued`; `test_l4_*` |
| 3 frontend types/wording | Done | `SiteFinancials.tsx:481` replaced by `FindingConsequence.tsx` |
| 4 walkthrough gate | Done | gate opened by the normal comparison; audit-only shown via `close-gate` |
| 5 Q2 to Architect | Open | batched (questions-2 Q2) |
| 6 no merge before 2b | Satisfied | |

Non-vacuity, each on committed code reverted with `git checkout --`: backend 9/9 killed (M1 branch off: 1 failed; gate not passed: 1 failed; HISTORICAL off: 1; completeness RAISE→NULL: 1; latest filter off: 1; skip off: 1; pending scope off: 1; STALE always "queued": 1; failing store unmapped: 1). Frontend 6/6 killed (bridge table always current: 5 failed; coverage-gap words dropped: 1; pinned never shown: 1; history replaces: 1; demo label dropped: 1; headline ignores currentness: 1).

## Acceptance criteria

| Criterion | Status |
| --- | --- |
| Quantity→price→amount bridge, 0-to-upper range, currency, plain "modelled, not a measured saving" | Met (evidence: priced claims, 1440/390) |
| IDs, digests, formula, `MODELLED_CONDITIONAL` only in disclosure | Met (visible-text UUID scan 0; opened details contain them) |
| Assumptions shows used price/source/SYSTEM actor and selectable earlier price versions; consequence versions | Partly: price versions on Assumptions, consequence versions on Overview linking each exact price version (Q12) |
| Finding → Financials → Evidence → old/new consequence → same FindingRevision, survives reload | Met (evidence round-trip, keyboard Enter, reload, back/forward) |
| Typed absent-source/no-price/quantity/closed-source/pending states | Met (missing, unpriced NO_PRICE, pending, stale, historical, audit-only captured at both widths) |
| Human edit disabled | Unchanged from S4-02a (`G-assumptions-human-edit`) |
| No "Scenario" label; L6 | Met |
| Absent-capability copy via `<MissingClaim>` or itemized | No new absent-capability literal; orphan scan 31 tagged / 12 baselined (unchanged) |
| Ordinary Findings qualifying | 0 of 11: 8 `POWER_MISSING`, 2 `FINDING_NOT_SUPPORTED`, 1 F01-gateway `POWER_COVERAGE_GAP`; positive amount only from authored P01-power (labelled) |
| Owner sees bounded, unpriced, unavailable, pending/historical, old/new at 1440/390 | Walkthrough `.agent/S4-02b-owner-walkthrough.md`; screenshots in `%LOCALAPPDATA%/AssetOps/s402b-evidence/shots` |

## G-05 itemization by manifest element (omitted, not rendered)

- `financials:3#a`, `financials:3#b`: Trade-offs and exclusions panel / cross-option trade-off.
- `assumptions:2#a`: Impact preview.
- `financials` metric cards other than the exposure range: Revenue / service, Asset exposure, Realized savings.
- `financials` second consequence line: maintenance accrual ($0.80 / runtime hour).
- `financials`/`assumptions` Scenarios subtab and "Edit example assumptions" scenario inputs; cash flow, FX, monthly extrapolation (manifest `deferred`).
- `assumptions` Interpretation history "Proposed next version" row (mock-only edit).
- `mini:4#a` stays with S5-01.

## Checks run (actual)

- Focused Postgres (recompute, store, power demo): 26 passed (DB `assetops_s402b3_a_test`); `test_s4_assumption_read_api.py`: 18 passed.
- Full backend: **2049 passed** in 864 s (DB `assetops_s402b3_full_test`, on `f7984fc`; later commits are docs only).
- Frontend: `tsc` clean; vitest 62 files, **1476 passed**; `npm run build` ok.
- `tools/check-all.ps1`: **9/9 guards passed** (one earlier run failed the configuration-persistence guard on `financials/demonstration.py` reading a file; moved to `demonstration_label.py`).
- Producer `tools/s402b_power_cases.py run`: VERIFY PASSED (12 Findings, 31 revisions).
- Walkthrough prepare (evidence and owner DBs): 34 work items, 0 failed; latest: 1 PRICED, 8 POWER_MISSING, 2 FINDING_NOT_SUPPORTED, 1 POWER_COVERAGE_GAP; gate open on both.
- Browser evidence `tools/s402b-fuel-cost-evidence.mjs`: **90/90 claims passed** (priced, missing, historical, pending, stale, old/new, unpriced, audit-only, mock refs at 1440 and 390; non-empty sets measured: counted readings > 0, identifiers present once disclosures open).
- `tools/layout-evidence.mjs http://localhost:5406`: 206 PASS / 28 FAIL, the same counts as recorded at S4-02a; failures are fixture preconditions (legacy file Kobo, no diagram on this store, six-tab claim) not in this slice's surface.

## Known deviations

- Q11 demonstration label is derived from the spec's declared day, not from stored authorship.
- Q12 consequence versions are listed on Overview, not Assumptions.
- Five currentness states (2a Q1 + `AUDIT_ONLY`), not one STALE/PENDING label.
- `PRICE_SPANS_WINDOW` not staged in the walkthrough (tested only, Q14).

## Residual risk

- Each money view runs two reads, each deriving the consequence fresh (2a review "cost per read").
- Evidence acceptance enqueues no work (Architect Q2); a drifted head shows STALE until someone runs `recompute`.
- The worker is a one-shot CLI; no scheduler.

## User-review focus

Owner checkpoint questions 1-6 in `.agent/S4-02b-owner-walkthrough.md`: final money copy, no-amount reasons, the demonstration label and 0/11 ordinary qualification, STALE/PENDING separation, the carried version-1 history item and 390 px tab wrap.
