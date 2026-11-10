# FX-KOBO-GAPS review packet

Task: card FX-KOBO-GAPS, D-E5.13 as amended by D-E5.19 (`.agent/build-sheet-OWN-GAPS-2026-11-08.md`, "Kobo gap-pattern
ruling" D-E5.11-15 and "Kobo days amendment" D-E5.16-20). Owner text: `.agent/owner-kobo-gap-pattern-2026-11-10.md`.
Branch `task/FX-KOBO-GAPS`, worktree `AssetOpsV1-fxkobo`. Not pushed.

## Commits

| Commit | What |
|---|---|
| 4b937a1d0 | Calendar v4 (`DEFAULT_FILE`; v3 kept as `V3_FILE` and the `--days` rollback), WK-GAP row and helpers, WK-2a/WK-2b restated, WK-6 comment, singular `LIMIT_UNKNOWN_ONE`, manifest `"days"` label |
| ed120cd76 | K7 three-Site story pins: v3 pins kept and asserted on the v3 list; new v4 pins |
| 4f2907c9f | Merge main (brings D-E5.16-20, bd0ffab3b) |
| 0f297432e | D-E5.19: six month-fill entries, v3-equality clause, `test_v4_month_fill`, WK-GAP month clause, WK-FILL report row, K7 v4 pins re-taken |

The previous builder's uncommitted edit to `test_demo_story_days.py` (week constants `V4_MISSED`/`V4_PARTIAL`/`V4_FULL`,
`V4_CHANGED_DAYS`/`V3_REPLACED_DAYS`) was kept, except its relaxation of `kinds` to "v4 is a superset of v3": the
ruling says the kinds stay byte-equal and they do, so `kinds` is compared strictly again.

## Files materially changed (main...HEAD)

`backend/conversions/demo-story-days-v4.json` (new), `tools/demo_story_days.py`, `tools/demo_combined.py`,
`tools/demo_combined_kobo.py`, `tools/demo_combined_finish.py`, `tools/demo_combined_rows.py`,
`backend/assetops_backend/chain/vocabulary.py`, tests: `test_demo_story_days.py`, `test_demo_combined_finish_rows.py`,
`test_ch4_opportunities.py`, `test_k7_kisiwa_story.py`, `k7_story_pins.py`.

## Changed assertions

- `test_default_file_validates_on_relative_dates`: v4 row (16, 6) -> (22, 6) full/story-only Kobo days; v3 row (13, 8) unchanged.
- Tests needing a `late` entry or v3's table load `sd.V3_FILE` (commit 1; not deleted).
- `test_v4_story_week_one_missed_one_partial` (S = 11-07, 11-08, 11-09): week S-6..S = one no-run day S-4 (`missing`),
  one story-only day S (`trial-before`), five tiling full days, no `late`. v3-equality clause now: v4 minus its 4 week
  entries and its 6 S-27..S-22 entries equals v3 minus its 2 week entries; `kinds`, trial and all other keys byte-equal;
  label contains "D-E5.12, D-E5.17".
- `test_v4_story_week_check_fails_on_the_v3_pattern`: must-fail, 4 problems on v3.
- New `test_v4_month_fill` (3 S): S-27 `steady-before-first`, S-26..S-22 `steady-before`, each tiling [00:00, 24:00)
  local through `resolve` with installs; no-run days in [S-28, S] == {S-10, S-4}. Must-fail in the same test: the
  un-amended v4 (six entries removed) still passes the week check but gives 7 month problems, the last
  "days with no run [-27..-22, -10, -4]".
- WK-GAP (`tools/demo_combined_finish.py` `wkgap`): week clause (commit 1): per measure (critical_served,
  daylight_headroom_kw, productive_kwh, avoidable_gen_min) NO_DATA exactly {S-4}, PARTIAL exactly {S}, COMPLETE the
  other five; Kobo days line "5 of 7 days checked · 1 partly checked"; CO-6 `gaps == missed`. New month clause:
  on [S-28, S], NO_DATA exactly the `missing`-kind days and PARTIAL exactly the story-only days, both from
  `ctx.site_days("kobo")` (`demo_rows.month_day_classes` / `month_gap_pattern`); no hard-coded date. A day with no
  snapshot counts as NO_DATA (passes only on a `missing` day; reported as `no_snapshot`).
- L0 `test_week_gap_pattern_passes_on_v4_and_fails_on_client4s_v3_pattern` (commit 1) and new
  `test_month_gap_clause_passes_on_amended_v4_and_fails_on_the_unbuilt_stretch`: must-fails on the un-amended v4,
  on v3 (S-4, S-2 also unbuilt), on any one measure reading a full day PARTIAL, and on a full day with no snapshot.
