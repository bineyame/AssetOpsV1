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

Next: 1b
