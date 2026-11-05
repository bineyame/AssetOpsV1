# Review packet CH-6a2: evaluator and claims (pure)

- Branch `task/CH-6a2-evaluator`, main merged at `84955b219` (CH6a2-R). Build head `921f537ea` (+ this packet).
- Sheet: `.agent/build-sheet-CH-6.md` §S.2, §A3, §A4, R5, R6, R8, R11, R12, R13; CH6a2-R (binding); pre-flight
  `.agent/CH-6a2-preflight.md`. Review: **batched with CH-6a3** (no consumer until CH-6a3).

## Outcome delivered

A pure `OutcomeEvaluator` gives each outcome its three node claims, `kpi`, `earnings` and `potential`. Each is a PC-1 `Claim`.
It also gives the R5/R6-adjusted KPI readings. The claim texts are rendered once, in `chain/vocabulary.py`, from §A4
templates. Server `money_text` equals the board's `boardMoneyText` on one shared fixture, checked by both pytest and
vitest. The CH-6a1 Lows L1–L3 are fixed. No composer, route, wire or frontend source changes, so no stored body changes
either (the clone run is CH-6a3's).

## Files

| File | Change |
|---|---|
| `backend/assetops_backend/chain/outcomes.py` (new) | `AUTHORITY`, `NodeInputs` (frozen), `OutcomeEvaluator.nodes/readings`, `headroom_signal_on` (R13), `POTENTIAL_STATES` (Q4), `READING_MEASURE` (Q2) |
| `backend/assetops_backend/chain/vocabulary.py` | MG-1 texts moved (Q3); `NODE_TEXT` (§A4); `money2`, `money_text`, `mg1_text`, `days_line`, `verdict_claim`, `money_claim`, `potential_claim`, `potential_lines` |
| `backend/assetops_backend/chain/reader.py` | public `day_grade`, `counts` (the existing `_day_grade`/`_counts`, no rule change) |
| `backend/assetops_backend/chain/strategies/graded_verdict.py` | L1: `day_grades` / `grade_counts` by `reader.day_grade` |
| `backend/assetops_backend/chain/strategies/priced_energy.py` | L2: money only from days whose day grade is COMPLETE/PARTIAL; L3: an amount with no currency (`None`, `"None"`, `""`) is `NOT_PRICED` |
| `backend/assetops_backend/site_outcomes/mini.py` | import-only: the four MG-1 constants deleted and imported from vocabulary under the same names (`COPY` and tests unchanged) |
| `backend/tests/test_ch6_evaluator.py`, `test_ch6_claims.py` (new); `test_out_b2_vocabulary.py` (+4 lines: `NODE_TEXT` in the guard-V scan) | L0 |
| `frontend/src/shell/__fixtures__/money-text.json`, `frontend/src/shell/__tests__/moneyText.test.ts` (new) | shared fixture with 15 cases: the 9 from `outcomeBoard.test.tsx:110-119` plus 0.00, a negative, -0.001, 0.005, 0.015, a 10-place value and an empty currency |

## Rulings applied (CH6a2-R)

- **Q1.** The potential's value line and money line are joined by `"\n"`. The money line is present only when the study is SUPPORTED and
  priced (`outcomes.py` `_potential`: `status == "SUPPORTED" and headroom`). LIMITED or UNKNOWN gives the item's
  `limit_line` alone, even when a headroom is stored. The money fields sit in `value` as strings.
- **Q2.** The MG-5 days are `counts` over the board day of `critical_served`. The figure comes from that row:
  `mini.py:496` passes `served=critical_served(day_facts, day)`, and `mini.py:607` builds the MG-5 Reading from that
  row's `unserved_kwh`. The MG-2 `avoided_cost` earnings have **days=None, NOT_KNOWN**. Their money is the lead
  Finding's stored consequence display (`chain/read.py:401`, `money_head`), not a value computed from `avoidable_gen_min` rows.
  The potential's days come from `study.day_grades` when the CH-4 item carries them. Today's item
  (`chain/opportunities.py` `_item`) carries `first_day`/`last_day` but no per-day grade. So every potential is
  days=None, NOT_KNOWN, with its text still shown: **MD-CH6-4**.
- **Q3.** The `mini.py` change is import-only (diff above).
- **Q4.** The potential shows for OPEN, RECURRED, REOPENED and CHANGE_APPLIED only. Every other state, including no
  thread, reads `potential.none`. The R13 status signal is OPEN or RECURRED.
- **Q5.** With no counted day, MG-1 reads "sales not recorded" (`MG1_NO_DAY == mini.MG1_ACTUAL`, asserted) and NOT_JUDGED.
- **Q6.** With no objective, the claim has `value=None`, `days=None`, NOT_KNOWN and "No target set yet". The
  `target.days_none` template is defined, for CH-6a3's days line.

## Acceptance criteria (§Build units CH-6a2)

| Criterion | Status | Test |
|---|---|---|
| MG-1 COMPLETE/PARTIAL/LOW/NO_DATA mix (LOW never added, PARTIAL added, checked = COMPLETE) | met | `test_mg1_mix_*`, `test_mg1_weakest_subject_decides_the_day` |
| MET on 2 days, TOO_EARLY on 1, ON_PACE/BEHIND_PACE, MISSED only on a full month | met | `test_mg1_too_early_on_one_day_and_pace`, `test_mg1_missed_only_on_a_full_month` |
| CC-1 chamber NO_DATA → NOT_JUDGED | met | `test_cc1_chamber_no_data_*`, `test_cc1_partial_day_is_not_met` |
| MG-2 AT_MOST miss on a PARTIAL day | met | `test_mg2_at_most_miss_proven_on_a_partial_day` |
| A DECLARED row ignored | met | `test_mg1_mix_*`, `test_a_declared_row_does_not_complete_a_day` |
| CURRENCY_MIXED; PARTIAL unscaled; zero kWh priced → 0.00 | met | `test_earnings_*` |
| Potential SUPPORTED / LIMITED / none | met | `test_potential_*`, plus parametrised Q4 states |
| `money_text` = `boardMoneyText` on `money-text.json` (pytest and vitest) | met | `test_money_text_equals_board_money_text_on_the_shared_fixture`; `moneyText.test.ts` (16) |
| `judge` / `judge_month` unedited | met | `git diff main -- backend/assetops_backend/outcomes/objectives.py` is empty |
| No composer, route or frontend edit | met | the frontend diff is the fixture and the test only; no `board/cold/ev/chain_api` change |

## Checks run (all at `921f537ea`, localised; no full suite, no demo prepare)

- **L0:** `pytest tests/test_ch6_evaluator.py tests/test_ch6_claims.py tests/test_ch6_contributions.py`: 75 passed.
- **Adjacent:** `test_ch5a2b_claims, test_out_b2_mini, test_out_b1_board, test_walk1_3b_target_progress,
  test_walk1_productive_sales, test_out_b4_imports, test_ch9_measures, test_ch9_no_noon_literal, test_out_a1_outcome_map,
  test_out_b2_vocabulary, test_ch1b_drain, test_out_b3_cold_ev, test_ch9b1_origin_readers, test_qw2_reuse`: 220 passed.
- **Vitest:** `npx vitest run src/shell/__tests__/moneyText.test.ts`: 16 passed. `tsc --noEmit`: exit 0.
- **Mutations.** Each was applied with sed, the tests run, then `git checkout`. Every one failed the tests:
  - Q4: add RESOLVED_MONITORING (2 failed); drop CHANGE_APPLIED (2).
  - Q2: ignore the study day grades (1); give MG-2 the days of a nearby measure (1).
  - Q1: join with " - " (2); show the money line when not SUPPORTED (1).
  - Q6: days on a no-objective claim (1).
  - R6: drop the completeness AND (3). R5: count LOW days (2). R13: REOPENED opens the signal (1).
  - AUTHORITY: count DECLARED rows (2).
  - L1: use the old max-order day grade (1). L2: filter per row (1). L3: accept "None" as a currency (1).
  - `money2` half-up instead of half-even (2).
  - Fixture text 0.02 → 0.01: pytest 1 failed, vitest 1 failed.
  - Guard-V scan with "load" in a node template: 1 failed.
- **Graph check:** `check_declared_chain_graph()` reports "chain graph OK: 7 measures, 5 lifecycle mechanisms, 15
  outcome-map entries", with CHARGERS_MOSTLY_IDLE still a known gap (BL-06).
- **Ratchet:** not run. R3 is backlogged as BL-04 (SCOPE-1), and `tools/checks/check_outcome_ids.py` is not on main.
  `chain/outcomes.py` holds no `MG-/CC-/EV-` or `FINDING:/SIGNAL:/WARNING:/MEASURE:` literal: it splits sources with
  `partition(":")`, and `READING_MEASURE` is keyed by objective measure key.
- **Guards**, run one at a time:
  - A (`check-architecture.ps1`): passed. Its first run failed on `headroom_signal_open(`, because the `open\(` storage
    pattern matched; the function was renamed `headroom_signal_on`.
  - N: passed. M scan and fixtures: exit 0. V (mock-deviation labels and client vocabulary): exit 0. L (v69 ledger):
    valid. Chain coherence: 103 passed. D (frontend hard-wiring ratchet): passed. W: see below.

## Known deviations (for the Architect)

1. **`verdict.mg5_basis` (" · checked over 12:00–13:00", R9) is not built.** Since CH-9 §9 R9, MG-5 reads the whole
   declared day (`mini.py` `MG5_UNSERVED` "... over the whole day"), so the suffix would be untrue. The MG-5 text is the
   composer's own.
2. **ACTION_IN_HAND reads `potential.none`.** Q4 lists only four states, and the brief says "only". This state has no
   change applied yet, so the study is arguably still the latest evidence. Confirm, or add it in CH-6a3.
3. **R6 needs `expected > 0`.** A window with no expected day of the measure cannot complete a reading, so there is no
   MET on unread days.
4. **`NodeInputs` is additive**, as the sheet's field list plus `lead_findings` (mechanism to Finding id). The sheet
   keys `money_heads` by Finding id, so the evaluator needs this to find the record's head. `price` is
   `{"amount", "currency"}`, the shape of stored money. CH-6a3 fills both.
5. **Earnings `value` is `{"amount", "currency"}`** (a range is `{"low", "high", "currency"}`, strings), not a bare
   Decimal string, so CH-6b's `money_total` can check currency.
6. **MG-2 earnings text is the amount alone** ("3.00 to 5.00 USD"), with no days phrase, because Q2 gives it no days.
7. **`mg1_text` restates `mini.num`** as `vocabulary._one_decimal`. `chain` cannot import `site_outcomes`, and Q3 keeps
   `mini.py` import-only. `test_mg1_text_equals_the_board_rule` asserts equality on five verdict cases. CH-6a3 can make
   `mini.mg1_reading` call `mg1_text`.
8. **`row.target_note` (R7) is not here.** R7 is CH-6a3's (Build units).

## Residual risk

- None of this has a consumer yet. CH-6a3 wires `NodeInputs` from ChainRequest, and the L2m/L3 proofs (stored rows,
  the clone's old → new values) land there.
- If CH-9b2 appends verification copy to `chain/vocabulary.py`, it will meet this unit's append. Both sides only append.

## User-review focus

None in this unit (pure). User review comes after CH-6a3, which carries the board changes.
