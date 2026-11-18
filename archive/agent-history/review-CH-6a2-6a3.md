# Review: CH-6a2 + CH-6a3 (batched)

- Reviewer: fresh Claude (independent; did not author either unit). Read-only.
- Worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch6a3`, branch `task/CH-6a3-composers`, head `f1beed6d9`.
- Judged against: build sheet CH-6 §S.2, §A3–§A8, R5–R13, Build units (CH-6a2, CH-6a3), SCOPE-1, CH6a1-R, CH6a2-R, CH6a3-R; mock `frontend/mockups/v70/index.html` (`:412-421`); both packets.

## Verdict: REVISE

Most of the evaluator is sound: the pure rules, `POTENTIAL_STATES`, R6, R7 precedence, the "Why?" price lines, the lead-head gate, and the restored EV wording. Four problems block acceptance. Six existing tests fail at the head. The L2m proof the sheet requires was not built. The Grow parts do not match the v70 mock, and none of the mismatches is labelled. And a Grow row can contradict itself on screen.

## High

**H1. Six existing tests fail at the head: `backend/tests/test_walk1_productive_sales.py`.**
- I ran it and got 6 failed, 14 passed:
  - 4 fail with `KeyError: 'MG-1'` (`:116, :139, :148, :168`).
  - `test_priced_estimate_leads_the_grow_row` (`:179`) fails: `headline_money` is `None`, but the test expects 25.25 USD.
  - `test_row_state_with_the_estimate_is_unchanged` (`:234`) fails: `None`, but the test expects 42.08 USD.
- The CH-6a2 packet ran this file as an adjacent test and it passed. The CH-6a3 scoped list ("288 passed") leaves it out.
- These tests guard exactly the Grow money and MG-1 behaviour this slice changes.
- **Fix:** update each test to the ruled behaviour, or fix the code. The failures show H3 below. Do not just delete the tests.

**H2. The L2m acceptance (§A8 item 3; the CH-6a3 Build-units acceptance) was not delivered.**
- The sheet requires these checks, on `mechanism_db()` (MD-0), asserted by recomputation:
  - Kobo D13: MG-1 `checked_days` equals the COMPLETE `productive_kwh` days, and the verdict equals `judge_month` over the stored rows.
  - Kobo earnings for D7–D13: 6 of 7 days, amount = Σ stored day money.
  - D13 potential: SUPPORTED, so the value line and the money line.
  - MG-2: D11 MISSED, D12 MET.
  - Cold D3: CC-1 and CC-6 not MET.
  - EV D9: earnings 1 of 1, EV-1 MISSED.
  - The rows are read once.
- `test_ch6_nodes_postgres.py` (`:27-85`) instead checks only the shape and the basis enum, on the estate, w502 and w504 builds.
- On that data every Grow node is NOT_KNOWN or "No target set yet" (the packet's own record). So no real-data run ever produces an earnings figure, a SUPPORTED potential money line, an MG-1 verdict from snapshots, or a price/fuel "Why?" line.
- The defensibility of every money figure therefore rests on fakes only. No ruling waived this (SCOPE-1 kept L2m).
- **Fix:** build the §A8 item 3 bullets on `mechanism_db()`.

**H3. A Grow row can state two contradictory things.**
- EV golden `ev_2026-10-27.json`, GROW row:
  - The Estimated income part reads "Not known yet", with "0 of 1 days checked · 1 with too little data, not counted".
  - The subline on the same row reads "182.5 kWh with a complete meter record, at the declared tariff of 0.30 USD per kWh · not billed or collected".
  - The `charging_delivered` contributor reads "182.5 kWh with a complete meter record".
- The packet's L3 says the same happens on clone data: on 6 EV boards, 4.50 USD becomes null because of "no readings on the day", while the analytic that wrote the subline did read the day.
- Mini has the same pattern. `mini.py:529-530` nulls Grow money whenever the snapshot earnings are NOT_KNOWN, but `SALES_SUBLINE` ("… kWh used by …, at the declared price of … · not billed or collected") still shows. See H1, test `:176`.
- Hiding the figure (CH6a3-R Q4) is right. But leaving a "complete meter record" or "kWh used" claim beside "Not known yet" makes one of the two statements untrue.
- **Fix:** route to the Architect. Either make the subline and contributors follow the earnings claim's grade, or explain and reconcile why the snapshot grade (LOW/NO_DATA) disagrees with the composer's own source on the same day. Also list the Kobo MG-1 case in L3 with evidence; see M1.

**H4. The Grow parts do not match mock v70, and the mismatch is unlabelled.**
- Code: `frontend/src/sites/OutcomeBoard.tsx:114-138` and `outcomes.css:178-181`. Mock: `v70/index.html:213-215, 416-420`.
- **The mock:** "Each part carries its own days line": `div.ob-part > span.ob-plabel + b + small.ob-days`, in a 3-column bordered grid that drops to 1 column at 760 px. All three parts always show.
- **The build:**
  - It shows one row-level `days_line` after the parts. That line is the first non-null of kpi, earnings, potential (`board.py:312`).
  - It drops null parts.
  - It uses a flex layout with no part borders.
- **Consequences:**
  1. CH6a3-R Q2 ("each Grow part carries its own days line … so every shown figure has its days") is not met.
  2. Q4's condition ("Estimated income must read `money.not_known` *with its days line*") fails whenever the kpi has days, because the kpi's line wins.
  3. The line can be read as the days behind a different figure. In the Kobo golden, "1 of 1 days checked" sits under "18–24.25 kW of daytime solar unused", whose days are None (MD-CH6-4). That reading is untrue.
  4. On EV Grow, the kpi is null (EV-3 has no kpi record), so the Target part disappears. The mock shows "Target: No target set yet".
- MD-CH6-1, -2, -3 and -4 are not in `mock-departure-register.md`, and there is no MOCK DEVIATION comment in `OutcomeBoard.tsx`. The packet says "MOCK DEVIATION: none added", and its table cites v69, not v70.
- **Fix:** send per-part `days_line` on the wire, or render `days_line(claim.days)` per part. Always render the three parts, Target reading `target.none` when no kpi applies. Match the grid and part markup. Label every remaining departure in the register.
- **Layout evidence was not run.** The packet says so honestly. It is still owed for this layout-sensitive change.

## Medium

**M1. The Kobo MG-1 L3 change is unexplained.**
- The change: "505 kWh so far this month, on 5 of 28 days checked" becomes "sales not recorded" on 16 boards and 6 summaries.
- R5 predicted that checked days would fall, because 8-of-24 h days are PARTIAL. It did not predict that the whole reading would vanish.
- The packet's reason, "the clone holds no productive-sales snapshots", has no evidence behind it (no row count, no producer log). It also conflicts with the productive readings that produced 505 kWh.
- "Sales not recorded" beside measured use is a weak claim to show a client.
- **Fix:** query the clone's `productive_kwh` rows for Kobo in that month. Then either fix the producer or settle gap, or record the reason in L3 with the evidence.

**M2. The R7 target note and the packet's own fixes have no tests.**
- The sheet requires an L0 test: the R7 "Cold lab 24 Oct → ON_TRACK with '2 of 3 outcomes have a target'" case.
- There is none, and no golden has a non-null `target_note`.
- `row_nodes` (`board.py:42-66`) has no unit test.
- Fix 1 (`mini.py:442-450` `_lead_findings`) has no test for the other-mechanism case.
- Fix 2 (`ev_priced`) is covered only by the golden.
- **Fix:** add the R7 case, a `row_nodes` kpi/days-line selection test, an `_lead_findings` negative test, and an EV priced/unpriced `not_measured_text` test.

**M3. Removed tests: part of the coverage is lost.**
- These are truly superseded:
  - The pace, too-early and missed texts. `test_ch6_evaluator.py:69,75` and `test_ch6_claims.py:64-65` assert them.
  - The conflicting-day test. That rule now lives in the producer.
- These are not covered anywhere now:
  - The board-level path from an MG-1 snapshot verdict to the row state.
  - The row state (ON_TRACK, WATCH, UNKNOWN).
  - The "Met" / "Behind pace" confidence chips.
  - `objectives_wire` `MET` (removed tests 1 and 3).
  - The OPPORTUNITY state and the `potential` chip with no objective (test 2). `test_ch6_contract.py` checks only that a `potential.` key exists.
- The packet lists six removed tests. A seventh was also removed, `test_ch6_claims.py::test_mg1_text_equals_the_board_rule` (handoff 2). It is legitimately superseded, because `mg1_reading` is deleted, but it is not listed.
- **Fix:** add one composer-level MG-1 test with snapshot rows: MET → ON_TRACK with a "Met" chip, BEHIND_PACE → WATCH, no objective → OPPORTUNITY with the chip. H2's L2m bullet 1 would also cover it.

**M4. `days_line` dates a single no-data day by the board's last day.**
- `board.py:312` passes `facts.day` (the window's last day, `read.py:413-415`) to `days_line`. That prints "No readings on {day}" whenever `expected == 1 and no_data == 1`.
- In a multi-day window with one expected day, that is the wrong date. An example is an EV window that covers non-operating days.
- Today's EV boards are within one day (the golden window is 08:00–16:00Z), so this is latent. But the route accepts any `from`/`to`.
- **Fix:** carry the no-data day in the claim, or pass `day` only when the window is one local day.

**M5. The price lines are taken from the board's declared price, not from the rows' own price revision.**
- `energy_basis` (`outcomes.py:253-270`) collects the rows' revision ids. With 0 or 1 revision, it prints `inp.price`: the mini board-day price, or the EV overview `tariff_value`.
- If the single revision on the counted days differs from that price, "{kWh} kWh × {price}" will not reproduce the figure. That happens when the price changed at `hi` and `hi` is not counted.
- `test_ch6_contract.py:41-43` even passes rows with amount 1+1 against 5 kWh × 0.5 and still accepts the line.
- **Separately:** the fuel line prints the unrounded `quantity.low/high`, while the amount shown is the outward-rounded `display` value. No test runs the fuel line on a real consequence body.
- **Fix:** only print `price` when its revision id equals the rows' single revision; otherwise use `price_several` or no line. Assert kWh × price ≈ amount in a test. Round the litres as `dispatch.py:735-736` does.

## Low

- **L1.** The branch does not contain current main. Main is at `d711ca8b7` and includes the CH-9b3 merge `7a89f58f0`. `git merge-tree --write-tree HEAD main` is clean, and no file overlaps the slice. Still, merge main and rerun the scoped set before merging.
- **L2.** The GrowParts vitest uses invented copy ("Target 120 kWh", "Checked 3 of 7 days") instead of server vocabulary, so it would not catch a copy regression.
- **L3.** `row.target_note` counts NOT_MEASURED and NOT_APPLICABLE outcomes in `m`. For example, EV-2 can never have a target. This is a preference; confirm with the Architect.
- **L4.** `outcomes.py` keeps an empty-line block (`:304-306`) and a stray import order. `board.py:61` has a long line with embedded whitespace. These are cosmetic.

## Items checked and found correct

- **`POTENTIAL_STATES`:** defined by exclusion over `TRANSITIONS` (`outcomes.py:33-41`). It is shown for OPEN, RECURRED, REOPENED, CHANGE_APPLIED and ACTION_IN_HAND, and hidden for RESOLVED_MONITORING, CLOSED and WITHDRAWN. Tests: `test_ch6_evaluator.py:221-241`. The mini headroom words and short value follow `potential_shown` (`mini.py:464`). The R13 signal is OPEN or RECURRED only.
- **Days and basis:**
  - The potential's days come from the study's `day_grades`, or NOT_KNOWN (MD-CH6-4).
  - With no objective, the kpi reads "No target set yet" with `days=None`.
  - A low-data day reads "Not known yet" with a days claim (`test_ch6_evaluator.py:320-322`).
  - The on-screen days line has the defects in H4 and M4.
- **Price-line copy:** "{kwh} kWh × {price} {cur}/kWh", "{kwh} kWh at {n} declared prices over these days", and "{lo}–{hi} L × {price} {cur}/L", or omitted with no price (a Known Deviation). The copy is as ruled; the sourcing caveat is M5.
- **Lead-money-head mapping:** gated on `mechanism == "GENERATOR_SUPPORT_CANDIDATE"` (`mini.py:442-450`). Correct by inspection, but untested (M2).
- **EV wording:** restored through `ev_priced`. "Needs a published charging tariff" now shows only when the window is unpriced (`board.py:780-783`), and the golden's not-measured text equals main.
- **Golden diffs:** status /4; `nodes`, `days_line` and `target_note` added; EV `headline_money` null because the fake rows are LOW; Cold CC-1 MISSED claim. They are as the packet says.
- **Test fakes:**
  - The Kobo opportunity `state: OPEN` and `status: SUPPORTED` are needed by R13 and Q1, and are fine.
  - The EV `headline_money` null is consistent with Q4, but it is the visible form of H3.
  - The `complete_rows` additions are needed by R6.
- **CH-6a1 Lows L1–L3 are fixed:**
  - L1: the day grade comes from the one `day_grade` rule.
  - L2: money comes only from COMPLETE or PARTIAL day grades.
  - L3: an amount with no currency is NOT_PRICED.
  - Each has a test (`test_ch6_evaluator.py:264-285`).
- **`judge` and `judge_month` are unedited**, and `objectives.py` is not in the diff.
- **L3 rules:** `policy_versions.status` /3 → /4 (R7), EV 20 Oct MET → NOT_JUDGED (R6), and EV Grow money null (Q4) are the intended rulings. The Kobo MG-1 change is not as R5 predicted (M1).

## Checks I ran (at `f1beed6d9`)

- **Scoped pure backend tests** (run-host-tests, 19 files):
  - Files: ch6 ×4, ch5a1 board contract, ch5a2*, ch5b_why, out_b1 ×2, out_b2 ×2, out_b3, out_d4, walk1_3b, out_a1, out_b4_imports, walk1_productive_sales.
  - Result: **447 passed, 6 failed** (H1), 12 s.
- **L2m:** `test_ch6_nodes_postgres.py` and `test_out_d5_objectives_postgres.py`, through `tools\run-host-tests.ps1` with the wrapper's default `127.0.0.1` `assetops_test`. Result: **6 passed in 304 s.**
  - A first attempt with a hand-set `postgresql://` URL failed on the SQLAlchemy driver after 792 s. That was my setup, not the slice.
