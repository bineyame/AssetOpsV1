# Review packet: CH-6a3 (composers, wire, R7, removals, proofs)

Branch `task/CH-6a3-composers`. Binding: `.agent/CH-6a3-preflight.md` + CH6a3-R. Handoff chain: `.agent/CH-6a3-handoff.md`.
`git merge main` done (CH-9b2 + FIX-MAIN-3 in). Needs user review: no (not a W1 UI sign-off slice); batched review with CH-6a2.

## Outcome
The mini, cold and EV composers read the OutcomeEvaluator: each board row carries `nodes` (kpi / earnings / potential claims),
`days_line` and `target_note`; the Grow row shows Target / Potential / Estimated income with the days each rests on, and
"Not known yet" where a claim is not known. MG-1 comes from snapshots (R5), a MET needs all expected days COMPLETE (R6),
the potential chip follows the thread's latest study (R13/Q5). "Why?" gains price lines. Old MG-1 board branch deleted.

## Mock -> new
| Mock (v69 Grow row) | New |
|---|---|
| One headline + money | `span.ob-grow` with three `span.ob-part` (Target, Potential, Estimated income), one `<b>` per line of the claim text |
| "Potential 18-20 kW" one line | Potential claim text split on "\n" (kW range / price / several-prices note) |
| Income shown as a figure | Earnings claim; NOT_KNOWN reads "Not known yet" + `days_line` ("No readings on 6 Oct") |
| Target "on track" with a count | KPI claim text from the verdict; "No target set yet" when no objective |
| "Why?" lines | + `why.from.price`, `price_several`, `fuel_price`, `fuel_price_one` |
Cold and EV keep their layout; only `nodes`/`days_line`/`target_note` and the Grow parts are new. MOCK DEVIATION: none added.

## What changed (files)
- Composers: `site_outcomes/mini.py`, `cold.py`, `ev.py`, new `site_outcomes/domain_nodes.py` (kept out of `board.py`, whose purity test
  allows only `outcomes/` and stdlib; the first cut broke it), `board.py` (`row_nodes`, `ev_priced`), `chain/outcomes.py`, `chain/why.py`, `read.py`.
- Frontend: `outcomeBoardClient.ts` (NodeClaim/RowNodes), `OutcomeBoard.tsx` GrowParts, `outcomes.css`.
- Tests: `test_ch6_contract.py` (L1), `test_ch6_nodes_postgres.py` (L2m, new), `outcomeBoard.test.tsx` GrowParts (new, 2 tests).
- `config/chain/stored-composer-modules-v1.json` +7 modules (reviewed diff, W6 back to 0 unlisted).
- `chainClient.ts`: no change needed (the board client carries `nodes`; the chain client does not read them).

## Fixes found while finishing (not in earlier handoffs)
1. Lead-Finding mapping (task step 3): `mini.py` fed the lead money head to MG-2's fuel-cost earnings as GENERATOR_SUPPORT_CANDIDATE whatever its
   mechanism. A client could have seen another mechanism's money labelled as generator fuel cost. Now `_lead_findings(heads, lead_money)` maps it only
   when the head's `mechanism == "GENERATOR_SUPPORT_CANDIDATE"`; otherwise the earnings claim is NOT_KNOWN ("Not known yet").
2. EV Optimize "not measured" sentence: the board used `headline_money[GROW] is None` as "no priced tariff". Since Grow money is now the earnings claim
   (null while days are unknown) the sentence wrongly turned to "needs ... a published charging tariff" for a priced EV (the regenerated golden had
   silently taken that change). Added `SiteFacts.ev_priced` (ev.py sets it); golden `ev_2026-10-27` back to the main wording.
3. Cold/EV passed an invalid route zone to `local_days` (ZoneInfoNotFoundError); now `site_timezone if tz is not None else None` (UTC fallback test passes).
4. Test fakes that predate R6 (`test_out_d4_board.py`): a MET needs COMPLETE snapshot rows, so `complete_rows(...)` added for MG-2 and CC-1.
5. Unused imports removed from `mini.py` (`calendar`, `BEHIND_PACE`, `ON_PACE`, `MISSED`, `TOO_EARLY`, `ObjectiveFact`, `judge_month`).
6. `test_out_b1_board` purity test extended (not loosened) to name the two wording helpers; `test_out_b2_vocabulary` sample gained price keys.

## Acceptance (build sheet §A8, CH-6a3)
- L1 contract goldens with `nodes`: pass. Non-vacuity of the contract test proven earlier by flipping `len(revs) > 1`.
- L2m `test_ch6_nodes_postgres.py` (Kobo estate, w502 cold, w504 EV; real Postgres): 3 passed in 126 s. Non-vacuous: its first run failed on a wrong
  expectation ("No target set yet" is not "Not known yet"), so the node assertions do bite. Recorded: Kobo kpi "No target set yet", earnings and
  potential NOT_KNOWN; EV earnings "Not known yet" with days_line "No readings on 6 Oct", `headline_money` null.
- Scoped existing list: 288 passed, 1 skipped (ch5a1 contract, ch5a2, ch5b why/graph, ch6 x4, out_b1/b2/b3/c2/c4/d4, polish_pa1, walk1_3b/4, b4 imports,
  chain structure tests). Not run: full backend suite (testing rule: localised only).
- Frontend: `tsc` clean; `vitest run src/sites src/estate src/blocks`: 1995 of 1997 passed first run; the 2 failures
  (`coldWorkCases` K3b, `evDepth` R347) passed on rerun in isolation (52/52): load-related flakes, unrelated to the board.
