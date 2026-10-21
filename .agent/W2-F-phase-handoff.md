# W2-F phase handoff

Branch `task/W2-F-structural-fixes` (from main `7cfcb751`). W4-03 merges before W2-F; `navigation-truthfulness.ps1`
and the unavailable-tab multiset are untouched (unit 4, after W4-03 is on main).

## 1a: cold backend truth (H1), commit `8028d57d`

Landed (`backend/assetops_backend/analytics/cold_site_reads.py`):
- `COOLING_TEXT` (~:77): `LIMITED` = `Cooling recovery is not established by the selected start chain.`; no `SUPPORTED`
  key (S2). New `COOLING_LIMITATION`, `PRODUCT_LIMITATION` (:84-86), exact S1 text.
- `_capabilities` (`chain_contradictory`, ~:462): cooling CONTRADICTORY / LIMITED (selected chain) / UNAVAILABLE (no
  chain); product CONTRADICTORY (selected excursion assessment state) / else UNAVAILABLE. `PROVED_LEVELS` removed
  (unused). Claim limitation set at ~:483.
- `evidence()` (~:411-417): `selected_excursion_present` (S5) = `bool(exc.result.excursions)`; `false` with no
  selection or no selected excursion analytic. Frontend type/consumer is unit 1b.

Tests (`backend/tests/test_w204_cold_reads.py`): `test_run5_exact_copy` pins new copy; S3 supersessions in
`test_capability_needs_qualifying_points`; no-selection flag in `test_missing_probe_and_empty_window`; new
`test_w2f_recovery_and_exposure_capability_vectors` (pure, `_capabilities(None, snap)`) and
`test_w2f_recovery_and_exposure_truth_across_selected_reads[excursion|normal]` (replay; same revision IDs, window,
`known_at` across Overview/Evidence/Backup).

Checks: `test_w204_cold_reads.py` 21 passed (Postgres `w2fa_test`, since dropped). Non-vacuous: cooling predicate
set back to `SUPPORTED` fails the vector test; reverted via `git checkout`. `check-all.ps1`: all 11 guards passed.

Readings (no ruling requested; flag if wrong):
1. "selected chain/step is CONTRADICTORY" = any selected chain result or any chain step CONTRADICTORY (W2-03 only
   ever marks `START_RESULT`; previously only a COMPRESSOR step counted).
2. Claim limitation is carried on every non-CONTRADICTORY state of the two claims (LIMITED and UNAVAILABLE), so 1b
   never needs the `Nothing required for this claim` fallback; CONTRADICTORY keeps the analytic limitations.
3. Product CONTRADICTORY keeps the existing predicate (selected excursion assessment `state == CONTRADICTORY`).
4. S5's flag is built here because S5 assigns it to unit 1a, though the 1a read index omits S5.
5. Cooling SUPPORTED text removed from `COOLING_TEXT` rather than kept unreachable.

Open for 1b: type and consume `selected_excursion_present`; all frontend copy (Overview `Recovery comparison not
assessed`, Evidence missing column, Financials rename). Frontend mocks still carry old cooling copy.

## 1b: cold truth UI (H1 S1/S2/S5/S7/S8/S12, N0/M4, M6, M7/N6, cold M13), commit `f3ccb41c`

Landed:
- `coldSiteClient.ts`: `ColdEvidenceRead.selected_excursion_present: boolean` (S5).
- `coldSiteViews.tsx`: Evidence `What is missing` for cooling/exposure = missing roles, then capability `limitation`,
  never `Nothing required` (S1); exposure appends `Required basis: ...` (`PRODUCT_REQUIRED_BASIS`). Stock prompt and
  `Next evidence not identified` keyed to `selected_excursion_present` (`excursionPresent`). Overview cooling chip has
  no SUPPORTED mapping (S2); money card adds `data-cold-money-basis` `Consequence basis: ...` (S8). Financials tile and
  basis label `Chamber thermal exposure`, row th `Chamber thermal exposure · Consequence basis: ...`, basis note
  `data-cold-thermal-basis-note` (S7/S8). `coldAssumptionRows` shared by Financials and Assumptions (M7/N6).
- `coldFormat.ts::degreeMinutes` (open upper -> `upper bound not established`; null -> `Not assessed`).
- `ColdAssessmentViews.tsx`: panel 3 `Claim boundary` (N0); Temperature exposure card and excursion Finding labelled
  `Observed excursion estimate` (S8); `FindingStatus` = lifecycle, `Confidence: {claimWord}`, `Selected source: ...`.
- `v69PanelTitles.ts`: `temperature:3` override and deviation-18 comment removed.
Tests: `coldRoutes.test.tsx` `w2f_temperature_claim_boundary_title` (loaded/none/refused), `w2f_temperature_bound_is_labelled`,
`w2f_finding_strip_confidence`, `w2f_backup_recovery_parity`; `coldSiteViews.test.tsx` `w2f_recovery_and_exposure_copy`,
`w2f_stock_prompt_follows_selected_excursion`, `w2f_consequence_bound_is_labelled`, `w2f_assumption_rows_match`.
Checks: cold files 50 + 51 passed; tsc clean; full frontend 2420/2421 - one failure in untouched
`s404SiteFindingIndex.test.tsx` ("changing the dates", got 2026-10-25), passes 37/37 alone (load flake);
check-all 11/11. Non-vacuous: S5 prompt reverted to the capability predicate fails `w2f_stock_prompt...`; reverted.

Readings (flag if wrong):
1. **Vocabulary glosses added** (`productVocabulary.json` top-level `glosses`): exact `Claim boundary` and exact
   `Ordered compressor running after the interruption`. Both mandated texts hit T028 terms `claim`/`running`; glosses
   are exact-phrase, so the words stay flagged elsewhere. Reviewer should confirm this is acceptable vs a ruling.
2. Contradictory cooling with no limitation shows `Coverage or claim basis incomplete`.
3. Currency label comes from the unit-value item's `currency` (else any item's); `No assumption in use` note only when
   all three rows are `Not declared`.
4. Temperature card value is the bound; its note carries `Observed excursion estimate`.
5. Cold Finding refused state unchanged (existing page refusal; no strip), since S12's neutral refused strip is EV.

Next: 2