- **Frontend:**
  - `npx.cmd tsc --noEmit`: exit 0.
  - `npx.cmd vitest run` on outcomeBoard.test.tsx, moneyText.test.ts and estatePortfolio.test.tsx: **3 files, 99 passed.**
- **Guards** (with `ASSETOPS_GUARD_PYTHON` set):
  - A `check-architecture.ps1`: passed. Without the variable it fails, because no interpreter is found; that is an environment issue.
  - W `check-agent-workflow.ps1`: passed.
  - V `node --test tools/checks/test_mock_deviation_labels.mjs`: 14 passed. Guard V checks labels that exist; it cannot see the missing MD-CH6 labels in H4.
- **Estate guard self-tests:** `pytest tools/checks/test_estate_guard.py -k …`, in 4 parts, run directly with absolute PYTHONPATH: **15 of 15 passed** (4 + 5 + 2 + 4; about 21 min). These are the self-tests the builder could not run.
- **Merge with lane 2:** `git merge-tree --write-tree HEAD main` is clean, and the CH-9b3 files do not overlap this diff (L1).

## Not verified

- The L3 and L3m clone results. I did not clone, per the brief; the packet's numbers are claims.
- The production build and the full frontend suite (not run).
- Layout evidence at 1440 and 390 (not run by the builder either).
- The full backend suite (not run, per policy).

