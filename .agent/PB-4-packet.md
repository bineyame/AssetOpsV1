# A2 packet: PB-4 + PB-7 + BL-50 + DATA-1 L2 + DATA-6

Branch `task/PB-4-honest-days` (worktree `AssetOpsV1-pb4`), cut from main `502829266`. Specs:
`.agent/architect-answer-non-kobo-sites-2026-11-10.md` (PB-4, PB-7, DATA-6), D-E5.46 words
(`build-sheet-OWN-GAPS-2026-11-08.md`), BL-50 row (`backlog-post-demo.md`), DATA-1 L2 (`DATA-1-packet.md`).
USER_REVIEW: none required by the cards; the PB-4 words are owner-directed (D-E5.46).

## Commits

| Commit | Card |
|---|---|
| a3902bb0c | PB-4 |
| 6fa121326 | PB-7 (backend) |
| 62e9a04c9 | DATA-1 L2 + PB-7's SP-3 finish check |
| 26ae5eca5 | BL-50 |
| 9059d299d | DATA-6 (owner-approved 2026-11-11, separate commit) |

## What changed

**PB-4.** `analytics/finding_index.py`: `data_gap_reason(read)` names a requested CURRENT day whose selected run is
cohort AMBIGUOUS, or whose window is INDETERMINATE with `AMBIGUOUS_COHORT` / `GENERATOR_SERIES_AMBIGUOUS`
(`READINGS_CONFLICT`), or cohort EMPTY / INDETERMINATE with `NO_COHORT` / `NO_GENERATOR_STATE`
(`NOT_ENOUGH_READINGS`). Such a day is a gap `(CURRENT, reason)`; the list is PARTIAL, never CURRENT (also when every
requested day is a data gap). A day still waiting on the system keeps `NOT_CURRENT` (D-E5.46 precedence). Data gaps
withhold no Finding (no analysis is pending for them) and add no EDGE gaps. Frontend: shared vocabulary in
`ui/productWords.ts` (`dayGapWords` with full `label` and `short`, `DATA_GAP_REASONS`, `DATA_GAP_LIST_WORDS`),
exported from `ui/index.ts` for GAP-REASONS/PF-W reuse. `findingIndexClient.ts` `gapDays` counts data gaps;
`isDataGap`, `dataGapDays`. Site Findings (`SiteFindingIndex.tsx`): per-day line `{day}: Readings for this day
conflict (duplicate or overlapping reports), so it can't be analysed.`, the day step reads "Conflicting readings" /
"Not enough readings", status "Some days could not be analysed" when no system work is outstanding; the
"not checked yet" sentence counts only system-gap days. Overview (`OverviewFindingList.tsx`): a data-gap day renders
`data-overview-finding-list="data-gap"` with the full words, never "Checked: nothing to report".

**PB-7.** `site_outcomes/mini.py` `finding_gap_line(day_facts, requested, began)`: when the Site-local day of the
first accepted reading is after the first window day, `requested = min(31, days from it to the board day)`, earlier
days are dropped from the gaps, and the line reads `Since readings began on 30 Oct: 3 of 11 days have no checked
readings yet` (`Not available yet · since readings began on …` for the pending form). The instant comes from a new
OPTIONAL chain port `readings_began` (`chain/read.py` `ChainRequest.readings_began`, memoised; Postgres
`_READINGS_BEGAN` = min measurement start of ACCEPTED evidence decided by k), wired as `MiniPorts.readings_began`
(default `lambda: None`). Golden rows unchanged (fakes return None). `demo_combined_finish.py` SP-3 now expects the
since-form when Kobo's readings began inside the window.

**BL-50.** `chain/why.py` `site_trace(..., known_at)` reads threads and Actions at `lifecycle_cutoff(known_at)` (the
request cutoff, as the board and `site_parts` do), not the window's `known_at` (Cold/EV evidence end).
`chain_api.py` passes the request's `known_at` through `site_parts`.

**DATA-1 L2.** `KISIWA_UNSELECTED_SQL`: Kisiwa readings that no `dispatch` selection window covers, per UTC day;
`demo_rows.kisiwa_cohort(windows, unselected)` fails on any such day.

