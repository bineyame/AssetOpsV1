# Review: CH-6b3 coherence, proofs and the packet

Branch `task/CH-6b3-coherence-proofs`, HEAD `8b168ddaa`, against main `9b1c53ae3`. Reviewer: fresh Claude, not the author.

## Verdict: REVISE

The builder's work matches the rulings, and I found no defect in the COH rules, the Q4b code or the four test fixes. The blocker is H1. On the Portfolio's week and S windows the page still contradicts itself about the Kobo fix. Q4b moved that contradiction rather than removing it, and the ruling's premise that "the week and the month agree" (CH6b3-R2 BL-26) does not hold on the drained bundle. H1 needs an Architect ruling before a builder can fix it. M1 and M2 are older client-visible number conflicts that are not in this diff. The Architect should say whether they are fixed here or separately.

## Findings

### High

**H1. Week and S: "Fixes confirmed · 0" and "None confirmed" sit beside "Verified" and "1 verified result".** (Acceptance gap against Q4b's stated aim.)

Client-visible values in `var/ch6b3r2_bundle`, week and S (S is the same unless noted):

| Surface | Reads | Source |
|---|---|---|
| Assure card | "None confirmed on the days checked" | claim, `count.verified_results` = 0 |
| Progress panel | "Fixes confirmed · 0" | the same claim (Q4b) |
| Portfolio table, Kobo row | Group Monitor, workflow "Verified", reason "Change verified on example data; watch for it coming back" | `portfolio.{w}.p1` `rows`: `thread.state` RESOLVED_MONITORING, `state_day` 2026-11-01 |
| Progress panel drawer ("Inspect basis") | "Action ACT-001 · fix confirmed" | `progress.rows[].verification_outcome` VERIFIED, `recorded_at` 2026-11-01T13:00Z, after the window ends |
| Assure "Why?" | "Kobo mini-grid: 1 verified result" | `why_estate.{w}.ASSURE_PERFORMANCE` `text.comes_from` |
| Kobo board for the window | Assure "1 verified result", while Optimize reads "Before the change on 1 Nov · after the change: not judged yet" | `board_summary.{w}.KOBO-001` |
| Pulse | "3 priority sites" counts Kobo (2 on S), yet Kobo's only row is under Monitor | Q4b |

Failing scenario: a client opens the Portfolio on the week, which is a window the story links open and BL-26 tells DS-1 to stay on. The cards say no fix is confirmed. The table below them says Kobo's change is verified. No click is needed. "Why?" on the Assure card then says 1 verified result.

Causes, from the code:
- The rows read thread state on a different day from the claims. `attach_threads` uses `day_at = req.to - 1 µs` in Site-local time (`estate/portfolio.py:161`), which is 1 Nov in Addis. The claims use `window_day` (`chain/claims.py:80`), which is 31 Oct for a UTC-midnight window. So one window yields RESOLVED_MONITORING on the row and ACTION_IN_HAND in the count.
- `workflow_label` and placement come from the Action's verification outcome, not the thread state (`estate/portfolio.py:227-232`, `estate/placement.py:154-156`). Aligning the day alone will not change "Verified".
- The Assure headline counts Actions whose `verification_state` is VERIFIED with no window-day limit (`site_outcomes/mini.py:475,480`).

The packet saw part of this. Its "old priority count" cause notes that Kobo "read RESOLVED_MONITORING", but it treats that as old behaviour, and the row still reads it at this head. COH-17 cannot catch this: L1 compares the legacy fields with the claim, W1 compares `say` with the row headline, and no rule compares the row or the Assure text with the claim.

Fix, which is an Architect decision because it reverses a ruling on one side or the other. Either:
- (a) Keep CH6b3-R2 step 4 (0 is true for a window ending 31 Oct). Then rows, the progress drawer and the Assure headline must read as of the window's last day. CO-3 asserts the verified "earlier" line on the S board, so the board side needs an explicit carve-out or a CO change. Or
- (b) Word the card so it is plainly window-bound, and state on the row that the verification came after the window ("verified 1 Nov, after this window"). Then the two statements stop conflicting. This is the smaller change, but it is new copy and needs a mock check.

Whichever is chosen, re-state BL-26: the week does not agree with itself. A one-line demo-script restriction to the month alone would also work if the Architect accepts it, but the story links open the week.

### Medium

**M1. One card shows "0 of 7 days checked" and "3 of 7 days checked" for the same Site.** Not in this diff (CH-6b2).
- Week, Assure card: `days_line` "Kobo mini-grid: 0 of 7 days checked · 3 with too little data, not counted", and `card_notes` "… · 3 of 7 days checked at Kobo mini-grid". Protect shows the same pair. Month: "0 of 31" and "8 of 31".
- Both render without a click on the same card (`frontend/src/estate/PortfolioOutcomes.tsx`, `oc-pfdays` and `oc-pfnote`). The note comes from `card_notes` / `checked_days_clause` (`estate/portfolio.py:659-670`), which counts coverage days, not `COMPLETE` grades.
- Fix: drop the checked-days clause from `card_notes` now that the card has its server `days_line`, or align the two definitions.

**M2. The estate "Why?" days line disagrees with the card, and names 32 days in a 31-day window.** Not in this diff.
- Cold, week: the card reads "0 of 7 days checked · 2 with too little data", "Why?" reads "0 of 8 days checked · 8 with too little data, not counted". Month: "0 of 31 · 3" against "0 of 32 days checked · 32 with too little data", then "Checking 32 more days".
- Cause: `why.py:249,264` reads the board's `facts.days`, the `local_days` of a UTC-midnight pair (one day more, CH6b1-R Q1), and `why.py:336` joins it into the estate text. No-data days are also worded as "too little data".
- CH6b3-R Q2 did not ask for this comparison, so it is not a builder miss. BL-23 and BL-24 cover nodes and earnings days, not this line.
- Fix: build the estate Why? days line from the summary's `window_days` Site days, as the card does.

### Low (do not block)

- **L1.** `backend/tests/test_ch6b_estate_postgres.py:158-160`: the test name still says `optimize_row_reads_act_k1_on_d13`, and the docstring still says the bullet "is not met" and cites KD-3b, though the bullet was restated. Rename when next touched.
- **L2.** The packet and the ruling say S+1 is "as CO-2". The S+1 assertions are in **CO-1b** (`tools/demo_combined_finish.py`, `co1b`). CO-2 checks only day S.
- **L3.** C2 passes if a card and its count key are both absent (`{} == {}`), and it still tallies as compared. Not the case on real bodies.

## Questions from the dispatch

**COH-17 and COH-18 can fail.** I planted breaks in memory on the real drained bundle, not only on the fixtures. C2, C3, M1, M2, M4, M5, V1, V2 (state, and headline on Cold month), V3, V4, L1 (both fields), W1, W2, R1 (Kobo day and Cold span) and R2 all fired. M3 and M6 are covered at L0 only. M4 also trips M1 and M5, and R1 cascades into R2, as expected.

**Compared and skipped mean what the packet says.** Clean run: COH-17 218/13, COH-18 21/0, 0 findings. The 13 skips are the 13 day windows, one skip each for their absent Portfolio body, which the ruling makes estate-only. COH-18's 21 is 3 windows × (3 Site tallies + 4 count claims).

**The verdict rows judge real values on the drained run.** Kobo Optimize is NEEDS_ATTENTION on week and S, and UNKNOWN / OBJECTIVE_NOT_JUDGED on month. Cold and EV rows carry real states except EV on S, where the day is not expected. No rule was skipped or narrowed beyond the rulings. R3 and R4 run on L3m only, as ruled; with `gap_days=[]` on polish they would flag all 21 built days as non-COMPLETE, which is why they stay off there.

**Q4b is correct as code.** Both fields read the claims, and the null paths hold (`estate/portfolio.py:186-193,866-872`). The singular renders correctly by reading the code. Packet counts equal the bundle: confirmed 0/0/1, priority 3/2/2, open threads 4/3/3, opportunities 1/1/1, disrupted 2/1/2. I could not re-derive the old values, as no bundle holds them. The code path supports them. H1 is the remaining contradiction.

**The four stale tests were truly stale.** All three named commits are ancestors of base. `progress` did gain `f_rows` in `3cea423fd`; `link_ref` came with `1c3e3a075`; `count.sites_disrupted` with `6b4e682f2`. Each fix changes only the named line, and no expected number moved. I re-ran `test_w303_portfolio_comparison_postgres.py`: 4 passed, so the verified-count assertions are now reached.

**The KD-3b restatement is still a meaningful proof, in part.** The MG-1 half recomputes the verdict from stored rows on 3 or more COMPLETE days, which is real. The surviving Optimize assertion compares UNKNOWN with UNKNOWN on `mechanism_db()`, so it proves agreement only. The ruling prescribed that and put the verdict proof on the drained clone, where the table holds.

**Drained measurement: the bundle matches the packet's rows** (states, reasons, headlines, `critical_served` PARTIAL, thread lines). No PRODUCER_NOT_SETTLED on any Kobo board, and no PENDING `critical_served` on any `chain_day` body.

**S+1, Optimize UNKNOWN beside "Fix verified, monitoring (ACT-001)": not wrong, no finding.**
- UNKNOWN comes from `outcomes/status.py:96-97`: the objective reads NOT_JUDGED because the day is only partly checked.
- "Fix verified" comes from the Action's verification over the trial window ("checked over 09:00–10:00 on 1 Nov"), and the same line says "7 more fully checked days to close".
- These are two different questions, each answered truthfully. "No fuel cost estimated for this day" is also true. CO-1b asserts no PRIMARY_FINDING_OPEN and the line, and only returns `cost_state`, so the demo expects nothing else.
- The presenter should be ready to explain it. Wording polish belongs in the UI pass.

**L1 pipeline low (`origin_selected`) is closed.** Replacing `action_segment_for` with the default segment fails the new test, and it passes unmutated (I ran both). **L5:** report `tallies` are as stated, and the vacuous test exists.

**Scope is clean.** MD-CH6-5 is registered (R707) with its inline label, and the mock wording it cites is at `v70/index.html:421`. R705, R706 and R707 are the correct list. BL-08 items were not built. The `G-portfolio-grow-revenue` gap stays. Product code is identical between `6334641f5` and HEAD, so the drained run measures this head's product code.

**Test-count mismatch is explained; no test was lost.** Collected per file: the three files of run 1 hold 4 + 6 + 2 = 12, and the eleven files of run 2 hold exactly 215. The sum is 227. The ruling's 215 was the first run's total (4 failed + 211 passed), and that run's list included the comparison and `ch5a2` files, so it is a different grouping that happens to give the same number. The first log does not list its files, so I could not name the 10-test difference.

## Checks I ran

- `tools/checks/test_chain_coherence.py`, `test_w303_portfolio_workflow_labels.py`, `test_w303_portfolio_api.py`: 141 passed, 1 skipped (no database URL in that run; I did not identify which test).
- `test_w303_portfolio_comparison_postgres.py` through `run-host-tests.ps1`: 4 passed, 333 s.
- Architecture guard: passed. Agent workflow guard: passed. A first architecture run without `ASSETOPS_GUARD_PYTHON` printed "cannot run" messages; the result above is with it set.
- Mutation runs on `var/ch6b3r2_bundle`, and the reports `ch6b3_report`, `ch6b3m_report`, `ch6b3r2_report`: tallies 218/13, 111/11, 218/13; COH-18 21/0, 75/0, 21/0. PERIOD info table matches the packet.

## Not verified

- **Frontend:** the worktree has no `node_modules`, so `tsc --noEmit` and vitest did not run. `namesOnePrioritySiteInTheSingular` and the packet's 60 passes are unverified.
- The rest of the scoped backend list (`ch5a2`, `ch6b_estate_postgres`, run 2): collected but not re-run; the packet's results stand as claims.
- The clones, L3m and CO-1 were not re-run (dropped, or excluded by the brief). No browser view: H1, M1 and M2 are traced from bundle values to the rendering code, not seen on screen.
- Values are the polish build's. DD-1 data may change the numbers, but not the causes in H1.

## Residual risk the packet does not name

- `board.day_cold_failure_2026-10-31` reads UNKNOWN / PRODUCER_NOT_SETTLED on every measured row on the drained and undrained runs alike, while the S-window board for the same Site reads NEEDS_ATTENTION. So it is not a drain effect. The local-midnight window seems to matter. I did not establish whether any client link opens Cold on that window. The Lane 2 F-THREADS note covers Kobo days only; it should report Cold and EV story days too.
- Portfolio Cold rows read "No action agreed yet" in the month while ACT-000002 exists. This looks like the known COH-2 month entries already in `expected-today.json`, so I do not raise it. It does sit beside the Q4b count that treats that Site's thread as in hand.