---

# Re-review (R2a+R2b)

- Reviewer: fresh Claude, read-only. Head `4342c11cd`, worktree `AssetOpsV1-ch6a3`. Diff `f1beed6d9..HEAD -- ':!.agent'`. Judged against H1-H4, M1-M5, L2/L4 and CH6a3-R2.

## Verdict: REVISE (one small item, M-R1 below; everything else is closed)

## Findings

**M-R1 (acceptance gap, Medium-High). H2 is only partly delivered on `mechanism_db()`.**
- `backend/tests/test_ch6_mechanism_postgres.py` proves the Kobo earnings D7-D13 (Σ stored money), the price line (kWh × price == amount), ONE-SOURCE on D13, and MG-1 D13 (`checked_days` and `judge_month` by recomputation). Four non-vacuity mutations are in the test itself.
- CH6a3-R2 H2 also said "CH-6a3 must prove now": the SUPPORTED potential carries its money line (Kobo D13), and MG-2 D11 MISSED / D12 MET. Both are Kobo, so MD0-S2 does not excuse them. The packet's "not asked in this round" is wrong: the ruling asked for them.
- The potential's money line and the MG-2 verdicts are therefore still proven on fakes only (`test_ch6_evaluator.py`).
- Cold D3 and EV D9 are legitimately out: MD-0 is Kobo-first (MD0-S2). The EV ONE-SOURCE case on the stored-row fake in `test_out_b3_cold_ev.py` is accepted.
- Fix: add the D13 potential value and money recompute plus MG-2 D11/D12 to the same test (0.25 or less), and list the Cold/EV bullets as moved with the MD0-S2 reason.

