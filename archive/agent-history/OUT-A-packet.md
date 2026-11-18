# OUT-A review packet: category labels and links

Task `tasks/OUT-A-category-labels.md`. Branch `task/OUT-A-category-labels`, cut from main `287a63a7`, main `cbc32703` merged in at ``8b4c52dc``. Contract: build spec `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md` rev 2 §0, §1.1-1.3, Slice A, "Pre-flight rulings A", addendum 1 and addendum 2. Pre-flight: `.agent/OUT-A-preflight.md`.
Reviewer diff: `git diff 287a63a7..HEAD -- ':!.agent'`, excluding main's own changes after the merge (`git diff cbc32703...HEAD`).

## Outcome delivered
- Pure outcome catalogue and outcome map (`outcome-map/1`). Categories appear on the estate Findings, Portfolio, mini Finding index and detail, cold and EV Finding reads, and the mini Action read. The Portfolio also gets `summary.category_counts`.
- Category pills on the Findings lists (estate, Site, cold, EV). One Affects line on the mini, cold and EV Finding pages and on the ACT-048 pages ("Safeguards checked").
- The Portfolio has four outcome category cards (Grow, Optimize, Protect, Assure) in place of the five value cards.
  - The Grow value "Not available yet" renders through gap `G-portfolio-grow-revenue`.
  - If OPERATING_COST is missing, the Optimize card keeps the unknown wording (addendum 2).
- `tools/measure-mock-panels.mjs --mock <dir>`. Register rows R520-R528.

## Files materially changed
- Backend:
  - `outcomes/{__init__,catalogue,outcome_map}.py`;
  - `estate/{portfolio,index}.py`;
  - `analytics/{finding_index,finding_read}.py`;
  - `adapters/postgres_assessment_store.py`;
  - `actions/service.py`.
- Fixtures, regenerated through write flags:
  - `backend/tests/fixtures/w3/w301-estate-golden.json`;
  - `s6_action_api_contract.json`;
  - `s6_verification_api_contract.json`.
- Backend tests:
  - new: `test_out_a1_outcome_map.py`;
  - extended: `test_s4_finding_api.py`, `test_s4_finding_index_postgres.py`, `test_s6_action_records_postgres.py`, `test_w203_cold_reads_postgres.py`, `test_w206_ev_reads_postgres.py`, `test_w301_estate_api.py`, `test_w301_estate_golden_postgres.py`, `test_w303_portfolio_api.py`.
- Frontend:
  - new: `sites/outcomeCategories.tsx` (CategoryTags, AffectsLine with `subject`, OutcomeGlyph), `sites/outcomes.css`, `sites/componentIcons.tsx`, `estate/PortfolioOutcomes.tsx`;
  - category wiring: `estate/{EstatePortfolio.tsx,estateClient.ts,findingIndex.tsx,estatePortfolio.css}`, `shell/SiteAnalyticsFrames.tsx`, `sites/{ColdAssessmentViews,EvAssessmentViews,EvFindingIndex,SiteAction,SiteFindingIndex}.tsx` and their clients;
  - `ui/gapCatalogue.ts`, `test/panelStructure.ts`.
- Frontend tests:
  - `estatePortfolio`, `estateRoots`, `s404SiteFindingIndex`, `coldFindingIndex`, `coldRoutes`, `evAssessmentRoutes`, `evFindingIndex`, `outcomeCategories` (new), `siteAction`, `siteActionVerification`, `siteFinding`.
- Registry and tools:
  - `frontend/docs/architecture/v69-dependency-registry-pilot.json` (row `G-portfolio-grow-revenue`);
  - `tools/measure-mock-panels.mjs`;
  - `.agent/mock-departure-register.md` R520-R528.
- Five-card tests updated, all in `estatePortfolio.test.tsx`; the pre-flight P-A6 list:
  - `rendersContextFiveCardsPulseAndSelectedRows`
  - `rendersUnpricedCardAndEmptyRisksLensNotAssessed`
  - `appendsOnlyFindingRowsOnLoadMore`
  - `rendersEmptyPendingHistoricalAndSourceConflict`
  - `noLineCardUsesExactShortLiteralFromApiAndFallback`
  - `rendersMeasuredPanelHierarchyAndScrollContainers`
- New Portfolio card tests:
  - `fourCardsInOrderWithIconNameDefinitionAndExactCopy`
  - `protectValueForTwoOneZeroAndNullAndAbsentCounts`
  - `optimizeValueEqualsTheOldOperatingCostValueByteForByte`
  - `optimizeCardStaysInUnknownWordingWhenOperatingCostIsMissing`
  - `assureGapTextForAllSomeOneZeroAndNull`

