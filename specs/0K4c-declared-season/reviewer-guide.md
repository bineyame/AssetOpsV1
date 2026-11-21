# 0K4c reviewer guide

Architect (Claude), 2026-11-21, rev 1. Read `spec.md` and D-0K4.8 in `specs/0K4-dispatch-model-review/rulings.md`,
then the diff. Done means every question of spec §5 answers yes with evidence and every plant fails its named test.

## What to check, and how

1. **Declared, not tuned.** The calendar, multiplier formula and Sunday rule in the code equal D-0K4.8 literally. Any
   change to them in the diff, or a figure run to pick them, is High (figures are outputs).
2. **Independent expected values.** S1-S4 use literals and the test's own loops; none calls the function it checks.
3. **v1 untouched.** S6's digest equals the pre-flight value; `git diff` shows additions only in `kobo_season.py`
   (new names and keyword arguments with defaults that reproduce v1).
4. **Scope of the multiplier.** Residential and clinic rows of the whole local day, never irradiance or the mill.
5. **Labels.** The module docstring and the packet say SIMULATED and "declared, not climatology"; nothing says observed.

## Plants (each must fail the named test; revert after)

| # | Plant | Must fail |
|---|---|---|
| P1 | day 20 dropped from `OVERCAST_V2` | S1 |
| P2 | the multiplier applied to the mill | S3 |
| P3 | the multiplier applied only to 06:00-18:00 rows | S3 (night rows of day 9) |
| P4 | Sunday rule `d % 7 == 6` | S4 |
| P5 | the mill row deleted instead of set to 0 on Sundays | S5 |
| P6 | `season_inputs` default changed to `"v2"` | S6 |
| P7 | `season_site_v2` without `assumed_site` | S7 |

## What counts as done

All of spec §5 yes; P1-P7 each fail; mid-build count 0.
