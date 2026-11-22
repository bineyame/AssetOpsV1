# 5c backend fix, rev 4 (D-5C.26 to D-5C.28): review packet

Task: spec `spec.md` rev 4 §11 "Backend fix" (about 0.5 unit). Branch `fix/5c-backend-r5` off main `4b13c0afe`, worktree
`/opt/assetecon/AssetOpsV1-5cfix`. Not merged. `USER_REVIEW_REQUIRED`: the spec's flag is true for the screen; this
backend fix changes served words, shares and adds bar positions the owner sees only through the screen fix, so the
owner's look belongs to the screen fix's walkthrough. The review gate is a fresh reviewer (§11 item 6).

## Outcome

A figure slot with no figure serves `word` null (never "Not available yet"); no share and no "Offsets it" without a
gap; each bridge step serves its bar and the bridge its scale as track percentages, so the screen fix draws the
mock's waterfall with no arithmetic (D-5C.2 stands).

## Files

- `backend/assetops_backend/deep_dive/view.py`: `bridge_bars` (module level, pure); `_View.figure_word`,
  `_View.heading_word`; `shares()` early return; steps gain `bar` (after `sites`), `bridge` gains `scale` (after
  `totals`); L9's card line removed; `heading_evidence` reads the steps its sum adds (see Known deviations).
- `backend/assetops_backend/deep_dive/words.py`: `word(..., currency: str)`; `NO_CURRENCY` deleted.
- `backend/assetops_backend/deep_dive/tables.py`: `TONE_LOWERS`, `TONE_RAISES`, `BAR_MIN_WIDTH`, `BAR_PLACES`.
- `backend/tests/deep_dive_worlds.py` (new): `in_kes`, `gone`, `world_h()`, `world_x()` (patch applied and undone
  inside the call; the view tests' module is imported inside the functions to avoid a cycle).
- `backend/tests/test_5c_deep_dive_view.py`: rev 4 tests; the 4 i currency worlds' patches lifted to module-level
  functions (`CURRENCY_WORLDS`) so class test 16 runs them; `_in_kes`/`_gone` now imported from the worlds module.
- `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json`: A's `scale` and four `bar`s, by hand.

## Acceptance, item by item (§11)

1. `shares()` returns `{}` when R's effect is None or 0; `or Decimal(0)` gone (and the `gap == 0` branch with it).
   Tests: `test_bars_world_x_no_share_no_bar_no_word`, `test_bars_gap_zero_no_share` (shares vector, gap 0 and None).
2. `figure_word(value, currency, ev, origins)`: None when value or currency is None, else `W.word`. Used for tiles[0]
   (R.actual), tiles[1] (R.effect), steps (row absent: None), drivers, Grow/Optimize cards (`heading_word`), cash
   (root.actual) and the headline's evidence (Nones dropped). Test: `test_16_word_null_iff_figure_absent` over A, B,
   D, G, H, X, nothing, subset, all_kes, two, sides; `test_4_i_currency_card_word_beside_no_figure` on `world_x()`
   asserts `word` None; `test_4_i_nothing_compared` now asserts None for the gap tile and both cards.
3. `bridge_bars` per §3.2, `prec=34`, half even, two-place strings. Key orders asserted in test 3. Schema unchanged.
   A: revenue `{"0.00","11.38",lowers}`, fuel cost `{"11.38","88.62",lowers}`, O&M null, staff null; scale
   `{"0.00","100.00"}`. H equals A (`test_4_h_kobo_litres`, which also checks `world_h() == view("H")`). V1-V6:
   `test_bars_vectors[V1..V6]`.
4. Fixture edited by hand (16 lines added); test 3 compares the whole payload to it.
5. Worlds module as above.
6. Tests listed; plants below.

## Checks (revision `0d402e030` for code; docs commit on top)

- Focused: `pytest tests/test_5c_deep_dive_view.py tests/test_5c_deep_dive_api.py tests/test_5b_*.py tests/test_3a7_*.py`
  (non-postgres): `379 passed, 1 skipped, 1 warning in 8.08s` (wall 9.1 s). View file alone: `182 passed`.
- Test 9: `bash tools/heavy-slot.sh --db --wait-seconds 3000 -- pwsh -NoProfile -File tools/run-host-tests.ps1 --
  backend/tests/test_5c_deep_dive_postgres.py`: `2 passed, 2 warnings in 9.70s` (exit 0; 692 s wall, most of it waiting for the db-job lock).
- Plants (each applied to `view.py`, run on the view file, reverted with `git checkout`):
  - P-a `or Decimal(0)` restored: `2 failed, 180 passed` (`test_bars_world_x_no_share_no_bar_no_word`,
    `test_bars_gap_zero_no_share`).
  - P-b L9's card word restored: `7 failed, 175 passed` (`test_4_i_nothing_compared`,
    `test_4_i_currency_card_word_beside_no_figure`, `test_bars_world_x_...`, `test_16_...[X|nothing|subset|two]`).
  - P-c bar from the rounded share (`(e / gap * 100).quantize(1)`): `3 failed, 179 passed` (test 3, `test_4_h`,
    `test_bars_vectors[V2]`).
  - P-d the crash restored (rest line at gap 0): `1 failed, 182 passed` (`test_bars_gap_zero_whole_payload`).