- L3 (polish clone `ch6a3`, dropped): create, migrate, settle, W6 (46 requests, 0 violations, 0 unlisted after the module diff), `fresh` store on
  43/43 equal a fresh compose, collect 85 requests, `check --expect expected-today.json`: **0 new vs main** (24 NEW on B = the same 24 on A=main:
  COH-10 x13, COH-11 x5, COH-2 x3, COH-8 x3, all pre-existing R-1 items), **COH-17 = 0**.
- L3m (states template rebuilt: fingerprint cd95a2e4, 5 parts of `--budget 540`; derive; collect 65): COH-10 x9 NEW, identical on main (A) => 0 attributable
  to this slice; COH-17 = 0. "Unexpected" is 9 on both sides (data/thread items, not board). Reported, not hidden: the expected file is stale for them.
- Graph check (`check_chain_structure.py`) rc 0; frontend ratchet totals api 12, href 24, lit 70, cmp 51, code 3 = baseline (nothing rose, no `--shrink` needed).
- Guards: A architecture passed; W agent workflow passed; V vocabulary 4 passed; M mock-deviation-labels OK (156 files); missing-claim scan passed;
  N ran (rc 0). Not runnable here: `tools/checks/test_estate_guard.py` self-tests (15 fail: PowerShell script execution policy blocks the temp-copy
  `_common.ps1`; the flag is forbidden). Guard A itself (which runs the estate guard) passed.

## L3 table: every board value that changed, A=main -> B=this branch (clone data, 85 requests)
| Value | Old -> new | Rule |
|---|---|---|
| `policy_versions.status` (all board/chain/summary) | outcome-status/3 -> /4 | status policy bump |
| `nodes`, `days_line`, `target_note` on every row | absent -> present (null where no record) | A5, R7 |
| EV Grow `headline_money` (6 boards, 2 summaries) | 4.50 USD -> null | Q4: Grow money = earnings claim; NOT_KNOWN (no readings on the day) |
| EV 20 Oct objective verdict + outcome | MET / ON_TRACK -> NOT_JUDGED / UNKNOWN ("Not checked yet") | R6: MET needs every expected day COMPLETE |
| Kobo MG-1 line text (16 board, 6 summary) | "505 kWh so far this month, 5 of 28 days checked" -> "sales not recorded" | R5: MG-1 from snapshots; the clone holds no productive-sales snapshots |
| Kobo `read_state` PARTIAL -> AVAILABLE (8 boards, 3 summaries), COST headline None -> "No fuel cost estimated for this day", contributor confidence None -> Unknown | | A-side artifact: main on this clone reads the producer unsettled (known from CH-5a1 results E2); B reads settled. Not a rule change. |
No other board value moved.

## Golden diffs explained (10 goldens, regenerated with `ASSETOPS_REGEN_CH5A1_GOLDENS=1`)
- Every board/site golden: status /3 -> /4; `nodes`, `days_line`, `target_note` added.
- `ev_2026-10-27` `headline_money` 54.75 -> null (Q4: the fake snapshot rows carry no money, so the earnings claim is NOT_KNOWN). Its
  `not_measured_text` stays the main wording (fix 2 above).
- cold CC-1 kpi MISSED claim added. `estate_week`, `thread_kobo_generator`: status policy only.

## Test-fake changes
- Kobo opportunity fake (`test_out_b2_mini.py`): item `"state": "OPEN"`, `study.status "SUPPORTED"` (else the R13 signal/Potential vanish). Applied in this
  packet's final commit; the earlier handoff said done but the file was unchanged (5 tests had been failing at the handoff head).
- EV fake (`test_out_b3_cold_ev.py`): `headline_money` expectation 54.75 -> `None` (Q4, as above).
- `Row` helper in the contract tests gained evidence_class / value / money defaults; `test_ch5b_why.py:150` slice `[1:]` -> `[-2:]` (a second measure
  line from the union); `test_out_d5_objectives_postgres.py` spy now `spy(dispatch, **kw)`.

## 6 removed tests (all `test_walk1_3b_target_progress.py`, board-level, superseded by R5 which deletes the board MG-1 branch)
1. `test_kobo_month_to_date_met_is_on_track_without_an_opportunity_chip`: asserted the old dispatch-month MG-1 verdict; now `test_ch6_evaluator`/contract (R5).
2. `test_spare_solar_is_the_opportunity_chip_beside_the_kpi_state`: chip now follows R13/Q5; covered by `test_ch6_contract`.
3. `test_pace_texts_and_states`: pace texts now `chain/vocabulary.mg1_text`, tested in `test_ch6_claims`.
4. `test_too_early_text_names_the_minimum`: same, `test_ch6_claims`.
5. `test_missed_only_for_a_complete_fully_checked_month`: `judge_month` rule kept and tested in `test_ch6_evaluator`.
6. `test_conflicting_day_is_not_checked`: day conflict now graded at the snapshot (R5); evaluator tests.

## Known deviations
- **MG-2 no-price omission:** the MG-2 fuel line (and its "Why?" price line) is omitted when the stored consequence carries no price; no estimate is invented.
- Lead money head: now mechanism-gated (fix 1); a lead Finding of another mechanism leaves MG-2 earnings "Not known yet" rather than mislabelled money.
- A-side L3 comparison used main with copied `var/`; Kobo PARTIAL/AVAILABLE rows above are that artifact.
- Estate-guard self-tests not runnable in this shell (execution policy); guard A passed.
- Layout evidence: not run (Grow parts CSS only; no browser run this phase). The Grow row layout claim is unverified in a browser.

## Residual risk / review focus
- EV Grow money now null where the stored consequence has a figure but days are unknown (Q4); confirm that is the intended client view.
- Kobo MG-1 "sales not recorded" on data without productive snapshots (R5).
- Two load-flaky vitest cases (not touched by this slice).
