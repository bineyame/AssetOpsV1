# Review packet: CH-6b3 coherence, proofs and the packet (size 1.3)

Sheet: `.agent/build-sheet-CH-6.md` CH-6b3 entry, Scope cut, CH6b3-R (`:833`). Pre-flight: `.agent/CH-6b3-preflight.md`. Branch `task/CH-6b3-coherence-proofs`, based on main `9b1c53ae3`. Review of CH-6b3 only.

## Outcome

COH-17 now guards count, money, verdict, legacy and Why? values over estate windows. COH-18 proves Site and count `days` from per-day grades. Both report `{compared, skipped}`. The two legacy Portfolio fields read the claims, so "Fixes confirmed" and the Assure card no longer contradict each other. L3 clone: 0 new. L3m: 0 findings.

**KD-3b is closed by CH6b3-R2 (bullet restated). The drained L3 clone replaces the earlier L3 result, which judged UNKNOWN Kobo rows.** Size 1.3 (the four test fixes 0.1, the drained clone 0.1).

## Files

- `tools/checks/chain_coherence.py`: `_coh17_full`, `_coh17_money`, `info_coh17_period_nodes`, `coh18_day_grades`, `Collector.day_bodies`, `rule_tallies`, `load_gap_days`.
- `tools/checks/test_chain_coherence.py`; bundles `clean_full`, `coh18_day_grades`; `expected-mechanism.json` `gap_days`.
- `backend/assetops_backend/estate/portfolio.py`: `priority_site_count`, claims into both legacy fields.
- `frontend/src/estate/EstatePortfolio.tsx`: singular "1 priority site"; `estatePortfolio.test.tsx`.
- `backend/tests/test_w303_portfolio_api.py`, `test_w303_portfolio_workflow_labels.py`, `test_ch6b_estate_postgres.py`.
- `backend/assetops_backend/chain/vocabulary.py` (inline MD-CH6-5 label), `.agent/mock-departure-register.md` (R707).

## Acceptance

| Item | Status | Evidence |
|---|---|---|
| COH-17 rows C1-C3, M1-M6, V1-V4, L1 | Met | One planted-break test per row (L1 has three); all fail on the break, `clean_full` clean |
| COH-17 W1, W2 | Met | Wrong `say`, extra Site line, early-warning line alone gives 0 |
| Findings keep their one key (trap) | Met | `FINDINGS_CLAIM_KEYS`, test |
| PERIOD info rule, not failing | Met | Unequal days: no finding, listed. Equal days: `unexplained` true, printed as UNEXPLAINED |
| COH-18 R1, R2 | Met | Planted wrong-day mapping, wrong count `days`, missing date, null `days`, unstamped |
| COH-18 R3, R4, `gap_days` | Met | Listed and unlisted PARTIAL; CHECKED_DAYS in an all-COMPLETE window fails and passes with NO_DATA; none judged without `gap_days` |
| Pipeline L5, Q6: `{compared, skipped}`, zero compared fails | Met | Report `tallies`, printed lines, `vacuous` test |
| Pipeline L1 | Met | Closed in code by CH-5a2b. Revert-failing test added; proof below |
| Q4b server and singular | Met | `test_legacy_fields_follow_the_claims...`, `namesOnePrioritySiteInTheSingular`, L1 on real bodies |
| L2m MG-1 on >= 3 COMPLETE days | Met | Recomputed with `judge_month`: MET, 2156.000 kWh, 9 COMPLETE days |
| L2m Optimize row on D13 reads ACT-K1 | Restated | KD-3b closed by CH6b3-R2; verdict proved on the drained clone |
| L3 clone 0 new, COH-17 = 0, COH-18 = 0 | Met | Below |
| L3m 0 unexpected; CHECKED_DAYS rule R4 | Met | Below |
| Old → new table, MD-CH6-4/5/6, §B6 line | Met | Below |

## Checks

