# 0K4c reviewer guide

Architect (Claude), 2026-11-21, rev 2. Read `spec.md`, D-0K4.8 and D-0K4.26 in `specs/0K4-dispatch-model-review/rulings.md`,
then the diff. Done means every question of spec §5 answers yes with evidence and every plant fails its named test.

## What to check, and how

1. **Declared, not tuned.** The calendar, multiplier formula and Sunday rule in the code equal D-0K4.8 literally. Any
   change to them in the diff, or a figure run to pick them, is High (figures are outputs).
2. **Independent expected values.** S1-S4 use literals and the test's own loops (S3 and S4 read the YAML with their own
   `yaml.safe_load`); none calls the function it checks. S6's recomputation is the test's own loop.
3. **v1 untouched, v2 pinned.** S6's two digests and S9's equal the pre-flight values; `git diff` shows additions only in `kobo_season.py`
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
| P7 | `season_site_v2` without `assumed_site` | S7 (document half) |
| P8 | `mill_on_v2` returns `True` from day 41 onwards | S9 (S4 stays green) |

## What counts as done

All of spec §5 yes; P1-P8 each fail; the packet says which split of D-0K4.26 applied; mid-build count 0.
