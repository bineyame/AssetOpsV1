# Review packet: WALK1-fix-suite

Branch `task/WALK1-fix-suite` from main `7149022b7`. Fix commit `35db0a8cd`.
Input: full backend suite OPS-03 `20261102-193833-e96c53` on main `4596f633f`, with 4 failures and 4816 passing.

## Root cause (failures 1-3)

This is not a product regression and no WALK1 merge caused it. It is a time bomb in a test fixture that went off on
2026-11-02 at 11:00Z.

- `tools/s602b_test_scoped_cases.py::publish_price_v1` published diesel price v1 through a plain
  `PostgresAssumptionStore(url)`. The revision's `recorded_at` was therefore the server's real `clock_timestamp()`.
- The cost check runs inside `actions/verification.py::_cost_check`. It reads the price as known at the evaluation's
  pinned clock: `known_at = self.clock()`, with `ev.CLOSED` = 2026-11-02 11:00Z, plus 1 h for `verified`. It does
  this through `composition.price_selection` -> `snapshot(..., recorded_at=known_at)` -> `recorded_at <= :c`.
- Until real time passed 2026-11-02 11:00/12:00Z, the wall-clock price was recorded before the pinned cutoff and the
  tests passed. The OPS-03 run started after that, so the price was "not yet known" at the cutoff. The result was
  `select_window_price` -> NO_PRICE, then `PRICE_MISSING` and UNAVAILABLE. In the e4 read-back this shows as "no
  diesel price covers both hours". The product behaviour is correct, because a price recorded after the cutoff must
  not be used.

## Bisect evidence

All runs were on `assetops_walk1g_test`, using the worktree's own code (PYTHONPATH in Windows form, `assetops_backend`
confirmed to load from `AssetOpsV1-w1g`).

| Revision | e3 result |
|---|---|
| `7149022b7` (main, WALK1-5) | 2 failed, 2 passed |
| `daa523b29` (WALK1-2, before WALK1-1/3/3b/4) | 2 failed, 2 passed (same two) |
| `35db0a8cd` (fix) | 4 passed |
| `35db0a8cd` with only the fixture files reverted to the parent | 2 failed, 2 passed |

The failure exists before every candidate merge and flips on the fixture alone, so WALK1-3, 3b and 4 are cleared. An
earlier bisect run at `253d6e8c2` also failed, but it loaded the main checkout's backend because the PYTHONPATH was
in POSIX form, so it is not counted.

**WALK1-4 identity gate reconciled.** The demo build publishes prices through `tools/demo_combined_kobo.py::publish_price`
with `test_recorded_clock_override` at a story instant. Its trial cost check never depended on the wall clock, so
"identical (0/0 no improvement)" on both sides is a genuine priced reading, not UNAVAILABLE. Only the test-scoped
s602b fixtures had the bug.

## Fix

- `publish_price_v1(url, recorded_at)` now records through the existing `test_recorded_clock_override` seam (the
  same one `demo_combined_kobo`/`demo_combined_ev` use, which is outside the package, so the
  `test_demo_a0_assumption_clock_seam` guard is unaffected). `recorded_at` is required, so no caller can fall back
  to the wall clock.
- The three callers pass `runner.now`, the case clock after the Finding steps and before any evaluation. This
  matches the documented "published after the Finding cases and before any evaluation". The callers are
  `backend/tests/out_e_trial_child.py`, and the s602b `verified` and `estate` cases.
- No product code changed and no assertion was weakened.

## Failure 4

`test_walk1_productive_producer_postgres.py` compared the whole +20-day property map to the +26 min snapshot. The
WALK1-4 +27 min roles-4 change adds `renewable-retained-margin` (ac-bus) and `pv-available-uncertainty`
(pv-inverter). The test now checks four things at +20 days:
- the same components exist;
- the supply-use projection is exactly mill/res/clinic;
- every property declared at +26 min is present with its value;
- any extra keys are limited to those two margins.

The intent is kept: the declaration carries forward to the story days.

## Checks

- e3 `test_out_e3_trial_comparison_postgres.py`: 4 passed (76 s).
- `test_out_e4_readback_postgres.py`, `test_walk1_productive_producer_postgres.py` and
  `test_walk1_productive_price_postgres.py`: 5 passed.
- e3 again, plus `test_out_e2_trial_comparison.py`, `test_out_e4_readback.py`,
  `test_walk1_ev_tariff_producer_postgres.py`, `test_walk1_objective_min_days_postgres.py`,
  `test_walk1_4_mini_binding_lineage.py`, `test_walk1_3b_target_progress.py`, `test_walk1_productive_sales.py`,
  `test_walk1_5_solar_window.py` and `test_demo_a0_assumption_clock_seam.py`: 109 passed.
- `test_out_b4_board_postgres.py` (the other s602b consumer): 5 passed.
- `tools/check-all.ps1`: 12/12 PASS, exit 0. The worktree uses junctions for `.venv` and `frontend/node_modules` to
  plan2's, and both are ignored.
- The full backend suite was not rerun.

## Residual risk

- Other tests may pin a clock in the fictional past or future and also publish through the wall clock. A quick grep
  found only this fixture among price publishers. Other wall-clock writers read at a pinned cutoff were not audited.
- The s602b UI capture cases (`verified`, `estate`) now record the price at `runner.now` rather than real time. The
  `verified` and `estate` reads are pinned at or after `runner.now`, so the price stays visible to them.