**L3 polish clone** `ch6b3` (dropped), revision `6334641f5` code: create and migrate 4 s; backfill a-d 20 s; settle 88 s; W6 133 s (46 requests, 0 non-200, unresolved [], untracked [], 0 file violations, unlisted []); `fresh` 231 s (43/43 equal); collect 190 s (134 requests, all 200: 31 `chain_day`, 6 `chain_span`, 12 `why_estate`); check against `expected-today.json`:
- COH-17: 0 findings, compared 218, skipped 13 (the 13 day windows have no Portfolio body).
- COH-18: 0 findings, compared 21, skipped 0.
- 0 new overall: self-check 2 pass (the known COH-2 month entries), 0 fail, 8 resolved (COH-7a). PERIOD info 4 items, 0 unexplained.

**The L3 result above is the undrained run and it judged UNKNOWN Kobo rows.** On that clone `critical_served` read PENDING on 7 of the 8 Kobo day bodies checked (the queued service work was never drained, CH-9 packet `:311`), so `day_settled` was False and every Kobo Optimize row read UNKNOWN / PRODUCER_NOT_SETTLED. COH-17's V rows compared those UNKNOWN rows, so they did not judge the demo's real verdicts. **The drained run below replaces it as the L3 result (CH6b3-R2 step 2).**

**L3 drained (replaces the above)** clone `ch6b3r2` (dropped), revision `2dfa838a9` code (same product code as `6334641f5`): create+migrate 2 s; backfill a-d 14 s; settle 79 s; drain `mini_depth.worker run-pending --limit 500`: one pass, 155 outcomes (< 500), 24 s; settle again 71 s; collect 209 s (134 requests, all 200); check against `expected-today.json`: COH-17 0 findings, **compared 218, skipped 13**; COH-18 0 findings, **compared 21, skipped 0**; self-check 2 pass, 0 fail, 8 resolved (COH-7a); PERIOD info 4, 0 unexplained. 0 new. (Same tallies as undrained: the checked set is fixed by the windows; the difference is in the verdicts compared. EV backfill considered 19 days, not 18, because the clock day advanced.) W6 and `fresh` were not re-run (not in the ruling).

| Day (board) | Optimize row state | MG-2 outcome, reason | Headline | `critical_served` | Thread line |
|---|---|---|---|---|---|
| S `day_kobo_trial-before_2026-10-31` | NEEDS_ATTENTION | NEEDS_ATTENTION, PRIMARY_FINDING_OPEN | No fuel cost estimated: the generator was on but delivered no measured power | PARTIAL | "Before the change on 1 Nov" (BEFORE_CHANGE, ACT-000001): as CO-1 |
| S+1 `day_kobo_trial-after_2026-11-01` | UNKNOWN | UNKNOWN, OBJECTIVE_NOT_JUDGED | No fuel cost estimated for this day | PARTIAL | "Fix verified, monitoring (ACT-001), 7 more fully checked days to close": as CO-2 |
| `day_kobo_overuse_2026-10-24` | NEEDS_ATTENTION | NEEDS_ATTENTION, PRIMARY_FINDING_OPEN | No fuel cost estimated: the generator was on but delivered no measured power | PARTIAL | "Before the change on 1 Nov" |

Undrained (labelled): all three read UNKNOWN / PRODUCER_NOT_SETTLED, headline "No fuel cost estimated for this day", `critical_served` PENDING on 7 of 8 and PARTIAL on 1. No stop condition fired: PRODUCER_NOT_SETTLED is gone on all three days, S equals CO-1, no new COH finding, Q4b counts equal the table (below).

Q4b counts on the drained data (week / S / month): fixes confirmed (`verified_resolution_count`, `count.verified_results`) 0 / 0 / 1; `priority_site_count` 3 / 2 / 2; `count.open_threads` 4 / 3 / 3; `count.opportunities` 1 / 1 / 1; `count.sites_disrupted` 2 / 1 / 2.

