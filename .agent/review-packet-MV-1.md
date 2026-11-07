# Review packet MV-1: mill dollars on the verdict page (FUEL-1 lane 1)

- Ruling: `.agent/build-sheet-FUEL-1.md` §2 (main `f63b46a01`). Branch `task/FUEL-MV1-mill-dollars`, worktree
  `C:\Users\assef\Bineyame\AssetOpsV1-mv1`, cut from main `f63b46a01`. Test DB `assetops_mv1_test` (127.0.0.1:55432,
  repo credentials from `backend/README-db.md`; run-owned `assetops_mv1_pt*_test` clones dropped by the harness).
- Commits: `4791d7b27` build (backend, frontend, MILL-3b row, L0 + vitest), `a7f829240` L2 tests, then this packet.
- Pre-flight: every anchor in §2.1/§2.6 matched the code at `f63b46a01`; no questions, no stop.
- Size: about 0.4 unit (under S5's 0.75).

## Outcome delivered

A VERIFIED mill verdict now carries `value`. It is the estimated-sales line at the declared productive-use price,
worked out from the stored shown means, plus the cost line. Every other state carries `value: null`. The page shows
both server strings under the verdict lines, before the table.

Shown dollar line (demo figures: means 42.00 → 110.00, v1 0.25 USD, 3 + 3 days; reproduced on L2 through the composed
port, `per_day == "17.00"`):

> About 17.00 USD a day more in estimated sales to productive users: (110.00 − 42.00) kWh a day × your declared 0.25 USD per kWh, on 3 fully checked days before and after the change
>
> No cost is recorded for this change

The measurements, all computed from the inputs and never typed from a run:
- per_day = (110.00 − 42.00) × 0.25 = 17.00
- before = 42.00 × 0.25 = 10.50
- after = 110.00 × 0.25 = 27.50

## Files materially changed

| File | Change |
|---|---|
| `backend/assetops_backend/financials/fuel_cost.py` | `select_window_price(..., *, key=PRICE_KEY, unit=PRICE_UNIT)`; the unit line uses them. Nothing else |
| `backend/assetops_backend/financials/composition.py` | `build_productive_price_selection(database_url)` (snapshot at `known_at`, `key=PRODUCTIVE_PRICE_KEY`, `unit=unit_for(...)`); added to `__all__` |
| `backend/assetops_backend/actions/verification.py` | `VerificationPorts.productive_price`; `domain_summary` passes `price=` only for a stored VERIFIED outcome (`_mill_price`: local midnight of the first baseline day to the end of the last later day, `known_at = recorded_at`) |
| `backend/assetops_backend/actions/composition.py` | wires `productive_price=build_productive_price_selection(database_url)` |
| `backend/assetops_backend/actions/verification_families.py` | the §2.2(e) constants verbatim, `_price_text`, `mill_value`, `summary_wire(..., price=None)` with `"value": None` in `head` |
| `frontend/src/sites/millVerificationClient.ts` | `MillValue`; `MillVerification.value`; parser: absent/null → null, bad object → parse error |
| `frontend/src/sites/SiteMillVerification.tsx` | two `<p>` after the lines (`data-mill-value`, `data-mill-cost`); header MOCK DEVIATION MD-FUEL-MV1-1; R700 line byte-equal |
| `tools/demo_combined_finish.py` | `@row("MILL-3b")` after MILL-3 |
| `tools/demo_combined_rows.py` | pure `productive_price_v1(path)` and `mill_value_page(page, price)` (the row's checks, L0-testable) |
| tests | `test_ch9b3_mill_verdict.py` (+5, 1 extended), `test_s4_fuel_cost.py` (+1), `test_ch9b3_mill_verdict_postgres.py` (+2), `test_demo_combined_finish_rows.py` (+1), `millVerification.test.tsx` (+3, fixture gains `value: null`) |

## Acceptance (§2.4) criterion by criterion

| Criterion | Status | Evidence |
|---|---|---|
| L0 1: PRICED 42.00/110.00 @0.25 → 17.00 / 10.50 / 27.50, text = `VALUE_TEXT.format(...)` | Met | `test_verified_priced_value_reads_the_shown_means_times_the_declared_price` |
| L0 2: reproduce-by-hand grid | Met | `test_value_reproduces_by_hand_over_a_grid_of_means_and_prices` (means 0.01/41.99/42.00/109.99/110.00 × prices 0.25/0.255/1/0.1) |
| L0 3: UNPRICED NO_PRICE, PRICE_SPANS_WINDOW, PRICE_CONFLICT (→ OTHER), None (→ PRICE_UNREADABLE) | Met | `test_unpriced_value_names_why_and_keeps_the_cost_line` |
| L0 4: null for INEFFECTIVE, INCONCLUSIVE, NOT_JUDGED, NO_PLAN, equal-means guard | Met | `test_value_is_null_for_every_other_state_and_for_a_guarded_verified` (also lower-means, missing mean, 2 days) |
| L0 5: every state has `value`; existing keys unchanged | Met | extended `test_summary_wire_reads_the_stored_outcome_and_the_not_judged_state` pins full key order for the stored, NOT_JUDGED and NO_PLAN bodies (S1 not triggered) |
| L0 6: `_price_text` parity | Met | `test_price_text_matches_the_site_outcomes_rule` |
| fuel_cost: productive key/unit PRICED; default call still PRICE_UNIT_MISMATCH | Met | `test_the_productive_key_and_unit_select_a_productive_revision_and_the_default_still_refuses_it` |
| L2: v1 published → PRICED with its revision id | Met | `test_mv1_a_verified_outcome_reads_the_declared_productive_price_as_known_at_its_recording` (S2 not triggered: the snapshot returns v1 at `recorded_at`) |
| L2: valid_from after the first baseline day → UNPRICED / PRICE_SPANS_WINDOW | Met | `test_mv1_a_price_starting_inside_the_window_reads_unpriced_spans_window` |
| Frontend: PRICED renders both lines; UNPRICED renders text + cost; null renders neither; parser accepts absent `value` | Met | `millVerification.test.tsx` 3 new tests; the vocabulary scan runs clean in the PRICED and UNPRICED states |
| MILL-3b row + L0 self-test | Met (row runs at E3) | `test_mill3b_recomputes_the_value_from_the_shown_means_and_the_v1_fixture_price` |
| Guards A, W, N, V, M, hard-wiring count not raised | see Checks | |

## Non-vacuity (mutate, run, `git checkout --`)

The build was committed first. One edit per mutation:
- `per_day × 1.001` fails L0 1, L0 2 and the L2 priced test.
- `lo` from the later days fails the L2 span test.
- `select_window_price` ignoring the `unit` keyword fails the fuel_cost test.
- Dropping the cost `<p>` fails both new render tests in vitest.
- Removing MILL-3b's per_day assertion, run alone, fails its self-test.

All were reverted. `git status` was clean afterwards.

## Checks run (scoped; no full suite, no prepare, no baseline build, no `test_demo_combined_postgres`)

- Backend, at `a7f829240`: `test_ch9b3_mill_verdict.py`, `test_s4_fuel_cost.py`, `test_demo_combined_finish_rows.py` and `test_ch9b3_mill_verdict_postgres.py` (on `assetops_mv1_test`), plus the adjacent `test_walk1_productive_sales.py` and `test_ch9b1_origin_readers.py`. Result: 128 passed, 0 failed, 0 skipped (47 s).
- Frontend: `millVerification.test.tsx` 10 passed; `tsc --noEmit` exit 0.
- Guards, run one at a time with `ASSETOPS_GUARD_PYTHON` set:
  - A `check-architecture.ps1`: passed (298 s).
  - N `check-navigation-truthfulness.ps1`: passed (30 s).
  - V `node --test tools/checks/test_mock_deviation_labels.mjs`: 14/14 passed.
  - M `missing-claim-scan.mjs`: passed (42 tagged, 10 baselined, ceiling 16).
  - `frontend-hardwiring.mjs`: passed, totals unchanged (api 12, href 24, lit 70, cmp 51, code 3).
  - W `check-agent-workflow.ps1`: passed, after the packet commit.
  - S3 not triggered: no guard rejected a §2.2(e) literal.
  - A and N were first launched through Git Bash `powershell -File`, which the execution policy refused. Both were rerun through the PowerShell tool, without `-ExecutionPolicy`.

## Known deviations

- **KD-1 (file list).** The MILL-3b checks live in `tools/demo_combined_rows.py` as two pure functions. The finish row calls them. This keeps the row testable without a database, the same pattern as MILL-3's `mill_page`. The ruling lists only `T/demo_combined_finish.py` (one row).
- **KD-2 (parser).** The parser also requires `value.state` to be PRICED or UNPRICED, besides string `text` and `cost_text`. This is stricter than §2.3 states, but it matches the declared type.
- **MOCK DEVIATION MD-FUEL-MV1-1** (`SiteMillVerification.tsx` header). v70 has no mill verdict page (D1, R700), and the value and cost lines are new. There is a single basis, so v69 `:482` holds.

| Id | Surface | Mock | Built |
|---|---|---|---|
| MD-FUEL-MV1-1 | Mill verdict page | no page in v70 (D1, R700) | value line + cost line under the verdict lines, same `<p>` as the lines, no new CSS |

## Residual risk

- The L2 tests read through `build_productive_price_selection`, which the service holds as a port. The `actions/composition.py` wiring line itself is exercised only at E3 (MILL-3b) and in the served app.
- MILL-3b has not run on a built dataset. It runs at E3.

## User review

Not required. §2.6 says "Owner: nothing to decide". Q4 (mill cost) is now answered on main at `8032040e8`: "No cost recorded (Recommended)". The page says "No cost is recorded for this change". That is `VALUE_COST_TEXT` verbatim, so nothing changes. Drop `assetops_mv1_*` after merge.