**Low (no action needed).** The "complete meter record" wording on the EV known path (`ev.py:237,298,314`) is also printed for a PARTIAL day. Wording only; confirm with the Architect.

## Closed, with what I saw
- **H1.** `test_walk1_productive_sales.py` passes; 25.25 and 42.08 USD present; LOW-day case `test_low_day_states_nothing_but_not_known_with_its_days_line` present. No test deleted. Removed asserts are repointed to the claim (`nodes["MG-1"]["kpi"]` + `judge_month`).
- **H3.** On the clone, all 13 Kobo/EV/Cold day boards: 0 rows with NOT_KNOWN earnings plus a kWh, "declared" or "complete meter record" text. EV golden contributor and subline now read "Not known yet" / null.
- **H4.**
  - Each part has its own `days_line`, and no row-level `days_line` remains (0 across the 13 collected boards).
  - The Target part is always present ("No target set yet" + "No target, so no days are judged yet"), and the other two parts are server-filled.
  - `.ob-grow` is `repeat(3,minmax(0,1fr))` with an 8px gap and one column at 760px, matching v70 `:213-215`; `.ob-part` is bordered at 6px.
  - R701-R704 are registered, and MD-CH6-1/2/3/7 are labelled in `OutcomeBoard.tsx` and cite v70.
  - Golden diffs: I computed a structural old-to-new diff for all 8 files. Every change is one of: row `days_line` removed; per-node `days_line` added; absent node filled. Plus the R2a EV changes (contributor, subline). Nothing else moved.