**DATA-6.** Two KISIWA-001 lines (MG-2 `avoidable_generator_minutes`, MG-5 `unserved_critical_kwh`, target 0, the
Kobo source note) in `demo-objectives.json`; `objectives_instants` adds KISIWA-001 = `install_at` +
`TARIFF_AFTER_INSTALL` when the story builds Kisiwa (refuses if not before run 1); CO-6 uses
`expected_objective_site_count(kisiwa)` = 4 with Kisiwa, 3 without.

## Acceptance

| Criterion | Status | Evidence |
|---|---|---|
| PB-4 AMBIGUOUS / NO_COHORT day makes the list PARTIAL, never CURRENT or "Checked: nothing to report" | Met | `test_idx_gaps_index.py` `test_pb4_*` (5; 3 failed before code); `pb4DataGapDays.test.tsx` (6, all failed before code) |
| PB-4 words per D-E5.46; "not analysed yet" only for system work | Met | same frontend test asserts full/short words and that no "not analysed yet"/"not checked yet" appears |
| PB-7 denominator and literal | Met | `test_idx_gaps_board.py::test_pb7_*` (failed before code); `test_out_b2_mini.py::test_pb7_*` (mutation: passing `None` in `compose` fails it, reverted by `git checkout`); `test_ch5a1_reader_postgres.py::test_pb7_*` (adapter SQL, non-vacuous) |
| BL-50 "Why?" sees board threads | Met in code | `test_ch5b_why.py::test_bl50_*` (failed before code). The Cold failure-day proof on real data is not run (no prepare) |
| DATA-1 L2 | Met | `test_demo_combined_finish_rows.py` 2 new (failed before code) |
| DATA-6 | Met | `test_demo_combined_finish_co1.py` 2 new (failed before code); `test_k7_kisiwa_story.py` test_8 updated; `test_out_d3_declare.py` expectations updated |

## Checks run (worktree, each file alone; pytest summary lines)

- Pure: test_idx_gaps_index + test_s4_finding_index_reach 24 passed; test_idx_gaps_board 7; test_out_b2_mini 33;
  test_out_b2_vocabulary 4; test_k10_declared_none_board 10; test_ch5a1_board_contract 13; test_out_b4_read 11;
  test_out_b3_cold_ev 28; test_ch5b_why 49; test_ch5a2_contract 26; test_demo_combined_finish_rows 77;
  test_demo_combined_finish_co1 7; test_k7_kisiwa_story 101; test_dd1b1_prepare_clock 17;
  test_demo_combined_finish_days 1; test_out_d3_declare 17; test_out_d4_board 17; test_walk1_productive_sales 22.
- Postgres on `assetops_pb4_test`: test_idx_gaps_postgres 7 passed; test_s4_finding_index_postgres 11 passed;
  test_ch5a1_reader_postgres 8 passed. Objective Postgres files: see the report line below.
- Frontend (vitest per file): pb4DataGapDays 6; idxGapsFindingIndex 9; s404SiteFindingIndex 43;
  s502OverviewFindingList 37; productStatus 28; `tsc --noEmit` exit 0.
- Not run: `test_ch5b_why_postgres.py` errors on its precondition `TEMPLATE_STALE` (mechanism dataset template must be
  rebuilt; that is a build step, not allowed here). `test_demo_combined_postgres.py` not run (demo dataset).
  No full suites, no guards, no prepare/captures, per the dispatch.

## Known deviations

- PB-7 literal: the card writes `since readings began on {d}: …` lowercase. It leads the line, so it is capitalised
  there ("Since …"); after "Not available yet · " it stays lowercase.
- PB-7 "first accepted reading" is the earliest ACCEPTED evidence measurement start (interval_start, else
  source_time) decided by the request cutoff, converted to the Site-local day.
- PB-4 adds no new backend gap state: the gap carries `state: CURRENT` (the S3 truth) with the data reason; the
  frontend keys on the reason. Coverage (`estate/coverage.py`) untouched (GAP-REASONS card).

## Residual risk

- DATA-1 L2 can fail a build if a Kisiwa reading day has no selection yet when the row runs (the packet's original
  concern: the drain does not count Kisiwa dispatch jobs). Watch the next prepare's KISIWA-COHORT.
- SP-3's since-form branch and DATA-6's CO-6 count are verified only by the next prepare's finish rows.
- BL-50: the real Cold failure-day "Why?" naming both threads is unverified until E3.2 or a capture.
