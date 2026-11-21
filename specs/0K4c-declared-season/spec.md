# 0K4c: Kobo's declared season v2, with weather spells and a varying load (implementer spec)

Status: live, rev 1 (Architect, Claude, 2026-11-21); handshake next. **1.0 unit.** Verification-depth review is enough
for the fixture, but it feeds a money figure, so a discovery reviewer reads it (W5). Non-screen. No migration. No
database. `USER_REVIEW_REQUIRED: false`. Rulings: `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.8, D-0K4.7).
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
- **Pre-flight print (packet, first section):** on `main`, a stable digest of `season_inputs(base_run(61), 61)` (v1):
  `sha256` over the sorted `(address, offset, duration, value)` of every forcing plus the initial values, printed as
  hex; kept for S6.
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
```

`day_windows(day_index, overcast=overcast_v1, *, load_multiplier=None, mill_on=None)`: unchanged when both are `None`.
With `load_multiplier`, every residential and clinic row of that local day (night, day, dusk and late windows) has its
value multiplied by `load_multiplier(day_index)`; with `mill_on` returning `False`, every mill row of that day has
value 0 (the row is kept, so coverage is unchanged). Irradiance is never scaled.

`season_inputs(run, days, *, overcast=overcast_v1, load_scale=Fraction(1), start_fuel_l=SEASON_START_FUEL_L,
site_stop_pct=None, season="v1")`: `season="v2"` means `overcast=overcast_v2` (unless the caller passes one),
`load_multiplier=load_multiplier_v2` and `mill_on=mill_on_v2`. `load_scale` still applies on top (0M halves the loads,
D-0M.3). `base_run(..., site_edit=season_site_v2, version=8)` is how 0K4d builds the v2 site; `base_run`'s defaults
are unchanged.

## 3. Tests (written first; `host/tests/test_0k4c_season_v2.py`, no kernel run over 2 days)

Expected values are the test's own literals and arithmetic (W2), never a call to the function under test.
- **S1 calendar:** `[d for d in range(61) if overcast_v2(d)]` equals the literal list of D-0K4.8; 13 below 30 and 8 from
  30; the spell lengths, read by the test's own run-length loop, are `[2, 3, 1, 4, 2, 1, 1, 2, 1, 3, 1]`.
- **S2 multiplier:** `load_multiplier_v2(d)` for d = 0 to 12 equals the literal sequence
  `37/40, 11/10, 19/20, 9/8, 39/40, 23/20, 1, 17/20, 41/40, 7/8, 21/20, 9/10, 43/40` (a literal in the test; the
  period 13 checked); minimum 17/20 and maximum 23/20 over 61 days.
- **S3 applied to res and clinic only:** for day 9 of `season_inputs(base_run(10, version=7), 10, season="v2")`, every
  res and clinic forcing value equals the shipped file's value times `load_multiplier_v2(9)` (computed by the test as a
  literal), irradiance equals the file's, and mill equals the file's.
- **S4 Sundays:** the mill forcings of days 5 and 12 are all 0; days 4 and 6 equal the file's; the test's own weekday
  count gives eight Sundays in the window (days 5, 12, 19, 26, 33, 40, 47, 54) and `date(2026, 9, 6).weekday() == 6`.
- **S5 coverage:** for an 8-day v2 season, each of the four series covers every 5-minute step exactly once (the 0K2
  review's check), and no other address gains a forcing.
- **S6 v1 byte-equal:** the digest of `season_inputs(base_run(61), 61)` equals the pre-flight value; `day_windows(d)`
  with no new argument equals `main`'s for d = 0 to 60.
- **S7 Foundation:** a 1-day `base_run(1, version=8, site_edit=season_site_v2)` freezes the three v8 needs as initial
  values (no-load 3.3 L/h as `11/200` L/min, minimum load 30, taper start 95), its Foundation document carries the
  three basis rows `GENERIC_DEFAULT`, and the tank is 20,000 L.
- **S8 runs:** a 2-day v2 season on v8 (`base_run(2, version=8, site_edit=season_site_v2)`) executes COMPLETED (smoke).

**Regression:** `host/tests/test_0k2_kobo_season.py` (unchanged, green), `host/tests/test_0m_mto_headroom.py`
(green), check-all (fast) once.

## 4. Units

| Commit | Content |
|---|---|
| 1 (1.0) | §2, S1-S8, regression, packet |

Packet `specs/0K4c-declared-season/packet.md`: the pre-flight digest, the calendar as a 61-day strip (C clear, O
overcast, S Sunday), the multiplier range, S5's coverage counts, the regression output, the mid-build count. The packet
says the season is declared and SIMULATED, not a Kobo record.

## 5. Done (questions; each can fail)

1. Does v2 hold the declared calendar, spells, multiplier and Sundays, and only those?
2. Does every series cover every step once, with no new address?
3. Is v1 byte-equal, so 0K2 and 0M stay reproducible?
4. Does the v2 Foundation carry the assumptions with their basis?
5. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 6. Out of scope

Running the 61-day studies (0K4d); any weather other than the two shipped day types (a partly cloudy type waits for
Kobo's readings); any change to v1, 0K2's or 0M's figures.
