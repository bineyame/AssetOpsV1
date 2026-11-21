# 0K4b packet: the generator's fuel curve and the battery's charge taper

Implementer (Claude), 2026-11-21. Branch `task/0K4b-fuel-curve` (base `main` `b96d5e978`); commits `72af72161`
(module, F1-F12), `d6f108613` (Foundation, needs, fixture, SC-1 words, P1-P6), and this packet. Spec rev 2; rulings
D-0K4.19 to D-0K4.21. `USER_REVIEW_REQUIRED: false`. Evidence: `/opt/assetecon/evidence/0K4b/`.

## Pre-flight print (D-0K4.20)

Script `preflight.txt` in the evidence folder; 97 boundaries compared in item 3b, so the compared set is not empty.

1. `kobo_draft("kobo-mini-grid-prolonged", timestep_minutes=5, model_profile="mini-grid", model_profile_version=7,
   site_edit=assumed_site)` carries **no** frozen value for `generator-no-load-fuel-rate` (nor the two new keys). v7
   does not need them. The frozen run document is identical with and without `assumed_site` except the random `run_id`.
2. `host/tests/test_registered_kobo_execution.py`, unchanged: green (in the host line below).
3. v7, with and without `assumed_site`, boundary by boundary (stocks, interval measurements, discrete states and
   every other `BoundaryState` field):
   a. The spec's call as written (default window 2026-09-22 03:00-15:00Z): both runs `FAILED` the same way at offset
      480 (`FORCING_NOT_AVAILABLE`, irradiance: the prolonged scenario declares no window that late). 96 boundaries
      each, 0 differing pairs, equal `inputs_identity`.
   b. The prolonged scenario's own window (2026-10-13 03:00-11:00Z): both `COMPLETED`, 97 boundaries each,
      **0 differing (boundary, field) pairs**, equal `inputs_identity`.
   Why equal: a frozen run carries only the model's Foundation needs, not every Site property.

## Acceptance (spec §5)

1. **Yes.** F1 (0 kWh for 1 h: 3.3 L), F2 (40 kWh: 12 L = 0.3 x 40), F3 (5.475 L, 7.65 L, litres per kWh strictly
   falling), F4 (STARTING 5 min: 0.275 L; STOPPED and FAILED 0; output while STARTING: `ValueError`).
2. **Yes.** F11: `frozen_canonical_value(3.3, "L/h")` then `normalize_authored_float` gives `L/min`, `11/200`; a
   5-minute STARTING step burns `11/40` L. No `/ 60` in any test. The module has one literal `60`
   (`MINUTES_PER_HOUR = Fraction(60)`), used by the slope and by `output_cap_kw` (KD2).
3. **Yes.** F7 (95 %: 30; 97.5 %: 15; 99.9 %: floor 1.5; start 100 at SOC 100: 30; SOC 100.1 raises); F8 below.
4. **Yes.** F5 checks each refusal and two overlaps (no-load first; then SFC before slope); F10 refuses through
   `consume`, with the exact minimum-load sentence.
5. **Yes.** P1-P3 (KD1 for the parser), P5; `git diff main...HEAD -- config/` empty; Kobo digest tests green.
6. **Yes.** Four `foundation_property` entries, `foundation.property_name`, `model_profile.need` (three variants),
   each with a hand case; `git diff main -- tools/` empty; statement guard `OK`, no `HAND_BUILT_NEW`.
7. **Yes**, plants below. Mid-build count: **3** (all resolved by content with a default; see below), not 0.

## F3 table: assumed (GENERIC_DEFAULT)

| Load | kW | Litres an hour | Litres per kWh |
|---|---|---|---|
| 0 % | 0 | 3.3 | not defined (no output) |
| 25 % | 10 | 5.475 | 0.5475 |
| 50 % | 20 | 7.65 | 0.3825 |
| 75 % | 30 | 9.825 | 0.3275 |
| 100 % | 40 | 12 | 0.3 |

## F8 step counts (5-minute steps, 30 kW limit, 200 kWh, 95 %)

Taper start 95: 80 to 90 % takes 9 steps; 90 to 100 % takes 20. Taper start 100: 9 and 9.

## Checks (revision `d6f108613`)

- `pytest simulator/tests` (whole): `528 passed in 13.43s`.
- Host: `test_registered_kobo_execution.py`, `test_0k2_kobo_season.py`, `test_0k4b_kobo_assumed.py`:
  `20 passed, 1 warning in 84.60s`.
- Backend: `test_component_properties.py`, `test_sc1_statements.py`, `test_0k4b_properties.py`,
  `test_model_owned_needs.py`: `500 passed in 4.11s`.