**L3m**: `ensure --close no` rebuilt the states template once (1300 s, against an 11-minute estimate); derive 76 s; collect 436 s (108 requests); check with `--variant states --threads var/mechanism/expected-threads.json`: 0 findings, 0 unexpected, COH-17 compared 111 skipped 11, COH-18 compared 75 skipped 0, PERIOD info 0 (Kobo only). The first check call used a wrong threads path and exited 1 on a missing file; the result above is the corrected rerun on the same bundle.

**L2m** `test_ch6b_estate_postgres.py`: both tests passed (the MG-1 test after KD-3b's assertions were removed; the first run failed on them). **L0** `test_chain_coherence.py`: 133 pass. **Vitest** `estatePortfolio.test.tsx`: 60 pass. `tsc --noEmit`: no output.

**Scoped backend, first run** (`test_w303_portfolio_*` listed files, `test_ch3_rows`, `test_w301_estate_coverage`, `test_cov_partial_portfolio`, `test_ch5a2_chain_api_postgres`, `test_ch6b_estate_chain`, `test_ch6b2_portfolio_cards`, `test_ch5a2b_claims`): 4 failed, 211 passed. All four were stale tests (causes already in main, so they fail on main today), fixed in CH6b3-R2 step 1 with only the lines the ruling names:
- `test_w303_portfolio_comparison_postgres.py::test_selected_action_window_workflow_and_withdrawal`: spy now `def spy(a_sites, a_rows, k, selected_pairs, *rest)` and passes `*rest` on (`progress` gained `f_rows`, `3cea423fd`). It now reaches its assertions, including the verified counts at `:157`, `:193-195`, `:211`: **no number failed, none changed**.
- `::test_operating_cost_first_match_wins_across_partitions`: `link_ref` added to the card dict (`1c3e3a075`). Passes.
- `::test_ev_window_money_has_no_finding_attribution`: `link_ref` added to the footer key set. Passes.
- `test_ch5a2_chain_api_postgres.py::test_estate_chain_has_one_read_per_key_and_count_claims`: `count.sites_disrupted` added (`6b4e682f2`); comment says "the four". Passes.
- Result of the first two files named by the ruling (`test_w303_portfolio_comparison_postgres.py`, `test_ch5a2_chain_api_postgres.py`) plus `test_ch6b_estate_postgres.py`: **12 passed, 0 failed** (663 s). The remaining scoped files: see "Scoped re-run" at the end.

**Proofs** (committed first, reverted with `git checkout`): `action_segment_for` replaced by the default segment fails the L1 test; `in_hand` removed from `priority_site_count` fails the Q4b test; both pass after revert. COH-17 and COH-18 are proved by the planted tests.

No full suite, per the brief. Layout evidence: not run (one word changes; no layout claim made).

**Guards:** see "Guard results" at the end.

## Portfolio old → new (polish clone, this head)

Old cards: the CH-6b1 browser rules as listed in the CH-6b2 packet, from `category_counts`. Old legacy: `thread_progress` at the same requests, store off.

| Value | Window | Old | New | Rule |
|---|---|---|---|---|
| Fixes confirmed | week | 1 | 0 | Q4b, claim |
| Fixes confirmed | S | 1 | 0 | Q4b, claim |
| Fixes confirmed | month | 1 | 1 | unchanged |
| Priority sites | week | 0 | 3 | Q4b |
| Priority sites | S | 0 | 2 | Q4b |
| Priority sites | month | 0 | 2 | Q4b |
| Protect card | week | 2 sites disrupted | 2 found on the days checked | CH6b2-R |
| Protect card | month | 2 sites disrupted | 2 found on the days checked | CH6b2-R |
| Protect card | S | not assessed (`category_counts` null) | 1 found on the days checked | CH6b2-R |
| Assure card | week, S | Not known yet | None confirmed on the days checked | CH6b2-R |
| Assure card | month | Not known yet | 1 confirmed on the days checked | CH6b2-R |
| Grow card | week / S / month | short value | At least 84.16 USD / At least 0.00 USD / At least 168.32 USD estimated | R10 replaced |

Other claims on this head: `count.open_threads` 4 / 3 / 3 and `count.opportunities` 1 / 1 / 1 (week / S / month).

**Cause, from `finding_thread_event` on the clone** (CH-5a `:691`; the events explain every change):
With no `known_at`, every event is visible. A thread's state differs by window because it is read on the window's last day against the event's `effective_day` (`threads_of`, `lc.state_on`), not because of a "known" time (CH6b3-R2 step 4).
- Kobo thread `6c6258e4`: RESOLVED_MONITORING effective 1 Nov. Week and S end before 1 Nov, so on their last day it is ACTION_IN_HAND: confirmed 1 → 0, and Kobo counts as a priority Site. Month runs to 3 Nov, so it reads verified: 1 stays 1.
- The old priority count of 0: `thread_progress` read rows whose Cold and EV thread states were null, while Kobo read RESOLVED_MONITORING. The claims read the lifecycle on the window's last day (CH6b2-R2).
- Cold `3e6e4c87` and `8b05d5cc`: OPEN, then in hand from their `effective_day`. EV `8afb054a`: OPEN on 27 Oct (in week, not in S), ACTION_IN_HAND effective 2 Nov (in hand in month). This gives 3 / 2 / 2 Sites (week = Kobo, Cold, EV; S = Kobo, Cold; month = Cold, EV).
- CH-5a's "1 against 0, 0 against 1" predates the CH6b2-R2 cutoff; these are the values at this head.

## PERIOD information table (polish; board against summary; the frame differs by design)

For the walkthrough: these Site boards read an event, not the whole window. Text is equal in all four; days differ. 0 unexplained. BL-33 owns a strict comparison.

| Site | Window | Row, part | Text | Board days | Summary days |
|---|---|---|---|---|---|
| Cold | week | Protect, kpi | above 4°C in this window | 0/1 (low 1) | 0/7 (low 2, no data 5) |
| Cold | month | Protect, kpi | above 4°C in this window | 0/1 (low 1) | 0/31 (low 3, no data 28) |
| EV | month | Grow, earnings | Not known yet | 0/1 (low 1) | 0/19 (low 2, no data 17) |
| EV | month | Protect, kpi | 1 interrupted | 0/1 (low 1) | 0/19 (low 2, no data 17) |

## Mock departures

- MD-CH6-4 (R705): Protect CHECKED_DAYS forms.
- MD-CH6-5 (R707, added here): the mock's note says Sites are not added together; OWN-1104 adds them, honestly worded.
- MD-CH6-6 (R706): per-Site targets on the Grow Target part.

This closes the note at `review-CH-6b2.md:78`. That file is only in the plan2 checkout.

## §B6 CH-9 order

**CH-9 merged first** (CH-9b3 `7a89f58f0` on main before CH-6b completed), so the Kobo Potential part reads CH-9's daylight study. L3 value: key `potential.daytime_solar_headroom`, "Limited evidence: readings come from mixed sources, so the size is not worked out yet"; the week item carries `headroom_unit` "kW over daylight hours" (`chain_estate.week`), read through `mini_depth/read.py` `daylight_hours`. The D12/D13 L2m assertion is BL-34.

## Known deviations

- **KD-1 (confirmed, CH6b1-R Q6):** Cold and EV are checked at L0 only in L2m; real-data agreement is the L3 clone and COH-17.
- **KD-2:** the `states` L3m set has no D6-D9, so its week reads 4 of 7 with 3 no-data days. R4 accepts a listed gap or a NO_DATA day (CH6b3-R Q4a). A day built with no readings cannot be told from an unbuilt one; MD-0 tests own that case.
- **KD-3b, CLOSED by CH6b3-R2 (acceptance row: Restated).** Not a product defect: `mechanism_db()` has no Performance comparison report, so the Performance gate is closed and every Kobo row reads UNKNOWN; D13's chain omitting the generator thread is by design (`threads_of` lists a thread only with an occurrence or event in the window). The L2m bullet is restated: the generator thread is RESOLVED_MONITORING since D12 on D13 (`test_md0_mechanism_postgres.py:268`) and the estate row equals the board row (`test_ch6b_estate_postgres.py:210`); the board verdict is proved on the drained clone (below) and by CO-1 and CO-2 in every combined `prepare`. Original observation, kept as evidence: the bullet says the Optimize row on D13 reads the ACT-K1 verdict (RESOLVED_MONITORING since D12). Observed on `mechanism_db()`, states:
  - D13 board Optimize row: state UNKNOWN, `thread_lines` [], `issues` [], read state PARTIAL. On the D11 board it is also UNKNOWN, with a "Generator use" contributor reading "Not available yet · this record could not be loaded".
  - Every one of the 11 named Kobo day boards reads Optimize UNKNOWN and Assure "No verified result yet".
  - D13 `/sites/KOBO-001/chain` lists only the headroom thread (OPEN). D12's lists the generator thread RESOLVED_MONITORING. D11's lists it ACTION_IN_HAND. `test_md0_mechanism_postgres.py:268` asserts the thread state on D13.
  - Counts: week `count.verified_results` 1, S 0, month 0 (month 1 open: the D14 recurrence).
  - Likely reading, not proved: counted threads need a Finding occurrence meeting the window (`chain/claims.py:56`), and D13 has none. I did not find why the Generator-use record fails to load on this data.
  - The assertions were removed rather than tuned; the test asserts only that the estate row equals the D13 board row, and says so in a comment.
  - Question: is this a defect in the mechanism read, or should the bullet read the D12 thread and the week count? The Architect also classifies it demo-critical or backlog.
- **Why? price line** is not compared (CH6b3-R Q2; BL-34).
- `clean_full` and `coh18_day_grades` were generated by a one-off script outside the repo, then committed as plain JSON.

## Residual risk

- Collect time grows: 190 s on polish, 436 s on L3m. Only the check tool pays this.
- The template rebuild took 1300 s, nearly twice the estimate.
- `assetops_mechanism_test` and the new states template are left in place, as after any L3m. The polish clone is dropped.

## User review

No owner walkthrough item in this unit. The reviewer focus is the drained-clone table (S equals CO-1, S+1 equals CO-2) and the four test fixes (stale tests, no number changed).

BL-36 (not demo-critical, recorded): `count.verified_results` counts only threads with a Finding occurrence in the window, so a Portfolio opened on one later day (for example 1 Nov) can read "None confirmed" while Kobo's board that day reads "Fix verified, monitoring". The story links open the week and the month, which agree. DS-1 must keep the Portfolio on those two windows.

Lane 2 note (DD-1b2 F-THREADS): must also report each row's state on every shown Kobo story day and fail on PRODUCER_NOT_SETTLED or a PARTIAL board; CO-1 covers only day S.

## Guard results

Run one at a time at `350b5a3a9`, `check-all` not run: A architecture pass; W agent workflow pass; N navigation pass; V mock-deviation labels pass; M missing-claim scan pass (42 tagged, 10 baselined), fixtures pass; frontend ratchet pass; COH fixtures 133 pass.


## Scoped re-run (CH6b3-R2)

Two runs, both via `tools\run-host-tests.ps1`, all 0 failed, 0 skipped: (1) `test_w303_portfolio_comparison_postgres.py`, `test_ch5a2_chain_api_postgres.py`, `test_ch6b_estate_postgres.py`: 12 passed (663 s). (2) `test_w303_portfolio_api`, `_fixture_postgres`, `_reduction`, `_scope_snapshot_postgres`, `_workflow_labels`, `test_ch3_rows`, `test_w301_estate_coverage`, `test_cov_partial_portfolio`, `test_ch6b_estate_chain`, `test_ch6b2_portfolio_cards`, `test_ch5a2b_claims`: 215 passed (718 s). The ruling expected 215 passed for the packet's scoped list; I could not reproduce that grouping exactly (the original list was written as "listed files"), so the figure is the two runs' sum, 227 passed. No full suite, no `check-all`, per the brief.


## CH6b3-R3 (supersedes the Q4b table above, CH6b3-R2 step 4 and the BL-36 premise)

Steps 1-5 and 7 done; step 6 partly (see "Not run"). Code commits: `c60bd8c07` (steps 1-3), the step 4 commit, lows/handoff.

### Step evidence
1. **H1, one claim.** `chain/claims.py` `LATEST_KNOWN = date.max`; `counted_threads` reads each thread's latest event visible at `k`. Text "{n} confirmed, from the days checked" (MD-CH6-8, R708, `v70/index.html:296`). L0 (a)-(d) in `test_ch6b2_portfolio_cards.py`; case (5) restricted with a comment. `test_ch5a2_contract.py` golden `estate_week_2026-10-25`: Kobo `threads` open 1 -> 0, in_hand 0 -> 1; cause: T1's ACTION_IN_HAND is effective 1 Nov and known by k. `count.open_threads` is still 1 (open + in hand).
2. **M1.** Protect note None; Assure note = recovered value + evidence gap (no coverage clause); `checked_days_clause`, `note.checked_one/many` removed; coverage strip reads "N of M days assessed" / "not assessed:" (R622 updated). Case asserting neither note holds "days checked". Literal strings in `test_cov_partial*.py`, `w301-estate-golden.json`, frontend tests/fixture updated. (`note.withheld_one/many` left in the vocabulary, now unused.)
3. **M2.** `_estate_why` uses the card's `days_line` (Optimize: Protect's) and `window_open` = expected - complete from `estate_counts`; `Trace.open_days`; `estate_text(days_used, window_open)`. L0 `test_estate_text_takes_the_cards_days_and_the_windows_open_days`; route test on the in-memory app, month window, three categories. **Not run:** the Postgres Why file route test (needs the mechanism template, see Not run) and the route time before/after (not measured).
4. **COH-17 rows**, `tools/checks/chain_coherence.py`; `clean_full` edited by hand (portfolio.S one Verified row, `days_line`/`days_used` on the week cards and four Why bodies), `coh18_day_grades` portfolio.S likewise. `test_chain_coherence.py`: 138 pass.

