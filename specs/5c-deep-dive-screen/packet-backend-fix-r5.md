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
  backend/tests/test_5c_deep_dive_postgres.py`: TEST9_RESULT.
- Plants (each applied to `view.py`, run on the view file, reverted with `git checkout`):
  - P-a `or Decimal(0)` restored: `2 failed, 180 passed` (`test_bars_world_x_no_share_no_bar_no_word`,
    `test_bars_gap_zero_no_share`).
  - P-b L9's card word restored: `7 failed, 175 passed` (`test_4_i_nothing_compared`,
    `test_4_i_currency_card_word_beside_no_figure`, `test_bars_world_x_...`, `test_16_...[X|nothing|subset|two]`).
  - P-c bar from the rounded share (`(e / gap * 100).quantize(1)`): `3 failed, 179 passed` (test 3, `test_4_h`,
    `test_bars_vectors[V2]`).
- `python3 tools/checks/statement_catalogue.py`: `OK statement catalogue: load, coverage, legacy, scan (6 adopted),
  keys, imports` (exit 0).
- check-all (fast): CHECKALL_RESULT.
- Layout evidence: not run (backend only; no page changed).

## Known deviations

- KD1 `heading_evidence` (used by the card word, `big()` and the headline) now reads only the steps with an effect,
  the ones the heading's sum adds. Class test 16 found, before this change, World "subset"'s Optimize card serving
  "−KES 730.00" with `word` "Not available yet": O&M and staff have no figure (KES and USD), so their NOT_AVAILABLE
  evidence was the weakest. D-5C.26 requires a present figure's word to be §2.4's word, never "Not available yet". A
  is unchanged (every step has an effect). Architect to confirm.
- KD2 a gap of exactly 0 with a non-zero rest raises `StatementError('REQUIRES_FAILED', 'deep_dive.tile_rest',
  'offsets')` in `tiles()` (pre-existing on main, outside §11). The gap-0 share case is therefore a `shares()` vector
  on a stub view, not a whole payload. Needs a ruling for the gap tile's rest line at gap 0.

## Residual risk and review focus

- `bar` effect uses the step row's currency equal to R's; World X has none (R's currency None). The ruling's "row's
  currency is not R's" case has no world of its own beyond X.
- Review focus: D-5C.26 (every slot through `figure_word`, KD1), D-5C.27 (bridge_bars maths against §3.2, the
  `100 - L` cap with the unrounded L, A's literal), D-5C.28 (no share at None or 0).
