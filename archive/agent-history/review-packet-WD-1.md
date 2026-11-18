# Review packet: WD-1 money wording (BL-48), ruled by WD-1-R

Branch `task/FUEL-WD1-money-wording`. Code commit e73ef9ef0 (plus this packet).

## Wording
| Where | Before | After |
|---|---|---|
| `chain/vocabulary.py` `MG1_NO_DAY`; `site_outcomes/mini.py` `MG1_ACTUAL = MG1_NO_DAY` (MD-WD1-2) | sales not recorded | no fully checked day counted yet this month |
| `site_outcomes/ev.py` new `NO_INCOME_FIGURE` (MD-WD1-1), Grow headline when priced and the claim money is None | estimated charging income (no amount) | No income figure for this day: it is not fully checked |
| `site_outcomes/board.py:90` `GENERATOR_KWH_UNKNOWN` | generator energy is not known for both hours | generator energy is not known for one or both hours |

Unchanged: priced with money keeps `TARIFF_ESTIMATE`; not priced keeps `NO_TARIFF`.

## Files
ev.py (constant, export tuple, `_charging_from_claim` returns `headline`), vocabulary.py, mini.py, board.py.
Tests importing the constant (no retyping): test_ch6_claims.py, test_ch6_evaluator.py, test_out_d4_board.py,
test_demo_combined_finish_rows.py, tools/demo_combined_rows.py (WK-4). New cases: test_ch6_claims.py (MD-WD1-2),
test_out_b3_cold_ev.py `test_ev_priced_day_with_unknown_claim_never_names_an_estimate_without_a_figure` (MD-WD1-1).

## Checks
- Focused: test_ch6_claims, test_ch6_evaluator, test_out_d4_board, test_demo_combined_finish_rows, test_out_b3_cold_ev,
  test_out_e4_readback, test_out_b2_mini, test_out_e2_trial_comparison, test_out_b1_board, test_out_a1_outcome_map
  (vocabulary patterns): 240 passed, imports resolved into the worktree.
- Non-vacuity: with the override disabled the new EV case fails (AssertionError); restored, it passes.
- No other test failed on the GENERATOR_KWH_UNKNOWN text. No DB, no full suite.
- Fix round (review-WD-1 M1/L2): regenerated only `ch5a1_board_contract/ev_2026-10-27.json` (`rows/0/headline`) and
  `ch5a2_chain_contract/site_ev_2026-10-27.json` (`outcomes/0/headline`); each shows one changed line, "estimated
  charging income" -> "No income figure for this day: it is not fully checked". The regen switches also rewrote
  line endings on three other ch5a1 goldens (no content change); restored with `git checkout --`. test_ch5a1_board_contract,
  test_ch5a2_contract, test_ch6_contract: 51 passed without the env vars. Stale `mg1_text` docstring fixed (L2).
- Guards run by the reviewer: check-architecture passed; check-agent-workflow passed.

## Residual risk
- L1: the EV headline says "for this day" also on part-day windows (e.g. the golden's 08:00-16:00 UTC window); literal is
  the Architect's verbatim MD-WD1-1 choice. Fine on one-day board windows; a walkthrough item.
- The longer EV headline's fit on the Depot Grow card is not checked in a browser.
- Mill verified line has no " on example data" suffix while the trial entry does (MB-1a-R2 note). Not changed here per
  WD-1-R section 4; closed by WD-1m.
- Existing finish-row WK-4 relies on the new text ending; verified only by unit test, not a live run.