| Rule | Fails on real (old) bundle `var/ch6b3r2_bundle` | Planted break |
|---|---|---|
| L2 | week, S (summary 1, claim 0) | yes |
| L3 | week, S (1 Verified thread in the table, claim 0) | yes |
| W3 | all four categories, week/S/month | yes |
| N1 | Protect and Assure notes, week and month | yes |
| C2 absent key | n/a (both sides absent) | yes; with the new clause disabled the test fails, restored by `git checkout` |

5. **Frontend:** lockfiles identical; `npx tsc --noEmit` exit 0; `vitest related` pulled in a `.py` file and aborted (Vite import analysis), so the five files in `src/estate/__tests__` were listed: 110 passed. This includes `namesOnePrioritySiteInTheSingular`. Junction removed with `rmdir`; plan2 `node_modules` intact.

### Drained polish clone (new, dropped), figures against expected
Commands as R2 step 2; drain one pass; collect 134 requests all 200; check with `expected-today.json`: COH-17 0 findings, compared 242, skipped 13; COH-18 0 findings, 21/0; 0 new (COH-2: the 2 known entries); self-check 2 pass, 8 resolved. No L3 finding, so no `expected-mechanism.json` entry was needed on this clone.

| Value (week / S / month) | Expected | Measured |
|---|---|---|
| Fixes confirmed (card, legacy, claim) | 1/1/1 | 1/1/1 |
| Priority Sites | 2/1/2 | 2/1/2 |
| `count.open_threads` | 3/2/3 | 3/2/3 |
| `count.sites_disrupted` | 2/1/2 | 2/1/2 |

