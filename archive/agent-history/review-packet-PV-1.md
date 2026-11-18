# Review packet: PV-1 Portfolio verified-value lines (FUEL-1, lane 1)

- **Task:** build sheet `.agent/build-sheet-FUEL-1.md` §3.3 as replaced by **PV-1-R** (main `3b09aea6c`).
- **Branch / worktree:** `task/FUEL-PV1-portfolio-values`, `C:\Users\assef\Bineyame\AssetOpsV1-pv1`, from main `3b09aea6c`.
- **Status:** built; ready for first review (fresh Opus reviewer, PV-1-R §9). No owner walkthrough of its own; joins the post-W6 walkthrough.
- **Size:** about 0.85 (stop at 1.0 not reached).

## Outcome delivered

On the Portfolio, the Assure card lists one line per verified result that has money. Each line names its Site and
keeps its own basis, and there is never a total.
- **Mill:** `{Site} · {code}: about {d} {cur} a day more in estimated sales to productive users (your declared price)`. `d` is the verdict page's own `value.per_day`.
- **Trial fuel:** `{Site} · {code}: about {l} L, {amount} {cur} less diesel in the one-hour trial (modelled, not metered)`. The figure is the credited stored `priced_total`, rounded half-even.
- **Clause:** below the lines, the card reads "Each result's money is shown on its own and never added together". With no line it reads "No money credited · modelled, not saved".
- **Body note:** the Portfolio-body note (`card_notes`) is now the evidence-gap clause alone.

## Files materially changed

| File | Change |
|---|---|
| `backend/assetops_backend/site_outcomes/mini.py` | `MiniPorts.verdict_value` (last, defaulted); `VALUE_LINE_MILL`/`VALUE_LINE_TRIAL_FUEL`; `_verified_values` (mill via port only for a VERIFIED outcome known by the cutoff, `memo=True`; trial via `credit.credited`, half-even); passed to `SiteFacts` |
| `backend/assetops_backend/site_outcomes/board.py` | `SiteFacts.verified_values` (last field); `_row` adds `nodes.verified_values` to the Assure row only when non-empty, before the NOT_MEASURED return |
| `backend/assetops_backend/site_outcomes/read.py` | `verdict_value` bound to `s.verification.domain_summary(t, sid, UUID(id))["value"]`; `portfolio_cards` Assure gains `value_lines`, `value_note` |
| `backend/assetops_backend/estate/portfolio.py` | `card_notes(summary, authorized)` = the gap clause; call updated. `recovered()` and `cost_checks` unchanged |
| `backend/assetops_backend/chain/vocabulary.py` | `CARD_TEXT` `assure.value_line`, `assure.values_separate` |
| `frontend/src/estate/estateClient.ts`, `PortfolioOutcomes.tsx` | card `value_lines?`/`value_note?`; Assure renders lines then clause (`oc-pfnote`, existing class), after detail, before body note; MD-FUEL-PV1-1 comment |
| `tools/checks/chain_coherence.py` (+ self-tests) | COH-17 row **PV1** (`coh17_values`), called after `coh17_optimize` |
| `tools/demo_combined_rows.py` `pv_values`, `tools/demo_combined_finish.py` | finish row **PV-A** after MILL-5 (written, runs at E3) |
| Tests | new `backend/tests/test_pv1_value_lines.py`; updated `test_ch6b2_portfolio_cards.py`, `test_w303_portfolio_api.py`, `test_out_b2_vocabulary.py`, `test_demo_combined_finish_rows.py`, ch5a2 golden, `estatePortfolio.test.tsx`, `portfolioFixtures.ts` |

## Acceptance (PV-1-R) criterion by criterion

- **§1 S1, verdict-page value through the injected service:** done.
  - Parity test: the entry amount equals `mill_value(details, "VERIFIED", price)["per_day"]` ("17.00"), so S-c did not occur.
  - Binding test through `SiteOutcomeBoardService.board`: `domain_summary` is called once with `(tenant, site, UUID)`.
  - The port is not called without a VERIFIED mill (INEFFECTIVE, INCONCLUSIVE, or verdict after the cutoff), checked with a counting fake.
  - A raising port leaves the board PARTIAL with `verdict_value` in `failed`, and lists no mill entry.
- **§2 S2:** done.
  - The card has `value_lines` in Site then code order, and `value_note` in both forms.
  - `card_notes` gives the gap clause only.
- **§3 entry shape and rounding:** done.
  - Shape: `{key, action_code, basis, amount, currency, text}`, with no `site`.
  - Rounding cases pass: 1/3 → 0.33, 0.125 → 0.12, 0.135 → 0.14; litres 0.25 → 0.2.
  - An uncredited trial (no total, negative, zero, not an improvement, INEFFECTIVE) gives no entry.
- **No sum:**
  - `test_pv1_value_lines`: no card or row string holds the pairwise or total Decimal sum.
  - COH PV1 (ii) and PV-A check the same; their fail cases put "21.12" (17.00 + 4.12) on the card.
- **Byte-equal:**
  - Grow, Optimize and Protect rows and cards are equal with and without entries (tests).
  - The Assure row differs only in `nodes.verified_values`.
  - `test_out_b3_cold_ev.py` passes unchanged.
