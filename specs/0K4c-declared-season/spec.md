# 0K4c: Kobo's declared season v2, with weather spells and a varying load (implementer spec)

Status: live, rev 2 (Architect, Claude, 2026-11-21; handshake answered by D-0K4.26, D-0K4.30). **1.0 unit.** Verification-depth review is enough
for the fixture, but it feeds a money figure, so a discovery reviewer reads it (W5). Non-screen. No migration. No
database. `USER_REVIEW_REQUIRED: false`. Rulings: `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.8, D-0K4.7, D-0K4.26).
Reviewer guide: `reviewer-guide.md`.

- **What it is.** A second declared 61-day Kobo season beside 0K2's v1, in the same fixture file: overcast spells of
  1 to 4 days, residential and clinic loads varying ±15 % day to day, the mill off on Sundays, and the assumed
  equipment of 0K4b on the Foundation. v1 stays byte-equal, so 0K2's and 0M's recorded studies stay reproducible.
- **Why next.** Review §5: the v1 season is "too kind" (overcast exactly every fourth day, never two in a row, the same
  load every day); the real risk is two or three overcast days in a row (§2 point 8). Lane 2, after 0K4b (D-0K4.1).
- **Builds on (`main` with 0K4b):** `host/tests/kobo_season.py` (whole), `host/tests/kobo_assumed.py`
  (`assumed_site`), `host/tests/test_0k2_kobo_season.py` (T8's pins, the coverage check of the 0K2 review).

## 0. Before you start

- Branch `task/0K4c-season-v2` off `main` after 0K4b's merge; worktree `/opt/assetecon/AssetOpsV1-0k4c`.
- **The split (D-0K4.26).** At the start, run `git merge-base --is-ancestor` with 0K4a's merge commit against
  `main`. If 0K4a is not on `main` (the expected case), S7 is its document half only and S8 is not built here: both
  frozen checks become 0K4d's V0. If 0K4a is on `main`, S7 and S8 are built whole. The packet says which applied.
- **Pre-flight print (packet, first section):** on `main` plus `inputs_digest` (§2), three hex digests:
  `inputs_digest(season_inputs(base_run(61), 61))` (v1), the `day_windows(d)` digest for d = 0 to 60 (v1), both kept
  for S6, and `inputs_digest(season_inputs(base_run(61), 61, season="v2"))`, kept for S9. All are v7 bases: inputs
  only, with no kernel run.
- **Files.** Edited: `host/tests/kobo_season.py` (additions only, §2). New: `host/tests/test_0k4c_season_v2.py`.
  Nothing else.
- **Heavy tools:** `pwsh -NoProfile -File tools/run-host-tests.ps1 -- host/tests/test_0k4c_season_v2.py` through the
  slot pool. No kernel run longer than 2 days (the 61-day runs are 0K4d's).

## 1. Outcome and gate questions

Does season v2 hold exactly the declared overcast calendar (21 of 61 days, spells of 1, 2, 3 and 4 days, 13 in
September and 8 in October), the declared per-day load multiplier (0.85 to 1.15) on the residential and clinic loads
only, and no mill load on the eight local Sundays? Does every series still cover each 5-minute step exactly once? Is
v1 unchanged to the byte? Does the season's Foundation carry the assumed equipment with its basis?

## 2. Design (additions to `host/tests/kobo_season.py`)

```python
#: D-0K4.8: declared, not climatology; Kobo's 61 days of readings replace it. Day index from 1 Sep 2026 (a Tuesday).
OVERCAST_V2 = frozenset({2, 3, 7, 8, 9, 13, 17, 18, 19, 20, 24, 25, 28, 33, 38, 39, 45, 50, 51, 52, 57})
def overcast_v2(day_index: int) -> bool: return day_index in OVERCAST_V2
def load_multiplier_v2(day_index: int) -> Fraction:
    return 1 + Fraction(15, 100) * Fraction((7 * day_index + 3) % 13 - 6, 6)      # 17/20 .. 23/20
def mill_on_v2(day_index: int) -> bool: return day_index % 7 != 5                  # off on local Sundays
def season_site_v2(document) -> None:                                              # v1's site plus 0K4b's assumptions
    season_site(document); assumed_site(document)