### Old -> new (replaces the Q4b table)
| Value | Window | R2 packet | Now | Cause |
|---|---|---|---|---|
| Fixes confirmed | week / S | 0 / 0 | 1 / 1 | latest-known: Kobo's 1 Nov verification counts for the problem found in the window |
| Fixes confirmed | month | 1 | 1 | unchanged |
| Priority Sites | week / S / month | 3 / 2 / 2 | 2 / 1 / 2 | Kobo is verified, no longer open |
| Open | week / S / month | 4 / 3 / 3 | 3 / 2 / 3 | same |
| Sites disrupted | week / S / month | 2 / 1 / 2 | 2 / 1 / 2 | unchanged |
| Assure card | all | "None confirmed on the days checked" (week, S) | "1 confirmed, from the days checked" | MD-CH6-8 |
| Protect note | week, month | "3 of 7 days checked at Kobo mini-grid" | none | M1 |
| Assure note | week | "... evidence gap at 1 site - 3 of 7 days checked at Kobo mini-grid" | "No money credited - modelled, not saved - evidence gap at 1 site" | M1 |

**Day-bound on purpose:** board rows and Site dots. On S, Kobo Optimize reads "Needs attention" with "Before the change on 1 Nov" (CO-1): a dated statement. The Portfolio claim answers "status as known now" for the problems found in the window. BL-36 premise withdrawn.