- **Golden (S-b):** regenerated `estate_week_2026-10-25.json`. Its diff against main is only `cards.ASSURE_PERFORMANCE` gaining `"value_lines": []` and `"value_note": "No money credited · modelled, not saved"` (3 insertions, 1 deletion). No other golden moved.
- **§4 frontend:** the Assure card renders its lines and note in the stated order; a card without the keys renders neither; no new CSS.
- **§5 COH PV1 and PV-A:**
  - COH PV1 self-tests: pass, fail (i), fail (ii), fail (iii), and an older bundle skipped.
  - PV-A L0: a pass in both trial cases, plus four fail bodies.
  - PV-A itself runs at E3; not run here.

## MOCK DEVIATION

| Label | Where | What |
|---|---|---|
| MD-FUEL-PV1-1 | `frontend/src/estate/PortfolioOutcomes.tsx` (comment at the value-line render) | v69 `:129` is one "Verified value recovered" tile ("Not established") and v70 `:492` puts the slot on the Assure card; we show per-basis lines (one per verified result) in that slot instead of one value, because v69 `:131` and `:482` forbid a combined total. |

## Checks run (revision `5b0b06c96` unless noted)

All runs used the plan2 venv. PYTHONPATH was absolute under this worktree, and `assetops_backend` and `assetops_contracts` resolved into it.

**Backend L0 (no DB):**
- `test_pv1_value_lines.py`: 23 passed.
- `test_out_b2_vocabulary.py`, `test_ch6b2_portfolio_cards.py`, `test_out_b4_imports.py`, `test_out_b2_mini.py`, `test_out_b3_cold_ev.py`: 122 passed.
- `test_demo_combined_finish_rows.py`, `test_mb1_opportunity_board.py`, `test_w303_portfolio_api.py`: 61 passed, 1 skipped. The skip was the w303 DB case without a DB; it ran in the DB batch below.
- `test_ch5a2_contract.py` + `test_ch5a1_board_contract.py`: 39 passed after the golden regeneration.

**Postgres:** DB `assetops_pv1_test` on 127.0.0.1:55432, created empty for this unit. Free RAM was 3.5–4.5 GB before the run, and it ran alone.
- Command: `pytest test_mb1_site_actions_postgres.py test_ch9b3_mill_verdict_postgres.py test_ch6b_estate_postgres.py test_out_b4_board_postgres.py test_ch5a2_chain_api_postgres.py test_out_e4_readback_postgres.py test_w303_portfolio_api.py`. Wall time 372 s.
- Result: **28 passed, 3 errors.** All three errors are at setup in `test_ch6b_estate_postgres.py`:
  - `test_kobo_week_days_earnings_total_and_summary_equal_chain`;
  - `test_mg1_judged_on_checked_days_and_estate_optimize_row_equals_the_d13_board`;
  - `test_optimize_card_is_the_one_builder_over_the_summary_rows_and_equals_the_board`.
- Cause: `MechanismRefused: TEMPLATE_STALE: template inputs abc647639e60 != this checkout ac20dd8af5e9`. This is the mechanism-template precondition, expected until E2. A rebuild is a baseline build, which this unit must not run.
- These three tests (estate Optimize/summary on the mechanism dataset) are therefore **not run** here, and their claims are unverified on Postgres.

**Chain coherence:** `tools/checks/test_chain_coherence.py`: 158 passed, including 5 new PV1 self-tests.

**Guards:** `tools/check-all.ps1`: **All 17 guards passed**. These include Architecture seams, Agent workflow, Navigation truthfulness, Mock deviation labels and client vocabulary, Missing-claim scan, Chain coherence, Chain graph, and Frontend hard-wiring ratchet (no rise: api 12, href 24, lit 70, cmp 51, code 3).

**Frontend:**
- `vitest run src/estate/__tests__/estatePortfolio.test.tsx`: 63 passed, including the 2 new PV-1 tests.
- `tsc --noEmit`: exit 0.

**Non-vacuity proofs** (on the committed revision; each mutation was reverted with `git checkout --`, and status was clean after):
- `read.py` mutated to append a "Total {sum}" line to `value_lines`: `test_pv1_value_lines::test_card_lists_site_order_then_code_order_and_states_the_clause` FAILED.
- `chain_coherence.py` mutated to clear `held` (the sum check disabled): `test_coh17_pv1_a_detail_holding_the_sum_of_two_amounts_fails` FAILED.

**Not run** (per brief): full suite, prepare, baseline build, `test_demo_combined_postgres`, layout evidence. The card adds text lines with an existing class; no layout claim is made.

## Known deviations

- **Golden placement:** the golden fixture moved by `ASSETOPS_REGEN_CH5A2_GOLDENS=1` (the test's own regenerate switch), with the diff inspected against main as DRIFT-R1 §2.2 requires.
- **PV-A placeholder code:** PV-A takes the trial code from the Action body's `action_code`, with "ACT-001" as a fallback only. It is unverified until E3.

## Residual risk

- **Board without a verification service:** with no injected verification service (only tests do this), a board with a VERIFIED mill becomes PARTIAL (`verdict_value` failed). Production always injects it (`site_outcomes/composition.py:59`).
- **Second read per board:** `domain_summary` per VERIFIED mill adds one service read per board (memoised per request).

## User-review focus

- S1 parity with the verdict page.
- The no-sum proof.
- The `card_notes` move and the card render order.
- The golden diff limited to the Assure card.
