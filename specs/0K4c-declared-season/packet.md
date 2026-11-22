# 0K4c packet: Kobo's declared season v2

Implementer (Claude), 2026-11-21. Branch `task/0K4c-declared-season` (the dispatch's name; the spec's §0 says
`task/0K4c-season-v2`), worktree `/opt/assetecon/AssetOpsV1-0k4c`, base `main` `ec8e64d3f` (descendant of the
dispatch's `68a4ba6c0`; the two commits between touch only four backend tests). Spec rev 2, reviewer guide rev 2,
rulings D-0K4.8, D-0K4.26. `USER_REVIEW_REQUIRED: false`.

**Season v2 is declared, not climatology, and SIMULATED. It is not a Kobo record. Kobo's 61 days of readings replace it.**

## Pre-flight

- **Split (D-0K4.26):** `git merge-base --is-ancestor task/0K4a-dispatch-v8 main` exits 1, so 0K4a is **not** on
  `main`. Built: S1-S6, S9 and S7's document half (three basis rows and the 20,000 L tank). S7's frozen half and S8
  are 0K4d's V0.
- **Digests** (v7 bases, inputs only, no kernel run). The two v1 digests come from `main`'s `kobo_season.py` with only
  `inputs_digest` and `windows_digest` added, run from a scratch copy. The branch reproduces both exactly.
  - `inputs_digest(season_inputs(base_run(61), 61))` (v1): `59d6456b88ddbe0760866971cd919944ca3ca9491b92471ea6c6f9b4c20b1c38`
  - `windows_digest()` (v1 `day_windows(d)`, d = 0 to 60): `f2f0088e743eade44dc96e428b749dac42d86d3388df9645b7ce8e21971cd3de`
  - `inputs_digest(season_inputs(base_run(61), 61, season="v2"))` (S9): `465ab6e0818f3fbd6d15a3fbb2a30b6ab75ad1e3cfaa250d6c3b9807f4cdb1a8`
- No question was open at the start: the handshake is marked answered, and D-0K4.26 to D-0K4.30 answer every row.

## Files

- `host/tests/kobo_season.py`: new names and new keyword arguments only. These are `OVERCAST_V2`, `overcast_v2`,
  `load_multiplier_v2`, `mill_on_v2`, `season_site_v2`, `SEASONS`, `inputs_digest` and `windows_digest`. `day_windows`
  gains `load_multiplier=None, mill_on=None`, and its old body is now `_day_rows`. `season_inputs` gains
  `overcast=None` (I3) and `season="v1"`, and an unknown season is `ValueError`. The docstring says the season is
  declared and SIMULATED.
- `host/tests/test_0k4c_season_v2.py` (new; 10 tests).

## Season v2 calendar (day 0 = Tue 1 Sep 2026)

```
CCOOCCCOOOCCCOCCCOOOOCCCOOCCOCCCCOCCCCOOCCCCCOCCCCOOOCCCCOCCC   weather (C clear, O overcast)
.....S......S......S......S......S......S......S......S......   Sundays (mill off)
```

21 overcast days: 13 below day 30 and 8 from day 30. The spells are `[2, 3, 1, 4, 2, 1, 1, 2, 1, 3, 1]`. Days 19 and
33 are both overcast and Sundays. The residential and clinic load multiplier has period 13 and runs from 17/20 to
23/20 (0.85 to 1.15).

## Acceptance (spec §3, §5)

| Check | Result |
|---|---|
| S1 calendar | literal list, 13/8 split, spells checked by the test's own run-length loop: pass |
| S2 multiplier | 13 literals, period 13, min 17/20, max 23/20: pass |
| S3 res and clinic only | day 9 equals the test's own `yaml.safe_load` reader of the four day-type files x 7/8 on res and clinic. Irradiance and the mill equal the file. Night literals are 21/8 and 7/4. The `load_scale=1/2` case passes too |
| S4 Sundays | mill on days 5 and 12 is 13 rows of 0. Days 4 and 6 equal the file. The test's own weekday count gives 8 Sundays, and `date(2026,9,6).weekday()==6`: pass |
| S5 coverage | 8-day v2 season: each of the 4 series has 104 rows covering 2,304 steps exactly once. The address set equals the base run's: pass |
| S6 v1 unchanged | both literals match, and so does the test's own recomputation of the canonical form. Unknown season gives `ValueError`: pass |
| S7 document half | `kobo_site(season_site_v2)`: three `-basis` rows `GENERIC_DEFAULT` (values 3.3, 30, 95), with tank-capacity and rating 20000: pass |
| S8, S7 frozen half | not built here (0K4d V0, D-0K4.26) |
| S9 v2 pinned | literal matches, and so does the test's own recomputation: pass |

## Checks run (revision `12851e0b8`; evidence `/opt/assetecon/evidence/0K4c/run1/`)

- First run, before the literals were filled: `2 failed, 8 passed` (S6 and S9 against `PENDING`).
- `tools/heavy-slot.sh -- ... run-host-tests.ps1 -- host/tests/test_0k4c_season_v2.py`: `10 passed in 1.46s`.
- Regression: `test_0k2_kobo_season.py`, `test_0m_mto_headroom.py` and `test_0k4b_kobo_assumed.py` gave
  `24 passed in 111.75s`.
- `check-all.ps1` (fast) once: `All 42 guards passed (blocking; 0 advisory, 0 warned)`, 144.2 s wall.
- The job's wall time was 21m57s, most of it spent waiting for a heavy slot.

## Plants (reviewer guide; each was applied by script, then reverted with `git checkout`, and the tree was clean after)

| Plant | Named test | Fails |
|---|---|---|
| P1 day 20 dropped | S1 | S1, S9 |
| P2 multiplier on the mill | S3 | S3 (both cases), S4, S9 |
| P3 multiplier only 06:00-18:00 | S3 | S3 (both cases), S9 |
| P4 Sunday `d % 7 == 6` | S4 | S4, S9 |
| P5 Sunday mill row deleted | S5 | S4, S5, S9 |
| P6 default `season="v2"` | S6 | S6 |
| P7 no `assumed_site` | S7 | S7 |
| P8 mill on from day 41 | S9 | S9 only (S4 green) |

## Known deviations

- The branch name follows the dispatch (`task/0K4c-declared-season`), not spec §0.
- Order of work: the §2 code was written in the same sitting as the tests and before them. The fail-first evidence
  for each check is the plant table above, not a red-then-green run per test.
- The `initial|...` lines of `inputs_digest` keep the frozen order and are not sorted. The ruling leaves this open,
  and the test's own recomputation follows the same reading. The `windows_digest` line uses the field names
  `address`, `offset_minutes`, `duration_minutes` and `value`.

## Residual risk and review focus

- S9's digest is what 0K4d's `study.json` must record. Any later edit to the v2 branch is a new season.
- Review focus: guide check 4 (scope of the multiplier) in `day_windows`; S3's reader is independent of
  `_series_events`.

Mid-build questions: 0.