- **M1.** The packet's clone evidence is credible, and my own clone reproduced it: Kobo 30 Oct is 42.08 USD, subline "168.3 kWh", claim kWh 168.333 (price line "168.333 kWh × 0.25 USD/kWh" per `price_lines`). EV reads "Not known yet" because the stored days are LOW (a coverage result).
- **M2-M5, L2, L4.**
  - M2: `test_ch6_r2a_rows.py` has the R7 Cold-24-Oct, row_nodes selection, `_lead_findings` negative and EV priced/unpriced cases.
  - M3: the MG-1 composer test is present.
  - M4: the day argument is passed only for a one-day window.
  - M5: price shown only when its `revision_id` matches the rows' single revision (`outcomes.py`), litres rounded half-up as dispatch does, and tests are present.
  - L2: the vitest uses server vocabulary.
  - L4: cosmetic items fixed.
- **Module list.** `financials.recompute` is imported by the already-listed `consequence_read` (`:38`), and by `cold_recompute` and `composition`. W6 on my clone: 46 requests, 0 violations, 136 modules, `unlisted_modules []`. The addition is justified.
- **Mutations I made (reverted; `git status` clean).**
  - Per-node `days_line` set to None: 7 failed.
  - Potential fill given a days line: 6 failed.

## Checks run
- Scoped pytest, 10 files (walk1_productive_sales, ch6_claims/contract/contributions/evaluator/r2a_rows, ch5a1_board_contract, ch5a2_contract, ch5a2b_claims, out_b3_cold_ev): **208 passed**.
- Postgres `test_ch6_nodes_postgres.py` + `test_ch6_mechanism_postgres.py` via `run-host-tests.ps1` (127.0.0.1): **4 passed, 273 s**. The MD-0 states template was stale (fingerprint bcdb2d1a vs 89ca40e5), so I rebuilt it (6 parts); the standard rotation dropped the oldest template cd95a2e4.
- `tsc --noEmit`: exit 0. Vitest outcomeBoard (26), estatePortfolio + estatePortfolioRoutes (60): all passed.
- Polish clone `rev6`: create, migrate, backfill a-d, settle, W6 (46 requests, 0 violations, 0 unlisted), `fresh` (43/43 equal a fresh compose), collect (85 requests, all 200), `check --expect expected-today.json`: **0 new** in every rule (COH-2 2/2 and COH-7 8/8 expected; COH-17 = 0; self-check 10 pass, 0 fail). Clone dropped.
- `check-all.ps1`: see the result line below.
- Not verified: layout evidence at 1440 and 390 (not run; the packet says it is owed at E5); production build.
- `check-all.ps1 -Python <plan2 venv>`: **All 17 guards passed** (estate guard self-tests 15 passed in 20 min; ratchet totals api 12, href 24, lit 70, cmp 51, code 3).

## Coordinator closure (M-R1, 1d24e70f3) — ACCEPT for merge
- D13 SUPPORTED potential money line now recomputed on `mechanism_db()` (kW × 1 h × declared price), planted wrong value fails.
- MG-2 D11/D12: on `mechanism_db()` the Performance comparison port is closed, so MG-2 honestly reads NOT_JUDGED with "Not known" fuel — no false figure shown; `check_fuel_line` proven to fail on a synthetic claim and the test pins NOT_JUDGED. The real-data litres × fuel price proof moves to DD-1b2 F-THREADS (combined dataset, where the comparison report exists), consistent with CH6a3-R2 H2's "real-data end to end → DD-1b2".
- Builder: the two Postgres files 4 passed.