### Lows and notes
- Test renamed `test_mg1_judged_on_checked_days_and_estate_optimize_row_equals_the_d13_board`, docstring fixed; "as CO-2" corrected to **CO-1b** (build sheet and this packet's reading: S+1 is CO-1b).
- For the walkthrough: Portfolio Cold and EV rows read "No action agreed yet" on the week while ST-4/ST-5 boards show those Actions in hand (row cutoff, known COH-2 entries). DD-1b2 F-THREADS reports it.

### Not run (stated plainly)
- **Stale mechanism template:** the scoped run (20 files, `var/ch6b3r3_scoped.log`) gave 337 passed, 2 errors, 0 failed. Both errors are in `test_ch6b_estate_postgres.py` and are setup errors: `MechanismRefused TEMPLATE_STALE: template inputs 8d37cd0333dc != this checkout abc647639e60`. The code change in steps 1-3 changed the template inputs. A rebuild (`mechanism_dataset.py build --variant states`, about 1300 s) is needed; the brief says not to rebuild and to stop and ask, so I did not. Consequently **not run:** those two L2m tests, the L3m collect/check (L3m / L3m D14 expectation), and the Postgres Why route test.
- No full backend suite, no `check-all`, no demo prepare, no layout evidence.

### How a re-reviewer checks H1, M1, M2
- H1: open `var/ch6b3r3_bundle` (if kept) or rerun; `portfolio.week.p1` Verified row thread `6c6258` and `chain_estate.week` `count.verified_results` 1; run the new COH-17 on `var/ch6b3r2_bundle` to see L2/L3 fail, on the new bundle to see them pass.
- M1: `portfolio.*.p1` `summary.card_notes` hold no "days checked"; N1.
- M2: `why_estate.{w}.PROTECT_ASSET` `text.days_used` equals `chain_estate.{w}` `cards.PROTECT_ASSET.days_line` (W3).

### Guard results (CH6b3-R3, one at a time, `check-all` not run)
A architecture pass; W agent workflow pass; N navigation pass; V ledger valid (110 screens); M `test_mock_deviation_labels.mjs` 14 pass; frontend ratchet pass; COH fixtures 138 pass. Backend focused: `test_ch6b2_portfolio_cards`, `test_ch5a2b_claims`, `test_ch5b_why`, `test_ch5a2_contract`, `test_cov_partial*` etc. pass inside the 337 of the scoped run.

### CH6b3-R3 final runs (rebuild approved by the coordinator; results as run, nothing tuned)
- **Template:** `mechanism_dataset.py build --variant states` (budget default stopped at 540 s twice, resumed with `--resume`, third with `--budget 3000`; total about 1300 s). New template `assetops_mechanism_tpl_abc64763_test`, matching this checkout. One rebuild.
- **L2m** `test_ch6b_estate_postgres.py` (with `ASSETOPS_TEST_DATABASE_URL`; the first run without it skipped both, discarded): **2 passed**, 515 s. Estate rows agree with the claim.
- **Postgres Why file** `test_ch5b_why_postgres.py`: **1 passed**, 420 s. That file covers the Site Why route only; it has no estate month assertion. The estate month evidence is the L3m bundle below: `why_estate.{week,S,month}.{PROTECT,OPTIMIZE,ASSURE}` `days_used` equals the card `days_line` on all 9, no "32" in `would_change` (month reads "Checking 21 more days").
- **L3m** (`derive --variant states` 72 s, collect 109 requests, `check --variant states`; bundle `var/ch6b3r3_l3m_bundle`, report `var/ch6b3r3_l3m_report.json`): **FAILS, 4 new COH-17 findings, no expected entry added**:
  - L3 week and month: "1 distinct Verified threads in the table, claim 0" (possibly the D14 recurrence; not confirmed, not entered).
  - **N1 week and month: ASSURE_PERFORMANCE note 'No money credited - modelled, not saved - no evidence gaps on the days checked' holds "days checked"**. This is not D14. On the mechanism DB the Assure note has a no-evidence-gaps branch that still says "days checked" (M1 closed only the other branch). Needs a code fix by the coordinator's decision.
  - All other rules 0; COH-17 compared 135, skipped 11; COH-18 compared 15.
- `expected-mechanism.json` untouched. Stopped here per the brief.

## CH6b3-R4 run (ruling steps A-C; fresh Sonnet builder, 2026-11-07)
- **Template:** unchanged, fingerprint `abc64763`; `mechanism_dataset.py status` printed `usable: true` for `states` before and after the edits. No edit under `backend/assetops_backend/` outside `chain/` (`vocabulary.py` only). No rebuild.
- **N1 text:** `note.gap.zero_checked` "no evidence gaps on the days checked" -> "no evidence gaps on the days assessed". Browser twin `NONE_ON_CHECKED_DAYS` "None found on the days checked" -> "None found on the days assessed" (pulse only; the two pulse assertions and one mock detail string in `estatePortfolio.test.tsx` follow). R670 in `mock-departure-register.md` updated. New L0 `test_evidence_gap_text_never_says_days_checked` (gaps None/0/1/2/4/6 x checked False/True, 12 cases); `:237` row updated.
- **Entries:** `expected-mechanism.json` has the two ruled COH-17 L3 entries (week, month; `variants: ["states"]`; cause D14 recurrence, owner BL-07). **Deviation from the exact JSON:** each also carries `"register": "CH6b3-R4: D14 recurrence"`, and `test_expected_mechanism_loads_and_only_names_declared_gaps` (`tools/checks/test_chain_coherence.py`) accepts the prefix `CH6b3-R4:` beside `MD-0:` and `MD0b-R:`. Without both, that L0 test fails with KeyError `register`; the file's own rule already allows "MD0b-R (or later)" items.
- **L0:** `test_chain_coherence.py` + `test_ch6b2_portfolio_cards.py` + `test_w303_portfolio_api.py`: 199 passed, 1 skipped.
- **Frontend:** lockfiles identical; `tsc --noEmit` exit 0; `vitest related --run src/estate/EstatePortfolio.tsx` fails to start on this tree (it pulls a `.py` file into import analysis, no tests run), so `vitest run src/estate` instead: 5 files, 110 passed. Junction removed (junction only).
- **L3m:** `derive --variant states` 58 s; collect 108 requests, all 200 (bundle `var/ch6b3r4_bundle`, report `var/ch6b3r4_l3m_report.json`); `check --variant states --expect expected-mechanism.json --threads var/mechanism/expected-threads.json`: COH-17 2 findings, 2 expected, **0 new** (N1 = 0, W3 = 0); COH-18 0; no RESOLVED entry; COH-17 compared 135 skipped 11; COH-18 compared 75 skipped 0; self-check 2 pass.
- **Guards:** V ledger valid (110 screens); M 14 pass.
- **Not re-run:** L2m and the polish clone (one text value, one browser constant and an expectation file moved; no read path or number changed; polish never reaches the branch).