- WK-2a: S-1 money follows S-1's kind, `steady` 27.50 USD, `normal` (v3) 42.08 USD.
- WK-2b: study ending S with >= 1 eligible day reads a `LIMIT_UNKNOWN` sentence with no kW and no money; 0 eligible days
  still "No potential found yet".
- `vocabulary.limit_line`: n == 1 gives "Not judged yet: 1 of the 5 study days has no reading" (`test_ch4_opportunities`).
- New WK-FILL row (not idx, no assertion): reports each Kobo story day's epoch on [S-28, S-11] and the S-27..S-22 kinds.
- K7 `THREE_SITE_STORY_PINS` (v4): 1d50fb8f... / 65083 (db_now 11-08) and 1bfc7592... / 65081 (12-03); superseded
  v4 pins 91ea68a9.../50821, 9fe1af48.../50819 noted in the file. `THREE_SITE_STORY_PINS_V3` unchanged and passing,
  so only the day list moved the hash.

## Checks run (this session, revision 0f297432e; pytest from plan2 venv, absolute PYTHONPATH, one file at a time)

| File | Result |
|---|---|
| test_demo_story_days.py | 91 passed |
| test_demo_combined_finish_rows.py | 67 passed |
| test_demo_combined_finish_days.py | 1 passed |
| test_demo_combined_finish_co1.py | 5 passed |
| test_demo_combined_mill.py | 15 passed |
| test_own_g1_add_dates.py | 45 passed |
| test_demo_combined_links.py | 11 passed |
| test_k7_kisiwa_story.py (K7 + plan-freeze) | 101 passed (2 failed before the v4 re-pin) |
| test_k7f_kis10_window.py | 3 passed |
| test_ch4_opportunities.py (vocabulary pin) | 16 passed |
| Guards: check-architecture.ps1, check-agent-workflow.ps1 | see "Guards" below |

Not run: no prepare, no Postgres finish run, no full suite (demo-sprint policy). `demo_combined.py` has no offline
`--check` subcommand; the offline resolve on v4 and on v3 (the `--days` rollback) is exercised by
`test_default_file_validates_on_relative_dates` (both files, with installs and db_now) and the week/month tests.

Required checks: WK-GAP fails on the v3 pattern (L0 must-fails, week and month); the 3-S week test passes on v4 and
fails on v3; the v3 `--days` rollback resolves (13 full + 8 story-only) and its K7 pins are byte-equal.

## Expected vs actual (confirmable without a prepare)

| Figure | Expected (D-E5.18/20) | Actual (resolve) |
|---|---|---|
| Kobo days in [S-28, S+1]: full / story-only / no run | 22 / 6 / 2 | 22 / 6 / 2 (S-10, S-4) |
| Kobo runs | 22 x 3 + 6 = 72 | asserted by the (22, 6) row |
| Week S-6..S | 5 checked, 1 missed S-4, 1 partial S | holds for S = 11-07, 11-08, 11-09 |
| Month no-run days [S-28, S] | {S-10, S-4} | {S-10, S-4} for all 3 S |
| Board gap line, 31 days | 4 no data (S-30, S-29, S-10, S-4) · 5 partly (S-28, S-21, S-14, S-7, S) | calendar agrees; served value not read |
| Coverage, days line, Grow 137.50, MG-1 550.0 kWh, study 3-7 Nov, WK-2b, MILL-3, ACT-001/005, epochs of S-21/S-14, October totals | as D-E5.20 | need the build; not confirmed here |

## Stop rules for the fresh build (D-E5.13 §7 + D-E5.19 item 4)

Stop and report, do not tune, on a failure of: WK-GAP (week and month clauses), WK-2a, WK-2b, F-COH, F-CAL, SP-3,
SP-4, CO-5/SP-1 (its S-28 window now meets the full day S-27), CO-6, and the `demo_combined_after.py` reads.
Report, not a fault: the mill thread's RECURRED effective day (may move earlier; `recurrence_holds` "2026-10-31" is
S-dependent, `--s2` only), the WK-FILL epochs of S-21 and S-14, and any October productive-use total (about +252 kWh /
+63.00 USD expected). Fallback: `prepare --days backend/conversions/demo-story-days-v3.json`.

## Known deviations

- Label wording: "Story calendar (v4, D-E5.12, D-E5.17): ..." rather than the bare "v4 (D-E5.12, D-E5.17)"; the test pins
  the substring "D-E5.12, D-E5.17".
- WK-FILL is a new report-only row (not named by the card) so the epoch report has a home in the finish output.

## Residual risk

- The month clause requires every measure/subject's NO_DATA set on [S-28, S] to equal the `missing` days. If a subject
  lacks snapshot rows on some built day (e.g. a generator subject in October), WK-GAP fails at the build: that is a stop
  to report, not to tune.
- Prepare time grows about +13 min (estimate, D-E5.20).

## User review

Fresh Claude review per D-E5.13; no owner walkthrough required for this card.
