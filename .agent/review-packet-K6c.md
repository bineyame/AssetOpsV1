# Review packet: DIESEL-K6c (Assure fuel count, summary claim count, 5 guard modules)

Ruling: `.agent/build-sheet-DIESEL-1.md` §9u (DIESEL-1-R3u, main 886341aff), items U2 (A1), U3 (L2), U6 (guard modules) and §9u.2 order.
Branch: `task/DIESEL-K6c-assure-fuel-count` from main 886341aff. Build commit: 5a7192741.

## Path fix (review-K6c)
M1: `test_k6c_assure_fuel_count.py` inserts `tools` on `sys.path` at module level (as `test_ch5c2_clock_guard.py` does),
so `checks.chain_coherence` imports without `tools` on PYTHONPATH; run alone it passes 8/8. L1: the stale
`_verified_results` comment in `site_outcomes/read.py` now says no production reader remains.

## Outcome
- **U2 (A1).** `site_outcomes/mini.py:572-574`: the Assure headline count adds `sum(1 for f in fuel if f.outcome == "VERIFIED")`. `site_outcomes/read.py:521-524` `_verified_results` adds the same term over `comp.facts.fuel_verdicts` (cold/EV facts default `()`, `board.py:338`). Kisiwa with ACT-004 VERIFIED reads "1 verified result".
- **U3 (L2).** `read.py` `_summary`: `verified_result_count` is `None if counted is None else counted.claims[VERIFIED_RESULTS].value` (`VERIFIED_RESULTS` was already imported). The per-board `verified +=` sum is removed; `verified_read` is kept for `verified_sites_unread` (unchanged).
- **U6.** `config/chain/stored-composer-modules-v1.json`: `actions.fuel_verification`, `actions.verification_families`, `financials.assumptions`, `financials.composition`, `financials.fuel_cost_v2` inserted in sorted (byte) order. `test_ch5c2_clock_guard.py` passes with them listed (no hit, no allowlist edit).

## Files
- `backend/assetops_backend/site_outcomes/mini.py` (1 line + comment)
- `backend/assetops_backend/site_outcomes/read.py`
- `config/chain/stored-composer-modules-v1.json`
- `backend/tests/test_k6c_assure_fuel_count.py` (new)
- `backend/tests/test_mb1_opportunity_board.py` (helper parity + new board-service fuel test, R3u item 4)
- `backend/tests/test_out_b4_read.py:254-256` (R3u item 6: summary count None without a reader; `verified_sites_unread` assert kept)

## R3u U3 test list, item by item
1. Mini compose, one VERIFIED fuel verdict, no trial/mill VERIFIED: headline "1 verified result", one FUEL_VERDICT verified entry, `_coh17_a1` returns [] - `test_1_...`.
2. Fuel verdict None (pending) / INEFFECTIVE / INCONCLUSIVE not counted, A1 still passes - `test_2_...` (3 params).
3. VERIFIED trial + mill + fuel: "3 verified results", A1 passes - `test_3_...`.
4. Board `_verified_results` includes the fuel verdict, equals the headline, one more than the mill alone - `test_mb1_opportunity_board.py::test_the_board_service_verified_results_includes_the_fuel_verdict` (real `SiteOutcomeBoardService.board` over a `ChainReader` port).
5. S shape: board sum 2, claim 1 -> summary 1; no chain reader -> None - `test_5_...` (two tests).
6. `test_out_b4_read.py::test_walk1_summary_verified_count_and_headline_money` updated to rule 5.
7. Non-vacuity: see Mutations.
- No double count: `test_4_...` proves a FUEL_BALANCE row is excluded by `site_chain.opportunity_actions`, listed once by `fuel_verdict_actions`, absent from `comp.facts.actions` (the Action index lists the trial only), and the board reads 1, not 2.

## Mutations (each on committed 5a7192741, reverted by `git checkout --`, `git status` clean after)
- M1 drop fuel term in `mini.py` and `read.py`: fails test_1, test_3, test_4 and the mb1 fuel board test (4 failed).
- M2 drop fuel term in `read.py` only: fails the mb1 fuel board test (item 4).
- M3 restore the board sum in `_summary` (`verified += body["_verified_results"]`, `verified if verified_read else None`): fails both test_5 tests and the updated `test_out_b4_read` test (3 failed).
- M4 plant `datetime.datetime.now()` in `financials/fuel_cost_v2.py`: `test_ch5c2_clock_guard.py::test_composer_modules_have_no_unaccounted_clock_read` fails naming `fuel_cost_v2:34 datetime.now` (the newly listed module is scanned).

## Checks run (pure, no DB; PYTHONPATH per brief; plan2 venv)
- `test_k6c_assure_fuel_count.py test_mb1_opportunity_board.py test_out_b4_read.py test_ch5c2_clock_guard.py`: 54 passed.
- Unchanged outputs: `test_out_b3_cold_ev test_ch5a1_board_contract test_ch5a2_contract test_ch6_contract test_out_b2_mini test_ch6b_estate_chain test_ch6b2_portfolio_cards test_out_b2_vocabulary test_k6b_fuel_verification_rules`: 228 passed, 0 skipped. No golden or fixture edited.
- Other readers of the field: `test_polish_pa2a_server_copy.py test_out_b4_route.py`: 20 passed; `tools/checks/test_chain_coherence.py -k "L2 or A1 or coh17"`: 49 passed.
- Not run (per brief): DB suites, check-all, full suites, `chain_watermark_guard --modules-out` (that is §9u.2 step 3 on the clone).

## Known deviations
- None against R3u. The mill fixture in the S0 Kobo goldens has no fuel Action, so no Kobo/Cold/EV output changed; the only field change is the summary `verified_result_count` (now the claim value; None in reader-less tests).

## Residual risk / merge notes
- **Expected conflict with K10** in `mini.py` near the headline block (K10 edits `:575-589`; K6c edits `:572-574`). Per §9u.2, K6c rebases after K9 and K10 merge; the conflict is textual only. Reviewer confirms the rebased diff equals this diff; no re-run then.
- The "no double count" proof is at the fake-port level (the Action index fake). That the real Action index never returns a FUEL_BALANCE domain Action rests on R3u's reading (it indexes Actions-store Actions; domain Actions come through the chain rows); the post-fix clone check (§9u.2 step 3, F-COH A1/L2) is the end-to-end proof.
- `verified_result_count` has no on-screen reader (`estateClient.ts:660` types it only), so no visible change.

## User review
Not required for this unit (back-end count and config only; the headline change is v69's count form). Merge gated on review ACCEPT and the §9u.2 step 3 clone check.
