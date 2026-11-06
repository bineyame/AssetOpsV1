# Review packet: CH-6b1 (estate chain and summary from one composition), lane 1

Branch `task/CH-6b1-estate-chain`, worktree `AssetOpsV1-ch6b1`. Sheet: `AssetOpsV1-plan2\.agent\build-sheet-CH-6.md` (CH6b1-R, CH6b1-R2). Size 2.0 units. USER_REVIEW: none required.

## Outcome
`summary` and `/api/estate/chain` come from one composition: one batch snapshot read (`seed_snapshots`), per-Site `window_days` nodes, one function (`portfolio_parts`) for per-Site rows/earnings and `money_total`. `LATEST_EVENT`, `latest_window`, `_event_window`, `_prefetch` are deleted; cold/EV are judged on the requested window (PERIOD); Kobo DAY. CH6b1-R2: a reading-based verdict with no kpi record keeps its last-day verdict and its days line names the day ("31 Oct · 1 of 1 day checked"; `days_line(..., named=True)`, `site_outcomes/board.py` `row_nodes`, `chain/vocabulary.py`). See `.agent/CH-6b1-handoff.md` for the build commit list.

## Acceptance / evidence
- L0 `backend/tests/test_ch6b_estate_chain.py`: 17 pass (15 earlier + R2 test run in Addis and Etc/UTC). Non-vacuity: with the named-day branch switched off, both R2 cases fail (2 failed, 15 passed); reverted. Earlier mutations M1-M5 (handoff) each failed the suite.
- `test_ch5a1_summary_ledger::test_summary_reads_each_key_at_most_once`: cause commit `c69cc6835` (CH-6a3 deleted `_productive_month`, the second month-to-date composer read, so the memo hit the test counted no longer exists; there is exactly one `productive_readings` read, no double read). Test now asserts the single read and no hit; what it checks (max one read per key, one executed read) is unchanged. Passes.
- L2m `test_ch6b_estate_postgres.py`: 1 pass (374 s, earlier). Postgres files via `run-host-tests.ps1` (DB 127.0.0.1:55432): c3 1 pass (after rewrite, KD-4), c4 1, w303 portfolio fixture 2, cov_partial 1, ch5a2 chain api 6, ch4 opportunity 3, qw2 many 1: all pass. (Handoff names `test_cov_partial_portfolio_postgres` and `test_ch4_opportunities_postgres`; the real files are `test_cov_partial_postgres.py` and `test_ch4_opportunity_postgres.py`.)
- Guards: agent-workflow passed; architecture passed; navigation truthfulness passed; vocabulary guard `test_out_b2_vocabulary.py` 4 pass after its node-sample gained `total/site/text` (extended, not loosened). `measure-mock-panels.mjs`: not run (needs a browser; frontend untouched). Full suites and prepare: not run (localised-only rule).
- L3 polish clone `ch6b1` (dropped): create, migrate, backfill a-d (17 s), settle (99 s), W6 (46 requests, 0 violations; 2 modules added to `config/chain/stored-composer-modules-v1.json`: `work.composition`, `work.domain_action`, reviewed diff, rerun 0 unlisted), `fresh` store on 43/43 equal a fresh compose, collect 85 requests all 200, COH check: 0 new (COH-7a on window_basis/window RESOLVED), self-check 2 pass 0 fail. Work dir copied from `AssetOpsV1-polC\var\polish_full` (story/days/keys). Perf: summary.seed_snapshots 37.5 ms on the first W6 `/api/estate/chain` call (under the 50 ms line).
- Portfolio week (25 Oct to 1 Nov): `money_total` "At least 84.16 USD estimated income, from checked days · not billed or collected", basis CHECKED_DAYS, days 0 complete / 3 partial / 4 no_data of 7. Lines: "Kobo mini-grid: 84.16 USD over 0 of 7 days checked · 3 partly checked" and "Depot Charging Hub: not known yet". Kobo earnings claim 84.16 USD (336.666 kWh at 0.25 USD); EV "Not known yet"; Cold none. 84.16 + (EV excluded, lower bound) = total, so the lines add up. Window basis: Kobo DAY, Cold and EV PERIOD; overview_href `/sites/KOBO-001`, `/sites/COLD-LAB-001`, `/sites/EV-LAB-001/ev`.

