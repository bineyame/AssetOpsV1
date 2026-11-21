# 0K4b review

## Round 1: discovery review (W5), fresh Claude reviewer, 2026-11-21

Head `81816c9f5` on `task/0K4b-fuel-curve`, diffed against merge-base `b96d5e978`.

**Summary (verdict: ACCEPT)**
- The curve is right. I recomputed it with `Fraction`: slope 87/400 (0.2175), 3.3 / 5.475 / 7.65 / 9.825 / 12 L an hour at 0-100 % load, a 5-minute STARTING step burns 11/40 L, and the F6 cap is exactly 40 kW. The taper gives 15 at 97.5 %, the floor of 3/2 at 99.9 %, and F8 steps of 9/20 (start 95) and 9/9 (start 100). All of these match the tests and the packet.
- The no-load rate is never converted. The module has no `float(` and no `round(`, and its one `60` is `MINUTES_PER_HOUR`. F11 runs the contract's `frozen_canonical_value` and `normalize_authored_float`. F12 pins the constants as literals.
- No template or digest moves. `git diff` of `config/`, `contracts/`, `tools/`, `packs/mini_grid.py`, `packs/minigrid.py` and `host/forward_replay.py` is empty. The pre-flight shows 0 differing (boundary, field) pairs, and the only run-document difference is `run_id`.
- Served text follows D-0K4.19. The four names and three needs are `Message`s through `served_text`, legacy names stay `str`, and the statement guard is OK with no `HAND_BUILT_NEW` and 2 allowed entries (unchanged). `_share_of_rating` uses generator wording.
- I accept KD1-KD3. `parse_foundation_content` does not parse component properties, so `parse_site_document` is the right path. One `MINUTES_PER_HOUR` matches the spec's own cap formula. The three exact-set extensions are hand literals.
- Plants: the 7 builder plants I re-applied failed as stated, and so did 3 of my own.
- Check-all (fast) on the head: `All 42 guards passed (blocking; 0 advisory, 0 warned).`
- 4 Low findings, none blocking.

### Findings

**L1 (residual risk for 0K4a, not an acceptance gap): `fuel_curve` accepts any rating.**
`simulator/assetops_simulator/packs/generator_curve.py:84`. `rated_kw == 0` raises `ZeroDivisionError` instead of `CurveRefused`, and a negative rating is accepted with an inflated slope. The spec lists only three refusals, so this is within contract. 0K4a must feed a rating that has already been checked as positive, or add a `RATING_NOT_POSITIVE` code.

**L2 (residual risk for 0K4a): `output_cap_kw` with `minutes == 0`.**
`generator_curve.py:115`. When the slope is not zero and `fuel_l >= 0`, the call divides by `slope x 0` and raises `ZeroDivisionError`. 0K4a's per-segment resolver must never call it on a zero-length segment, or the function should guard that case.

**L3 (preference): F8 pins one count of two.**
`simulator/tests/test_generator_curve.py:162-164`. The test asserts `lower == 9` but only `upper > lower`, while the packet prints 20. Pinning `upper == 20` would make a change to the taper's shape fail by number, not only by direction.

**L4 (outside the diff, for the Architect): one quantity, two figures.**
`specs/0K4-dispatch-model-review/rulings.md`, D-0K4.5, says "about 0.54 L/kWh at a quarter load". The exact value is 0.5475 (219/400), which rounds to 0.55. The packet and the tests are right. Correct the ruling's figure when it is next touched, per the owner's one-figure rule.

### Checks run (this reviewer, head `81816c9f5`)
- `pytest tests` from `simulator/`, whole: `528 passed in 12.74s`.
- Backend, from `backend/`: `test_0k4b_properties.py`, `test_component_properties.py`, `test_sc1_statements.py`, `test_w205a_ev_vocabulary.py`, `test_w402_roles_properties.py` and `test_model_owned_needs.py` gave `611 passed in 4.59s`. This includes the three KD3 files, which postdate the packet's run.
- Host `test_0k4b_kobo_assumed.py`: `2 passed`, with the worktree's packages first on `PYTHONPATH`. Run from `host/` without that, it imports the main checkout's `assetops_backend` (the shared venv's editable installs) and P5 fails. That is an environment effect, not a defect. The builder's host run is green in the same way as `run-host-tests`.
- `tools/checks/statement_catalogue.py`: `OK statement catalogue: load, coverage, legacy, scan (2 adopted), keys, imports`, with 2 allowed entries.
- Check-all (fast), on the head through the slot pool: `All 42 guards passed (blocking; 0 advisory, 0 warned).` (138 s).
- I recomputed F1-F8 independently with `Fraction` in a scratch script.
- Readers of `PropertyDefinition.display_name`: `sites_api.py:147` is the only one, and it goes through `served_text`. `foundation_parsing.py:1099/1118` reads a different definition type.

### Plants (applied in the worktree, run, reverted; the tree was clean afterwards)
| Plant | Failed |
|---|---|
| Builder P4, rate x minutes / 60 | F1, F2, F3, F4, F11 |
| Builder P5, slope checked before SFC | F5 |
| Builder P10, floor 1/10 | F7, F12 |
| Builder P12, `display_name` as a `str` | statement guard `HAND_BUILT_NEW sites/models.py:302` |
| Builder P13, `assumed_site` overwrites | P5 (`a_key_already_present`) |
| Reviewer R1, `_taper_start` accepts 0 | F10 |
| Reviewer R2, `output_cap_kw` drops the idle burn | F6 |
| Reviewer R3, `battery-charge-taper-start-basis` carried by GENERATOR | P1, P3 |

### Not verified
- I did not rerun the builder's backend non-Postgres selection (252 files) or the six failures it attributes to `main`. I cite them at `b17977d87`.
- I did not rerun the pre-flight. I read `preflight.txt` in the evidence folder.
- I did not run the Postgres part of `select-tests`. Neither did the packet.

### Residual risk the packet does not name
- `assumed_site` is not atomic. If a battery key collides, the generator rows have already been appended before the `KeyError`. Callers treat the error as fatal, so this is harmless today.
- L1 and L2 move to 0K4a's resolver: zero or negative ratings and zero-length segments.
