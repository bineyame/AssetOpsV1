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