## Known Deviations
- KD-1 (CH6b1-R Q6, confirmed): Cold 7/7 and EV D9 are L0 only (`mechanism_db` is Kobo only); real-data cross-Site agreement is the L3 clone and COH-17 in CH-6b3.
- KD-2 (MG-5, CH6b1-R2): reading-based verdicts with no kpi record are judged on the last window day (`chain/outcomes.py:136-140`); now labelled with the day. Judging over every window day is BL-17.
- KD-3 (confirmed): the `states` template holds D1-D5, D10-D14 only, so Kobo D7-D13 reads 4 of 7 (D7, D8, D9 NO_DATA), not §B5's 6 of 7. L2m asserts counts recomputed from stored rows (Kobo earnings 239.00 to 299.00 USD after `late_fill` D7; days 4/7 to 5/7). The template is not rebuilt to reach 6 of 7.
- KD-4 (new, Architect to confirm): with `LATEST_EVENT` gone, `test_out_c3_repeat_visits_postgres` (cold, sub-day W5-01 evidence window 16:00-17:05Z) over the whole day or week summary returns the Cold cost row UNKNOWN with no repeat warning (the Site board over that day also reads UNKNOWN, cold overview/findings empty). The test previously expected NEEDS_ATTENTION and a REPEATED warning on day and week; it now asserts PERIOD basis, window equality, plain href, UNKNOWN and no repeat warning there. A sub-day evidence window is not reachable by the summary (INVALID_WINDOW on a 65-minute window). Product consequence of CH6b1-R Q2; real polish data (whole-day windows) showed no COH change.
- Handoff file names for two Postgres tests were off (above). Frontend untouched (CH-6b2): `estateClient.ts:627` type still lists `LATEST_EVENT`; `portfolioFixtures.ts:406-410`.

## Mock to new (v70 `pfGrowParts`, index.html:421)
| Mock | New |
|---|---|
| Target: "No target set yet at any site" | unchanged (CH-6b2 frontend) |
| Estimated income: "Kobo: $7.50 over 3 checked study days ($2.50 per window) · Depot: $36.00 on 6 Oct · GreenHarvest: not measured yet" | `income.total` "Estimated income from checked days: {total}" or `income.at_least` "At least {total} estimated income, from checked days" plus `income.site` "{site}: {text}" per Site and `income.site_not_known` "{site}: not known yet"; per-Site text is the Site's own earnings claim ("84.16 USD over 0 of 7 days checked · 3 partly checked") |
| "Different days at each site, so not added together" | removed: all Sites share one window and the total is the sum of per-line rounded values, "not billed or collected" kept |
| "$" and "per window", single study day | "USD" suffix, days counts from the claim |
| GreenHarvest "not measured yet" | no line (Cold has no income record) |

## CO-6 PERIOD change
`tools/demo_combined_finish.py` :416 (CO-6) `basis.get(COLD) == basis.get(EV) == "PERIOD"`; :458 (CO-6b) Cold PERIOD; :460 EV PERIOD (was `LATEST_EVENT` unless no event). Only those lines changed. CO rows not re-run here (needs the demo DB).

## Residual risk
Row state on cold/EV now follows the requested window (KD-4). MG-5 line wording ("1 day" singular only in the named form; the unnamed form keeps "1 of 1 days checked" for existing fixtures).

## Fix round R3+R4 (builder 2, Sonnet)

Rulings: CH6b1-R3 (cold/EV rows read the latest selected window CONTAINED in the requested window; board window stays the request) and CH6b1-R4 (every node claim carries `span {first,last}`, additive; the days line names the span only when it differs from the window). Landed in WIP commit 287e5ff6b plus this round's test and low commits.