- After KD2 (at `0b8210ac6`): focused `380 passed, 1 skipped, 1 warning in 6.71s`; view file `183 passed`; test 9
  superseded by the PF1 line below.
  - P-e PF1 undone (registry name as the unit): `2 failed, 183 passed` (`test_4_h_driver_detail_kwh`,
    `test_1_driver_units_have_words`).
- After KD2 and PF1 (at `9280e866f`): focused `382 passed, 1 skipped, 1 warning in 6.66s`; view file `185 passed`;
  catalogue OK; test 9 `2 passed, 2 warnings in 8.74s` (exit 0, 644 s wall with the db-lock wait); check-all (fast, at `16cb7fb5f`) `All 42 guards passed (blocking; 0 advisory, 0 warned).` (142.3 s).
- `python3 tools/checks/statement_catalogue.py` (before and after KD2): `OK statement catalogue: load, coverage, legacy, scan (6 adopted),
  keys, imports` (exit 0).
- check-all (fast, through the slot, at `435a71c87`): `All 42 guards passed (blocking; 0 advisory, 0 warned).` (142.8 s; estate and pool self-tests skipped as unchanged).
- Layout evidence: not run (backend only; no page changed).

## Known deviations

- KD1 `heading_evidence` (used by the card word, `big()` and the headline) now reads only the steps with an effect,
  the ones the heading's sum adds. Class test 16 found, before this change, World "subset"'s Optimize card serving
  "−KES 730.00" with `word` "Not available yet": O&M and staff have no figure (KES and USD), so their NOT_AVAILABLE
  evidence was the weakest. D-5C.26 requires a present figure's word to be §2.4's word, never "Not available yet". A
  is unchanged (every step has an effect). **Accepted** (coordinator for the Architect, owner away, 2026-11-21).
- KD2 **fixed in this round** (coordinator ruling, 2026-11-21): a gap of exactly 0 with a non-zero rest raised
  `StatementError('REQUIRES_FAILED', 'deep_dive.tile_rest', 'offsets')` in `tiles()` (pre-existing on main). Ruling: at
  gap 0 the gap tile has no rest line (nothing to offset); value and word per D-5C.26. `tiles()` adds the rest line
  only when R's effect is not None and not 0 (commit `0b8210ac6`). Test `test_bars_gap_zero_whole_payload` builds the
  whole payload through the view (lead world gap 0.00, steps +5.00 and -5.00): it renders, the gap tile's lines are
  only "Grow +$5.00 · Optimize −$5.00", no "Offsets it", no share, no bar, no scale.

- PF1 **fixed in this round** (DDR finding, coordinator, 2026-11-21): with the emulated `budget.csv` loaded the route
  answered 500, `StatementError VOCABULARY_UNKNOWN deep_dive.driver_detail actual_quantity` (`words.py` `detail`,
  from `view.py` `driver_detail`; on main). Cause: `driver_detail` passed the registry's dimension name (`KWH`) as
  the unit, and the SC-1 `unit` vocabulary's key is `kWh` (`L` matched by chance). Reproduced directly
  (`delivered_kwh` quantity and `tariff` price both raised) and in a view world. Fix: `tables.UNIT_WORDS` (`KWH` ->
  `kWh`, `L` -> `L`), used by `driver_detail`; no vocabulary or baseline entry added (commit `9280e866f`). Tests:
  `test_4_h_driver_detail_kwh` (World A with revenue's `delivered_kwh` 8,550 against 9,000 and a `tariff` row: the
  payload renders, "Actual 8,550 kWh · Target 9,000 kWh", and the price form "Actual $0.27 per kWh · Target $0.25 per
  kWh"); `test_1_driver_units_have_words` (every single-dimension unit reachable from the MINI_GRID roots has a
  vocabulary word and renders). Not re-run on the DDR rehearsal database itself (not touched by this brief).

## Residual risk and review focus

- `bar` effect uses the step row's currency equal to R's; World X has none (R's currency None). The ruling's "row's
  currency is not R's" case has no world of its own beyond X.
- Review focus: D-5C.26 (every slot through `figure_word`, KD1), D-5C.27 (bridge_bars maths against §3.2, the
  `100 - L` cap with the unrounded L, A's literal), D-5C.28 (no share at None or 0).