## Acceptance criteria (spec §A.7)
1. **PASS.** `test_out_a1_outcome_map.py`: 7 passed. The purity test was proven non-vacuous (A1 `c2fdc0f0`), and it is in the full run.
2. Estate Findings pills: mini rows show solid Optimize and outlined Protect. The null-mechanism case shows "Category not mapped". Tests: `estateRoots`, `outcomeCategories`. Capture: PASS (estate case and Kobo replay Findings, Kobo Site Findings on the estate case: solid Optimize + outlined Protect; `.agent/OUT-A-captures/` (README.txt, shots/raw-evidence.json)).
3. GreenHarvest: start-failure shows solid Protect and outlined Optimize; the excursion shows solid Protect only. Tests: `coldFindingIndex`, `coldRoutes`. Capture: PASS (w502 positive, assessed window 2026-10-29 16:00-17:05 UTC: start-failure solid Protect + outlined Optimize; excursion solid Protect only).
4. Depot: the interruption shows solid Grow and solid Protect, with no outlined pill. Tests: `evFindingIndex`, `evAssessmentRoutes`. Capture: PASS (w504 positive: interruption row solid Protect + solid Grow, no outlined pill).
5. Affects line:
   - mini: exactly one, on the overview, evidence and history tabs (`siteFinding`);
   - cold and EV: one, on the overview only;
   - the child-address gap shows none (R527).
   - Capture: PASS (GreenHarvest and Depot Finding pages: exactly one `.oc-affectsline`; the line also lists outlined touched outcomes, e.g. "Also check · Protect asset and capital" (compressor life / charger life), see review focus).
6. ACT-048 overview and verification show "Safeguards checked" with "reliable service, battery and generator life". Tests: `siteAction`, `siteActionVerification`. Capture: PASS (s602b guardrail case, both pages, 1440 and 390).
7. **PASS** in tests. The four cards are in order with icon, name and definition. The Optimize value equals the old operating-cost value byte for byte ("$3.31–$3.97"). Capture: cards in order with icon, name, definition; Grow "Not available yet". Optimize equality not checkable in capture: the estate case has no operating-cost consequence (card reads "No supported value" / "No selected operating-cost consequence"); the byte-for-byte equality is proven in the unit test.
8. **PASS.** The w1 vocabulary scan runs in every touched screen test, and no raw code is rendered.
9. Guards, backend, vitest and golden:
   - check-all: **PASS 11/11** on merged head `8b4c52dc` with main's fixed `tools/check-all.ps1` (no execution-policy override; navigation truthfulness via `tools/check-navigation-truthfulness.ps1`).
   - Full backend `-Tier fast`: **PASS under the coordinator's ruling**, with only the 2 known main failures (below).
   - Full vitest: **PASS** apart from the 3 known main failures.
   - Golden equality: prints equal for all three fixtures (output below).
10. Captures at 1440 and 390, with no page-level horizontal scroll at 390: **PASS**: 24 captures (12 screens x 1440/390) plus v70 mock pairs; scrollWidth == clientWidth at 390 on every capture (390/390); console messages are favicon 404s and one 409 on the Kobo replay `finding-index` (that capture showed no rows; Kobo Site Findings evidence is the estate-case capture).

## Checks run
- **Full backend:** `tools\run-backend-suite-in-container.ps1 -Tier fast`, at `a1733184`, run `20261030-083106-83d548`.
  - Wall 2658 s (44 min). 4 workers, postgres-test.
  - JUnit: `cases=4143 skipped=0 failed=2`. Console: 4141 passed, 2 failed.
  - Accepted by the coordinator as the full backend gate.
- **Full vitest (`npx vitest run`), at `a1733184`:**
  - Run 1 (350 s): 6 failed, 3477 passed. The failures are the 3 known w1f4 tests plus 3 EV load flakes.
  - Run 2 (356 s): 3 failed, 3480 passed (3483). Only the 3 known w1f4 tests failed.
- **EV load flakes** (flakes that passed on rerun): all 3 passed alone (35/35) and in run 2.
  - `evDepth.test.tsx` R347 Site tabs window, "expected '/sites/EV-LAB-001/ev' to be '/sites/EV-LAB-001/ev?from=…'";
  - `evHealthDepth.test.tsx` R347 (same text);
  - `evEnergy.test.tsx` `energy_states_table_loading`, "the store read has not settled".