**Tests repointed (no assertion's intent weakened):**
- Goldens regenerated by the files' own regen path (`test_ch5a1_board_contract` x4, `test_ch5a2_contract` x5): the diff is only the added `span` objects (checked by a line-diff).
- `test_ch5a1_board_contract::test_fixture_ledger_has_no_deleted_read[cold,ev]`: the estate fake allows exactly `site_selected_windows` (recorded in `WINDOW_READS`), every other estate read still goes to `Never`; the ledger test now asserts exactly one window read for cold/EV and none for Kobo.
- `test_qw2_reuse` (4): `SingleEstate` counts window reads (`single`) apart from readiness reads (`readiness`, must stay 0); plain estate = 2 window reads (cold+EV), batched = 1 batch / 0 singles, failing batch = falls back to 2 singles with an equal response; a board = exactly 1 window read, 0 readiness.
- `test_out_w2_summary_window` (6 touched): the fake `board` takes `windows`; the `Estate` fake serves a batch; asserts one batch of the cold/EV codes only (Kobo none), the board window stays the request, the contained event reaches the board.
- `test_ch6_evaluator::test_cc1_chamber_no_data_is_not_judged_and_met_when_read`: NOT a regression. The mini CC-1 record kpi is the board day's reading (R4 H2), so its days are counted over day 2 (no row: NOT_KNOWN), not days 1-2 (CHECKED_DAYS). The test now asserts NOT_KNOWN, `span == (day 2, day 2)` and `no_data == 1`; value and text unchanged.
- `test_out_c3_repeat_visits_postgres`: back to NEEDS_ATTENTION + exactly one REPEATED on day and week (PERIOD basis, plain href), plus L4: the Site board over the same day/week gives the same OPTIMIZE_COST state, one REPEATED, same window. The window spy now asserts only COLD-LAB-001 window reads, each finding the W5-01 window.
- `test_ch6b_estate_postgres` (L2m): the Q1 check is by span (spanned node `days.expected` = its span's day count; unspanned = 7); both the window-wide and the narrower sets are asserted non-empty.
- `test_out_c4_ev_warnings_postgres`: passes unchanged.

**Checks run:** localised only. L0 `test_ch6b_estate_chain` 20 pass; the repointed unit files above pass. Postgres via `run-host-tests.ps1` (127.0.0.1:55432): c3 1 pass (59 s), c4 1 pass (73 s), L2m 1 pass (580 s). The MD-0 template was stale (aad4a485d2be != ca0b47e0e2f7): one `mechanism_dataset.py build --variant states` rebuild (5 resumed passes, 1588 s seed), `assetops_mechanism_tpl_ca0b47e0_test`.

**Clone ch6r (R3 check, then dropped), Portfolio, Cold / EV, states (old = before R3/R4, new = this code):**
- Week 25 Oct-1 Nov: Cold old Cost UNKNOWN, Protect UNKNOWN, Assure UNKNOWN; new Cost NEEDS_ATTENTION, Protect NEEDS_ATTENTION, Assure WATCH. EV old Grow UNKNOWN, Protect UNKNOWN, Assure UNKNOWN; new Grow WATCH, Protect NEEDS_ATTENTION, Assure WATCH (Cost NOT_MEASURED both).
- Day 31 Oct: Cold old all UNKNOWN; new Cost NEEDS_ATTENTION, Protect NEEDS_ATTENTION, Assure WATCH. EV unchanged (no event that day: Grow/Protect/Assure UNKNOWN), as the ruling requires.
- Surface that reached the failure before: Portfolio and the Findings/evidence page showed Unknown for a week that held a real cold failure night and the EV fault Tuesday.
- W6 (`chain_watermark_guard`): 46 requests, 0 non-200, 0 file violations, unlisted_modules [], 17 estate-window fallbacks (see L3). `chain_response_probe fresh` (store on): 43/43 equal a fresh compose. Collect 85 requests, all 200.
- COH check: the new bundle reports 2 COH-2 findings (month window: Cold and EV, Action answers a Finding whose Portfolio row has no action_id) and "self-check 0 pass 2 fail". The same two findings appear on the OLD bundle (`var/ch6r_bundle`, before R3/R4) run through the same checker, so R3/R4 added none, but the instruction "COH 0 new" is NOT met on this clone. Needs the Architect/reviewer: either a clone-specific baseline (this clone's work dir `ch6b1work` is from an earlier polish copy) or a real pre-existing COH-2 on the month window.

**Lows:** L1 docstrings in `tools/demo_combined_finish.py` now say PERIOD. L3: every fallback logs and counts: `summary.window_fallback` (batch refused, no batch, multi-tenant, board read failure) and `summary.seed_fallback`; the seed no-reader/multi-tenant path now also logs (it only counted). Fallback counts on W6: seed 0, summary batch 0, board-level window 17 (all Site boards over sub-day, non-midnight windows, e.g. the W5-01 65-minute board: the estate refuses INVALID_WINDOW and the board reads the requested window, which equals the event). Mutation proofs (committed first, reverted after): `days_line` always naming the span -> 3 L0 tests fail; the contained filter removed (`return list(windows)`) -> `test_a_contained_event_is_read_and_an_outside_one_is_not` fails.

**Known Deviation (new): event window not named in the days line.** R3 asks for "26 Oct 16:00-17:05" in a cold/EV days line. Not built: the cold/EV node claims' `days` are counted over the requested window's days (chain rows), not over the event, so naming the event beside "k of m days checked" would pair a window of hours with a day count of the week, against R4's one-source rule. The facts (Findings, cost, repeat warning) are the event's; the days line is the window's. A correct line needs the node claims to be counted over the event (a span of instants), a wire change for the Architect.

**Guards:** `tools/check-all.ps1 -Python <plan2 venv>` run once on the final revision: 17 of 17 PASS (architecture seams, estate self-tests, navigation, workflow, dependency registry, delivery and mock-gap fixtures, missing-claim scan and fixtures, evidence width, mock deviation/vocabulary, screen ledger, chain coherence fixtures 108, event register 12, chain graph, perf budget 8/8, frontend ratchet). Output: `var/guards3.txt`.

## Fix round R5 (CH6b1-R5, Architect 24)

- **Dated lead.** When the contained event window (R3's `event_window`) is shorter than the requested window, the cold/EV Protect lead gains " · 26 Oct 16:00-17:05" in Site-local time (UTC plus the existing suffix if the zone is unavailable). Template `cold.EVENT_DATED` (in `cold.COPY`, so guard V scans it); built by `cold.dated_lead`, applied in `read.py` `compose`. Copy only, no wire change; the days line stays the window's. A None lead is left alone (the board uses the lead title).
- **L0** `backend/tests/test_ch6b1_r5_dated_lead.py`: week window shows "26 Oct 16:00-17:05"; event-length window does not. Non-vacuous: forcing the condition False fails the week case; forcing it True fails the event-length case (both reverted).
- **COH-2 month findings** (COLD-LAB-001, EV-LAB-001) are the `expected-today.json` entries COH-2 / month, register I-09 (owner DD-1), matched by rule, Site and window; the old-code bundle shows the same two. Not CH-6b1's to resolve; the "0 pass 2 fail" self-check is Action-UUID subjects from the `polish_full` baseline against the `ch6b1work` copy. No baseline change. "0 new" met in substance.
- **Backlog:** BL-21 (count claims over the event itself) in `.agent/backlog-post-demo.md` (spec said BL-19; BL-21 is the next free id).
- **Checks:** scoped tests (r5, w1, w2, b2 vocabulary, b3 cold/ev, ch6b estate chain) 67 passed; c3 Postgres test via `run-host-tests.ps1` (127.0.0.1:55432) 1 passed; guards: see below.
- Guards: V (`test_out_b2_vocabulary`, in the 67), A (`check-architecture.ps1`) and W (`check-agent-workflow.ps1`) PASS. `check-all.ps1` was not completed (stopped after 30+ min with no output).