SEASONS = ("v1", "v2")
def inputs_digest(inputs) -> str: ...      # D-0K4.26: sha256 hex of the canonical text below
def windows_digest(days: int = 61) -> str: ...  # the same line form over day_windows(d), d = 0 .. days - 1 (v1)
```

`inputs_digest` text: one line per forcing, sorted, each holding every `ForcingInput` field in declaration order as
`name=value` joined by `|` (numbers as `str(Fraction)`), then one line per initial value,
`initial|<address>|<str(value)>|<unit>`, all joined by `\n` and encoded UTF-8.

`day_windows(day_index, overcast=overcast_v1, *, load_multiplier=None, mill_on=None)`: unchanged when both are `None`.
With `load_multiplier`, every residential and clinic row of that local day (night, day, dusk and late windows) has its
value multiplied by `load_multiplier(day_index)`; with `mill_on` returning `False`, every mill row of that day has
value 0 (the row is kept, so coverage is unchanged). Irradiance is never scaled.

`season_inputs(run, days, *, overcast=None, load_scale=Fraction(1), start_fuel_l=SEASON_START_FUEL_L,
site_stop_pct=None, season="v1")`: `overcast=None` means the season's own calendar (`overcast_v1` for v1,
`overcast_v2` for v2); a passed function overrides it. `season="v2"` also sets `load_multiplier=load_multiplier_v2` and
`mill_on=mill_on_v2`. A season not in `SEASONS` is `ValueError`. No current caller passes `overcast`, so v1 is
unchanged. `load_scale` still applies on top (0M halves the loads,
D-0M.3). `base_run(..., site_edit=season_site_v2, version=8)` is how 0K4d builds the v2 site; `base_run`'s defaults
are unchanged.

## 3. Tests (written first; `host/tests/test_0k4c_season_v2.py`, no kernel run over 2 days)

Expected values are the test's own literals and arithmetic (W2), never a call to the function under test.
- **S1 calendar:** `[d for d in range(61) if overcast_v2(d)]` equals the literal list of D-0K4.8; 13 below 30 and 8 from
  30; the spell lengths, read by the test's own run-length loop, are `[2, 3, 1, 4, 2, 1, 1, 2, 1, 3, 1]`.
- **S2 multiplier:** `load_multiplier_v2(d)` for d = 0 to 12 equals the literal sequence
  `37/40, 11/10, 19/20, 9/8, 39/40, 23/20, 1, 17/20, 41/40, 7/8, 21/20, 9/10, 43/40` (a literal in the test; the
  period 13 checked); minimum 17/20 and maximum 23/20 over 61 days.
"The file's value" in S3 and S4 is read by the test's own `yaml.safe_load` loop over the day-type YAML files that
`kobo_season` loads, never through `_series_events` or `day_windows` (D-0K4.26). Day 9 is overcast in v2, so the
overcast file is the reference.
- **S3 applied to res and clinic only:** for day 9 of `season_inputs(base_run(10, version=7), 10, season="v2")`, every
  res and clinic forcing value equals the file's value times 7/8 (`load_multiplier_v2(9)`, a literal), irradiance
  equals the file's, and mill equals the file's. The night rows are also asserted as literals: res 3 kW to 21/8 and
  clinic 2 kW to 7/4. A second case, with `load_scale=Fraction(1, 2)`, gives res and clinic the file times 1/2 times
  7/8 and the mill the file times 1/2 (0K4d's Mto path).
- **S4 Sundays:** the mill forcings of days 5 and 12 are all 0; days 4 and 6 equal the file's; the test's own weekday
  count gives eight Sundays in the window (days 5, 12, 19, 26, 33, 40, 47, 54) and `date(2026, 9, 6).weekday() == 6`.
- **S5 coverage:** for an 8-day v2 season, each of the four series covers every 5-minute step exactly once (the 0K2
  review's check), and no other address gains a forcing.
- **S6 v1 inputs unchanged:** `inputs_digest(season_inputs(base_run(61), 61))` and `windows_digest()` each equal the
  pre-flight's literal. The test also recomputes the first with its own loop over the canonical form, beside the
  literal.
- **S7 Foundation (document half):** `kobo_site(season_site_v2)` (`host/tests/kobo.py`) carries the three basis rows
  `GENERIC_DEFAULT` (no-load rate, minimum load, taper start) and the 20,000 L tank. **Frozen half, only when 0K4a is
  on `main`** (else 0K4d's V0): a 1-day `base_run(1, version=8, site_edit=season_site_v2)` has
  `frozen_world_inputs(run).initial_values` with `parameter_id` `model-need:generator-no-load-fuel-rate` = `11/200`,
  `model-need:generator-minimum-load` = `30` and `model-need:battery-charge-taper-start` = `95`, each answered by the
  Foundation.
- **S8 runs, only when 0K4a is on `main`** (else 0K4d's V0): a 2-day v2 season on v8 (`base_run(2, version=8,
  site_edit=season_site_v2)`) executes COMPLETED (smoke).
- **S9 v2 pinned as a whole:** `inputs_digest(season_inputs(base_run(61), 61, season="v2"))` equals the pre-flight's
  literal. Docstring: "a change here is a new season, never an edit". 0K4d's `study.json` records the same digest.

**Regression:** `host/tests/test_0k2_kobo_season.py` (unchanged, green), `host/tests/test_0m_mto_headroom.py`
(green), check-all (fast) once.

## 4. Units

| Commit | Content |
|---|---|
| 1 (1.0) | §2, S1-S7 and S9 (S7 and S8 whole only if 0K4a is on `main`), regression, packet |

Packet `specs/0K4c-declared-season/packet.md`: which split applied, the three pre-flight digests, the calendar as two
61-character rows (row 1 weather, `C` or `O`; row 2 Sundays, `S` or `.`), the multiplier range, S5's coverage counts, the regression output, the mid-build count. The packet
says the season is declared and SIMULATED, not a Kobo record.

## 5. Done (questions; each can fail)

1. Does v2 hold the declared calendar, spells, multiplier and Sundays, and only those?
2. Does every series cover every step once, with no new address?
3. Are v1's inputs unchanged (both digests), so 0K2 and 0M stay reproducible, and is v2 pinned as a whole (S9)?
4. Does the v2 Foundation carry the assumptions with their basis?
5. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 6. Out of scope

Running the 61-day studies (0K4d); any weather other than the two shipped day types (a partly cloudy type waits for
Kobo's readings); any change to v1, 0K2's or 0M's figures.