- **`coldWorkCases.test.tsx`:** the 2 long-text tests that failed in an earlier implementer's full run passed alone (36/36) and in both full runs. They are a load flake, not OUT-A.
- **Focused:** `estatePortfolio.test.tsx` 29/29. `tsc --noEmit` clean.
- **Guards:** check-all 11/11 at `8b4c52dc` (above). Earlier at `3aeda54b`: `check-architecture.ps1` and `check-agent-workflow.ps1` run directly, PASS.
- **Golden equality:** `.venv\Scripts\python.exe .agent/OUT-A-golden-equality.py` (rerun 2026-10-30):
  ```
  equal (raw): backend/tests/fixtures/w3/w301-estate-golden.json  categories keys main=0 new=12
  equal (after normalise): backend/tests/fixtures/s6_action_api_contract.json  categories keys main=0 new=5
  equal (equal except 2 selection_seq leaves): backend/tests/fixtures/s6_verification_api_contract.json  categories keys main=0 new=1
      $.responses.plan.plan.baseline_selection.days[0].selection_seq: main=19 new=27
      $.responses.plan.selection_bindings[0].selection.days[0].selection_seq: main=22 new=30
  ```
  - The normalisation strips exactly `categories` and `selection_seq`.
  - `selection_seq` is a database sequence value taken in the regenerating run's order; it is not a product value.
  - Addendum 1 requires the reviewer to rerun the script.

## Known failures on main (merge gate ignores exactly these, by name)
- Vitest, `src/sites/__tests__/w1f4VerificationStructure.test.tsx`; pre-existing (addendum 2):
  - "W1-F4 C2: Verification keeps the v69 panel structure (verification) > stocked: strip, four cards from the read, panel 1 full width, then Activity and Outcome evidence side by side"
  - "... > historical selection: the exact earlier outcome keeps the same three panels"
  - "W1-F4 C2: the guard is not vacuous on Plan, Evidence and Verification > verification: a planted extra panel before panel 1 fails"
- Backend:
  - `backend/tests/test_w303_selectors_postgres.py::test_portfolio_row_facts_and_verification_ids_match_stored_rows`: "MINIGRID and 'GENERATOR_SUPPORT_CANDIDATE' is None";
  - `backend/tests/test_w303_portfolio_scope_snapshot_postgres.py::test_three_domains_same_window_cutoff_and_full_selection_ids`: "COLDCHAIN and 'COLD_EXCURSION' is None".
  - Both reproduce identically on a detached main checkout at `287a63a7`: run `20261030-091945-a32406`, 11 passed, 2 failed.
  - Cause: CC-R2 `0bcb7f16` began filling `_mechanism`, and these tests still assert None. The coordinator's ruling: they are fixed in a separate round, not in OUT-A.

## Known deviations
- `G-portfolio-grow-revenue` uses `element_ids: ["portfolio:3.grow-card-value"]` and `panel_portion_ids: []`, per addendum 2: the cards are not a registry panel, and panel 3 is the headroom home. No `panels` row was added.
- `G-site-outcome-earlier` was withdrawn by addendum 2. It is not added (OUT-B work).
- `AffectsLine` takes `subject` rather than `variant` (addendum 1, accepted).
- The S6 contracts are proven by the normalised comparison (addendum 1, accepted on three conditions, all met above).
- Register R520-R528 (D1/D4/D5 per row).
- Captures: part 1 (s602b) at product `a1733184`, part 2 (w502/w504) at `8b4c52dc`; the main merge carried no product code (tools/docs only), so both describe the same product. Superseded captures (run 1 Portfolio 1440 not ready; run 4 GreenHarvest list on the unassessed window) were recaptured. All producer DBs were dropped and servers stopped by PID (README).

## Residual risk
- Most acceptance claims about cold and EV pills rest on unit fixtures plus the producer captures. No combined three-domain demo estate exists (D1 R535); the Portfolio capture is mini-only.
- The full vitest suite has load-sensitive EV and cold tests that flake under full parallel load.

## User-review focus
USER_REVIEW_REQUIRED: false for merge. A fresh independent review gates the merge; the owner sees the slice in the post-sprint walkthrough. Focus areas:
- pill solid/outlined semantics;
- the Portfolio card copy (R524, R528);
- the Optimize missing-card wording;
- the Finding-page Affects line's outlined "Also check" pills for touched outcomes (cold and EV), which no §A.7 item names.
