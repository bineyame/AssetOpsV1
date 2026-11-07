# Review: WD-1 money wording (BL-48)

Reviewer: Claude (fresh, independent first review). Branch `task/FUEL-WD1-money-wording`, commits e73ef9ef0 (code) and c979da22a (packet). Spec: WD-1-R in `.agent/build-sheet-FUEL-1.md` (c1db80094), BL-48 in `.agent/backlog-post-demo.md`.

## Verdict: FIX

The code matches WD-1-R exactly. But two committed goldens still hold the old EV Grow headline, so two contract tests fail on the branch. The packet says no other test failed. It did not run these two files. The fix is a reviewed regeneration of the two goldens. It touches no code.

## Findings

### M1 (Medium, acceptance gap): two EV goldens fail on the new headline
- **Where:**
  - `backend/tests/fixtures/ch5a1_board_contract/ev_2026-10-27.json`, at `rows/0/headline`.
  - `backend/tests/fixtures/ch5a2_chain_contract/site_ev_2026-10-27.json`, at `outcomes/0/headline`.
- **What fails:** `test_ch5a1_board_contract.py::test_board_equals_its_golden[ev_2026-10-27]` and `test_ch5a2_contract.py::test_chain_body_equals_its_golden[site_ev_2026-10-27]`. Both fail on the branch. Run: 2 failed, 49 passed.
- **Cause:** both goldens record the exact case that BL-48 describes. The day is priced, `headline_money` is null, the charging line reads "Not known yet · 0 of 1 day checked …", and the headline is "estimated charging income".
- **Scope of the change:** I diffed each body against its golden field by field. In each file the only difference is the headline, now "No income figure for this day: it is not fully checked". So the change is the one the ruling intended, and nothing else moved.
- **Why it matters:** the branch is red on two contract tests. The packet's "No other test failed" claim does not hold for these two files. WD-1-R §3 only names the STOP rule for the `GENERATOR_KWH_UNKNOWN` text. Even so, a golden carrying the changed EV headline is the kind of change a reviewer must see recorded.
- **Fix:**
  - Regenerate only these two goldens. Use `ASSETOPS_REGEN_CH5A1_GOLDENS=1` for ch5a1, and the ch5a2 regeneration switch in `test_ch5a2_contract.py`. Under that switch, the ch5a2 test rewrites every case in its file, not only the EV one.
  - Confirm `git diff` shows exactly one changed line in each EV golden and no change to the other ch5a2 goldens.
  - Rerun both files, and record the diff in the packet.

### L1 (Low, wording precision; not blocking): "for this day" on a part-day window
- **Where:** `backend/assetops_backend/site_outcomes/ev.py:307`.
- **What:** the override also fires on windows that are not one Site-local day. The golden's own window is 08:00–16:00 UTC. In that case `earnings_parts` gets `day=None`, but the headline still says "for this day".
- **Why it's minor:** the literal is the Architect's verbatim choice (MD-WD1-1). On the demo board's one-day windows it reads correctly.
- **Action:** none for WD-1. Record it under residual risk so it is a known item for the walkthrough.

### L2 (Low, stale comment): the old words remain in one docstring
- **Where:** `backend/assetops_backend/chain/vocabulary.py:339`. The `mg1_text` docstring still says the board's "sales not recorded".
- **What:** this is a comment only. It does not reach the screen.
- **Fix:** optionally say "`MG1_NO_DAY`" instead, in the same fix round.

## Checklist results
1. **Literals: exact.**
   - `NO_INCOME_FIGURE` is at `ev.py:52` and is added to `COPY`.
   - `MG1_NO_DAY` is at `vocabulary.py:269`, and `MG1_ACTUAL = MG1_NO_DAY` is at `mini.py:135`, joining the existing import at `:27`.
   - The `GENERATOR_KWH_UNKNOWN` words are at `board.py:90`.
   - The labels MD-WD1-1 and MD-WD1-2 are present.
