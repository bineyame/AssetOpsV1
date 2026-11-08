# Review packet: FUEL-1 A3, idle fuel on Kobo's screens and story

- Card: `.agent/build-sheet-FUEL-1.md` **A3-R** (replaces §4.3's build detail; main `0c4aa7310`). Branch `task/FUEL-A3-kobo-idle-fuel`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-a3`. Cut from `b70be217b`; `git merge main` (fast-forward to `0c4aa7310`) before the build. No rebase.
- Build commit `58b09582c`. **Scratch prepare (§6) NOT run**: held at the coordinator's one-heavy-job gate. Its reads (§6 items 1-5) and the RAM samples are owed and will be appended here.
- `USER_REVIEW_REQUIRED`: screen-wording change; joins the post-W6 owner walkthrough (A3-R §8), no separate walkthrough.

## Outcome delivered

- Kobo declares the generator's idle (no-load) fuel rate, 3.3 L/h, basis `GENERIC_DEFAULT`, with the §4.3 note, at install + 25 min (`tools/demo_combined_kobo.py` `declare_no_load_rate`, called right after `declare_supply_uses`).
- Board Optimize headline on a fuel-cost-2 PRICED day whose counted fuel is all idle (exact: `high_exact == multiplier × idle_h × rate`): `COST_IDLE`, which extends `COST_MONEY`; `headline_money` is unchanged. Mixed, fuel-cost-1 and zero days keep today's lines.
- Trial lines keyed on the presence of the stored `priced_total` plus a shown price (no sign check, A2-R1): board `COST_PRICED`, Assure `VERIFIED_WITH_FUEL`; otherwise the per-kWh lines.
- `_cost_check_read` adds `price_per_litre` (the stored `result.price.value`) only with `priced_total`.
- The trial verification outcome read adds `fuel_value` (VERIFIED outcome + stored `priced_total` + price only); the page renders it under the verdict.
- G4(b): the stored `/2` `no_load` block gains `basis` (read from the same Foundation revision through `_generator_property_history(companion=...)`); `basis_sha256` is unchanged.
- "Why?": the Optimize fuel line gains the example-tank sentence only for a fuel-cost-2 row with idle time on example data (`source_class` in `EXAMPLE_SOURCES`).
- Single sources: `trial_litres` (PV-1's expression, moved) and `price_text` (moved from `mini.py`, re-exported by import) in `chain/vocabulary.py`.

## Rendered literals (from `test_a3_idle_fuel.py -s`, fake inputs at r = 3.3, price 1.25)

- Board idle morning: "0.00 to 15.13 USD possible extra fuel cost on this day: generator on for 200 minutes delivering no power, up to about 12.1 L · counted at a generic idle fuel rate of 3.3 L/h, not measured" (the money prefix is the frontend's; the fake head's high is 15.13).
- "Why?": "0–12.1 L × 1.25 USD/L · The example data's fuel tank does not count fuel while the generator idles; this estimate does, at the declared idle fuel rate, so the two differ"
- Board trial cost line: "Estimated effect of the trial (not money saved): about 3.3 L less diesel in the trial hour, 4.12 USD at 1.25 USD per litre."
- Assure: "ACT-048 verified on example data: estimated effect of the trial (not money saved): about 3.3 L less diesel in the trial hour, 4.12 USD at 1.25 USD per litre"
- Verification page: "About 3.3 L less diesel in the trial hour, about 4.12 USD at 1.25 USD per litre · modelled from a generic idle fuel rate, not measured by a fuel meter"

## Files materially changed

- Backend: `chain/vocabulary.py`, `chain/outcomes.py` (`idle_fuel`, `fuel_basis`), `chain/why.py` (`price_lines`), `site_outcomes/mini.py` (literals, `idle_headline`, headline, `_assure`, PV-1 litres), `site_outcomes/board.py` (`COST_PRICED`, `cost_line`), `actions/verification.py` (`_cost_check_read`, `outcome`, `_fuel_value`), `financials/trial_fuel_comparison.py` (`NoLoadValue.basis`, `no_load` block), `actions/adapters/postgres_action_store.py` (`no_load_history`, `_generator_property_history`).
- Tools: `demo_combined_kobo.py`, `demo_combined_finish.py` (PROBE_CHOSEN/SP-6, MONEY-B extended, new CH5D1-O1 and A3-PAGE), `demo_combined_rows.py` (`idle_morning`, `never_summed`, `steady_day`, `trial_cost`, `optimize_card`, `trial_page`).
- Frontend: `sites/verificationClient.ts`, `sites/SiteActionVerification.tsx`, `sites/__tests__/siteActionVerification.test.tsx`.
- Tests: new `backend/tests/test_a3_idle_fuel.py`; amended `test_tfc2.py`, `test_out_b2_vocabulary.py`, `test_demo_combined_finish_rows.py`, `test_fuel_cost_v2_postgres.py`.
- No migration, no golden file changed.

## Mock deviations

| Id | Where | Note |
|---|---|---|
| MD-FUEL-A3-1 | `chain/vocabulary.py` `FUEL_VALUE_PAGE`; `SiteActionVerification.tsx` | v69 `:498-505` shows no money on Verification |
| MD-FUEL-A3-2 | `mini.py` `COST_IDLE` | v69's cost row has no idle-fuel basis |
| MD-FUEL-A3-3 | `chain/vocabulary.py` `why.from.fuel_idle_example` | v69's "Why?" has no idle-fuel line |
| MD-FUEL-A3-4 | `mini.py` `VERIFIED_WITH_FUEL`, `board.py` `COST_PRICED` | v69 states the trial's effect per kWh only |

## Acceptance (A3-R) criterion by criterion

- §2 literals verbatim, guard V: met (`test_out_b2_vocabulary.py` scans all four lines with every basis word; `WHY_TEXT` scanned automatically).
- §2.4 formatting single sources: met (`test_helpers`; `test_pv1_value_lines.py` green unchanged).
- §3.1 declaration: met (code); stored effect owed to §6.
- §3.2-3.5: met (§5.1 items 1-5 tests).
- §3.6 verification: met (§5.2 tests).
- §3.7 G4(b): met (`test_tfc2.py` new case; L2 `TestNoLoadBasisRead`). S-e checked: the only `result["no_load"]` equality reader was `test_tfc2.py:85` (amended); every `NoLoadValue(...)` construction is positional.
- §3.8 frontend: met, with deviation D2.
- §3.9 finish rows: written with L0 pass/fail self-tests; run at §6 / E3. Deviations D3, D4.
- §4 files: met, plus D1 (test file placement).
- §5 tests and must-fail proofs: met (below).
- §6 scratch prepare: **not run (gate)**.
- §7 stops: none hit so far. S-c and S-f can only be judged at §6.

## Must-fail proofs (each on the committed build, reverted with `git checkout --`, tree clean after)

1. `idle_fuel` `==` → `>=`: `test_idle_fuel_selects_only_fuel_cost_2_with_idle_time_and_is_exact` and `test_mixed_and_fuel_cost_1_days_keep_the_existing_headlines` FAIL (2 failed, 14 passed).
2. Mini headline without the `idle_only` test: `test_mixed_and_fuel_cost_1_days_keep_the_existing_headlines` FAIL.
3. `price_lines` without the `EXAMPLE_SOURCES` gate: `test_why_idle_line_only_on_example_data_with_idle_time` FAIL.
4. `_fuel_value` without the VERIFIED check: `test_outcome_fuel_value_only_for_verified_with_priced_total` FAIL (INEFFECTIVE case).
5. `basis` added to the `/2` digest input: `test_tfc2.py::test_a3_no_load_block_stores_the_basis_outside_the_digest` FAIL.

## Checks run (revision `58b09582c`)

- Contracts before (tree at `0c4aa7310`) and after: `host/tests/test_k0_kisiwa_actions.py` (K0 byte-equal pins), `test_scenario_execution_contract.py`, `test_execution_contract_alignment.py`, no DB: **131 passed, 2 skipped** both times (the 2 skips are the K0 file's two DB cases, `ASSETOPS_TEST_DATABASE_URL` unset). `k0_byte_equal_pins.py` unchanged.
- No-DB focused and adjacent: `test_a3_idle_fuel.py`, `test_tfc2.py`, `test_demo_combined_finish_rows.py`, `test_out_b2_vocabulary.py`, `test_out_b2_mini.py`, `test_out_b3_cold_ev.py`, `test_ch3_rows.py`, `test_pv1_value_lines.py`, `test_out_e4_readback.py`, `test_ch5a2_contract.py`, `test_out_e2_trial_comparison.py`, `test_polish_pa1_board_truth.py`, `test_polish_pa2a_server_copy.py`, `tools/checks/test_chain_coherence.py`: **440 passed, 0 skipped**, 25 s.
- Postgres on base `assetops_a3_test` (created for this unit; harness clones), free RAM 3.39 GB / 3.36 GB before each step:
  - `test_fuel_cost_v2_postgres.py`: **10 passed**, 64 s.
  - `test_s6_verification_evaluator_postgres.py`, `test_k3_fuel_balance_postgres.py`, `host/tests/test_k0_kisiwa_actions.py`: **53 passed**, 265 s.
- Frontend (after `npm ci`): `siteActionVerification.test.tsx` **34 passed**; `tsc --noEmit` exit 0.
- Guards: `tools/check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` on `58b09582c`: **All 17 guards passed** (architecture, agent workflow, chain coherence 158 passed, hard-wiring ratchet totals `{"api":12,"href":24,"lit":70,"cmp":51,"code":3}`, missing-claim scan, mock-deviation labels and the rest). The estate guard self-tests alone took 22.5 min, because other lanes were loading the machine.
- Not run: full suites, baseline build, any prepare.

## Known deviations

- **D1** §5.4 names "the existing A2 Postgres file that covers `no_load_history`". No such file exists (A2 tested it with fakes). The two L2 cases went into A1's `test_fuel_cost_v2_postgres.py`, whose PowerSite already declares the rate and basis (new class `TestNoLoadBasisRead` + fixture `rate_only_site`).
- **D2** §3.8 asks for "the existing verdict-detail class". The mill verdict page's value line (MV-1 precedent, `SiteMillVerification.tsx:90`) uses a bare `<p>`; the trial line does the same (`<p data-verification-fuel-value>`). No CSS added.
- **D3 (needs an Architect call before E3)** `tools/demo_combined_after.py` O16 `fuel_rows_ok` (`:146-159`) still asserts S-14 and S-7 are PRICED with quantity 0. After A3 they are PRICED above 0, so O16 in the after-run will fail at E3. The file is not on A3-R §4's list, so it was not edited. MONEY-B now carries the O16 idle checks; the fix is a small edit in `demo_combined_after.py` (or retiring that half of O16).
- **D4** §3.9 says steady days have "stored `idle_seconds == 0` and the headline is `COST_MONEY`". O16 asserts steady days have **no** fuel row at all, so the board shows `COST_NO_MONEY` there. `steady_day` therefore asserts: every stored head row on the day (if any) has 0 or no idle seconds, and the headline is not the idle line; it reports the headline and money as shown.
- **D5** `chain/outcomes.idle_fuel` checks `model_id == "fuel-cost-2"` as a literal: `chain/` does not import `financials/` outside its composition, so `fuel_cost_v2.MODEL_ID` is not imported.
- **D6** MONEY-B's "week estate body" sum check walks the S week summary (S-6 to S+1) **and** the three idle-morning boards, because S-14 and S-7 fall outside that week.

## Residual risk

- All stored figures (12000 s per morning, 3600 s trial baseline, the 15.125 high) are unproven until §6. The board's money prefix is the consequence read's outward display (`ROUND_CEILING`), so a stored exact 15.125 reads **15.13**, not 15.12 (§2.2's question answered from code: `consequence_read.display`).
- Every Kobo Finding becomes fuel-cost-2 once declared (A1 selection). WK-2a's 42.08 must still hold at §6 (no 0 kW reading inside its Candidate time).
- The Foundation display name "Generator no-load fuel rate" (backlog item, A3-R §8): grep of `frontend/src` finds no screen that renders a component property's `display_name`; the Foundation views render asset and component names only. Not changed.
- Template fingerprint goes stale (writer changed); rebuild owed at E2 (MB-1a-R2 §5).

## User-review focus

- The board idle-morning sentence and the "Why?" sentence (owner decision 3) on S-14, S-7 and S.
- The trial lines (board, Assure, verification page): litres and USD, labelled modelled and generic, never summed with the mill.