- `tools/checks/statement_catalogue.py`: `OK statement catalogue: load, coverage, legacy, scan (2 adopted), keys,
  imports`; allowed entries 2 (unchanged).
- `tools/select-tests.py --base main`: 474 of 587 backend files selected (`models.py`, `profiles.py` are widely
  imported). The non-Postgres part of that selection: 252 files at `b17977d87`, `-n 2`: `8 failed, 6696 passed, 154 skipped in 266.87s`. Two failures were this unit's (exact-set tests, KD3; fixed, `111 passed`). The other six fail the same way on the main checkout at `e39a5d2fa`, without this branch: `test_demo_combined_finish_rows` kis8, `test_k7_kisiwa_story` test_8, `test_s1_cutover` analytics 503, two in `test_w302_evidence_api` ('Opens this range'), and one in `test_w302_money_api` (log `backend-selected-nonpg.txt`). The Postgres part was not run (full-suite scale;
  coordinator's call).
- check-all (fast), at `b17977d87`: `All 42 guards passed (blocking; 0 advisory, 0 warned).` (log `check-all.txt`). The KD3 test-only edits came after it; none of the 42 guards reads them.
- Tests first: the new backend and host test files fail at collection against `main`'s implementation (imports
  missing), checked by restoring `main`'s files in the worktree and putting them back.

## Plants (each applied, run, reverted; `plants-module.txt` and `p12.txt` in the evidence folder)

| # | Fails |
|---|---|
| P1 no-load term dropped while RUNNING | F1, F2, F3 |
| P2 slope = sfc | F2, F3, F5, F6 |
| P3 STARTING burns 0 | F4, F11 |
| P4 rate x minutes / 60 | F1, F2, F3, F4, F11 |
| P5 slope checked before SFC | F5 |
| P6 floor 0 | F7, F8 (never reaches 100), F12 |
| P7 taper below the start | F7 |
| P8 basis set gains `ASSUMED` | P2 (generator basis) |
| P9 minimum load carried by BATTERY | P1, P3 |
| P10 floor 1/10 | F7, F12 |
| P11 `daytime._percentage(...)` | F10 |
| P12 a new `display_name` as a `str` | statement guard exit 1, `HAND_BUILT_NEW backend/assetops_backend/sites/models.py:296` |
| P13 `assumed_site` overwrites | P5 (`a_key_already_present`) |

## Known deviations

- **KD1. P1-P3's parser.** `sites/foundation_parsing.py:parse_foundation_content` parses topology, devices, signal
  mappings, control assumptions and site controls only. It never reads component properties, and the carrier rule is
  `minigrid_foundation.validate_minigrid_properties`. Both run inside `sites/site_parsing.py:parse_site_document`
  (:153, :199). P1-P3 therefore parse the rendered Kobo document with the six inline rows through
  `parse_site_document`, the Site-document Foundation parse. The rest of D-0K4.21 R5 holds: the rows are inline,
  there is no `sys.path` edit, and P5 is on the host.
- **KD2. One `60`, two uses.** Spec §2.1 writes `output_cap_kw` with `slope * minutes / 60`, and also says the
  module's only `60` is the slope's. The module defines `MINUTES_PER_HOUR = Fraction(60)` once. Both the slope and
  the cap's kWh in a step use it. The no-load rate is never converted (F11 and P4 prove it).
- **KD3. Three test files not in the Files list. Each pins an exact set the new keys join.**
  - `test_sc1_statements.py` T8 lists the shipped statement and vocabulary keys, and adopters add theirs (3A7 and
    3C2 did). It gains `foundation.property_name`, `model_profile.need` and `foundation_property`.
  - `test_w205a_ev_vocabulary.py` pins `STATE_PROPERTY_VALUES`. It gains the two basis sets.
  - `test_w402_roles_properties.py` pins the mini-grid units, kinds and carriers. It gains the four rows.

  Every addition is a hand literal.

## Mid-build questions (3; each resolved by its default, nothing blocked)

1. P1-P3 parser. Default: `parse_site_document` (KD1).
2. The `/60` in `output_cap_kw`. Default: one named constant (KD2).
3. Exact-set tests outside the Files list. Default: extend them with hand literals (KD3).

## Residual risk and review focus

- Nothing runs these laws until 0K4a assembles v8. `git grep generator_curve` lists only the module, its test and
  the specs.
- `served_text` renders at read. `sites_api` serves `display_name` for the four new keys only when a Site declares
  them, and no shipped Site does.
- Review focus: F1-F3 and F6-F8 hand arithmetic (module docstring and test docstring); KD1.
