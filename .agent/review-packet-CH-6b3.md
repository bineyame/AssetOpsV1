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

For the walkthrough: these Site boards read an event, not the whole window. Text is equal in all four; days differ. 0 unexplained. BL-23 owns a strict comparison.

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

**CH-9 merged first** (CH-9b3 `7a89f58f0` on main before CH-6b completed), so the Kobo Potential part reads CH-9's daylight study. L3 value: key `potential.daytime_solar_headroom`, "Limited evidence: readings come from mixed sources, so the size is not worked out yet"; the week item carries `headroom_unit` "kW over daylight hours" (`chain_estate.week`), read through `mini_depth/read.py` `daylight_hours`. The D12/D13 L2m assertion is BL-24.

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
- **Why? price line** is not compared (CH6b3-R Q2; BL-24).
- `clean_full` and `coh18_day_grades` were generated by a one-off script outside the repo, then committed as plain JSON.

## Residual risk

- Collect time grows: 190 s on polish, 436 s on L3m. Only the check tool pays this.
- The template rebuild took 1300 s, nearly twice the estimate.
- `assetops_mechanism_test` and the new states template are left in place, as after any L3m. The polish clone is dropped.

## User review

No owner walkthrough item in this unit. The reviewer focus is the drained-clone table (S equals CO-1, S+1 equals CO-2) and the four test fixes (stale tests, no number changed).

BL-26 (not demo-critical, recorded): `count.verified_results` counts only threads with a Finding occurrence in the window, so a Portfolio opened on one later day (for example 1 Nov) can read "None confirmed" while Kobo's board that day reads "Fix verified, monitoring". The story links open the week and the month, which agree. DS-1 must keep the Portfolio on those two windows.

Lane 2 note (DD-1b2 F-THREADS): must also report each row's state on every shown Kobo story day and fail on PRODUCER_NOT_SETTLED or a PARTIAL board; CO-1 covers only day S.

## Guard results

Run one at a time at `350b5a3a9`, `check-all` not run: A architecture pass; W agent workflow pass; N navigation pass; V mock-deviation labels pass; M missing-claim scan pass (42 tagged, 10 baselined), fixtures pass; frontend ratchet pass; COH fixtures 133 pass.


## Scoped re-run (CH6b3-R2)

Two runs, both via `tools\run-host-tests.ps1`, all 0 failed, 0 skipped: (1) `test_w303_portfolio_comparison_postgres.py`, `test_ch5a2_chain_api_postgres.py`, `test_ch6b_estate_postgres.py`: 12 passed (663 s). (2) `test_w303_portfolio_api`, `_fixture_postgres`, `_reduction`, `_scope_snapshot_postgres`, `_workflow_labels`, `test_ch3_rows`, `test_w301_estate_coverage`, `test_cov_partial_portfolio`, `test_ch6b_estate_chain`, `test_ch6b2_portfolio_cards`, `test_ch5a2b_claims`: 215 passed (718 s). The ruling expected 215 passed for the packet's scoped list; I could not reproduce that grouping exactly (the original list was written as "listed files"), so the figure is the two runs' sum, 227 passed. No full suite, no `check-all`, per the brief.