2. **EV override: correct and narrow.**
   - `earnings_parts` always returns a money dict when the claim is known (`chain/outcomes.py:341`, `earnings_money` returns None only for NOT_KNOWN). So the override fires only when `priced` is true and the claim is NOT_KNOWN.
   - Money present keeps `TARIFF_ESTIMATE`. Not priced keeps `NO_TARIFF`, because the condition requires `priced`.
   - The base headline at `ev.py:230` and the path where `_charging_from_claim` is not called (`:275`) are unchanged.
3. **Retyped strings: by import only.**
   - Changed by import: `test_ch6_claims`, `test_ch6_evaluator`, `test_out_d4_board`, `test_demo_combined_finish_rows`, and `tools/demo_combined_rows.py` (WK-4, with the docstring updated).
   - The ruling's "WK-1" citation for `tools/demo_combined_rows.py:93` refers to the same WK-4 function. `wk1` never checked the old sales string, so it needs no change.
   - `wk1`'s unknown branch does not assert the headline. The new EV headline therefore does not break WK-1.
   - The import inside `wk4` keeps `demo_combined_rows.py` free of a backend import at module level, which matches its existing pure-helper style.
4. **The new tests catch a break.**
   - The EV case asserts `headline == NO_INCOME_FIGURE`. Removing the override makes it `TARIFF_ESTIMATE`, so the case fails. I confirmed this by reading the code; I did not rerun the mutation myself. The packet reports the same result.
   - The MG-1 case pins the literal.
   - `test_out_d4_board` checks the rendered line, so it would catch a broken `MG1_ACTUAL` tie.
5. **Mill line:** unchanged. The packet lists it under residual risk as "closed by WD-1m". Pass.
6. **Wording:** all three strings are plain client language with no system vocabulary. Pass.
7. **Regression risk:**
   - Cold, Kobo and the other EV board tests pass. The 16-file set below passed.
   - The EV goldens fail; see M1.
   - The frontend `EvSiteViews` "estimated charging income" caption is on the Site money surface, which is gated by `state === "ESTIMATED"`. WD-1 does not change it.
   - No frontend fixture or other golden holds "sales not recorded" or "not known for both hours". I checked with `git grep` across backend, tools, frontend, contracts and simulator.

## Checks run (all in the wd1 worktree)
- **Imports:** `assetops_backend` and `demo_combined_rows` resolve to `C:\Users\assef\Bineyame\AssetOpsV1-wd1\...`. PYTHONPATH was absolute under wd1, using the plan2 venv python.
- **Focused and adjacent tests:** 16 files, 394 passed in 16.2s. The files were:
  - the packet's set: test_ch6_claims, test_ch6_evaluator, test_out_d4_board, test_demo_combined_finish_rows, test_out_b3_cold_ev, test_out_e4_readback, test_out_b2_mini, test_out_e2_trial_comparison, test_out_b1_board, test_out_a1_outcome_map;
  - plus test_ch5a1_r1_visibility, test_ch5a1_summary_ledger, test_ch5b_why, test_ch6b2_portfolio_cards, test_ch6b_estate_chain, test_mb1_opportunity_board.
- **Golden contracts:** `test_ch5a1_board_contract.py`, `test_ch5a2_contract.py` and `test_ch6_contract.py` gave 2 failed and 49 passed (M1).
- **Guards:**
  - `tools/check-architecture.ps1` passed: "Architecture check passed.", exit 0, 255s. `ASSETOPS_GUARD_PYTHON` was set to the plan2 venv. A main check-all was running at the same time.
  - `tools/check-agent-workflow.ps1` passed: "Agent workflow check passed.", exit 0, 1.2s.
- **Not run (by instruction):** no DB tests, no full suite, no frontend checks. The slice has no frontend diff and no layout change, so layout evidence does not apply. The new EV headline is longer than the old one, and its fit on the Depot Grow card was not checked in a browser. Leave that to the owner walkthrough.

## Process deviations disclosed by the builder (noted, not blocking)
- A failed `sed` that produced nothing.
- A pytest pass whose imports resolved to the wrong tree; the builder discarded it and reran.
- Sleep-based polling.

## Residual risk not named in the packet
- The two EV goldens (M1).
- "for this day" on part-day windows (L1).
- The longer EV headline's fit on the board card is unchecked visually.
