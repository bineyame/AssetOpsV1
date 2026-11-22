# DD3b review packet (DD3b1 + its D-DD.145 fix round; DD3b2 part 1 of the writer, PARTIAL)

Branch `task/DD3b-mini-plant` (worktree `/opt/assetecon/AssetOpsV1-dd3b`), base main `6e3c02ab5`. Part 1 of 3
(D-DD.142: DD3b1 2.0 u). Scope: D-DD.127 and spec DD §4.3, in `simulator/assetops_simulator/packs/mini_grid.py` and
tests only. DD3b2 (writer units, D-DD.97/104/126/128/129/132) and DD3b3 (D-DD.92/130/131) follow.
`USER_REVIEW_REQUIRED`: no (no screen, no figure moved; the owner-approved D-DD.97 lands in DD3b2).

## What was built

- `MINI_GRID_V9_MODEL` (`mini-grid` 9) = v8 + `V9_SENTENCE`, appended after v8; v1-v8, the kernel, the contracts and
  the writer are untouched (`git diff main -- simulator/assetops_simulator` adds lines only, after line 1875).
- **Lifecycles (D-DD.127).** `GENERATOR_LIFECYCLE_V9`: v8's transitions plus STOPPED/STARTING/RUNNING → FAILED and
  FAILED → STOPPED. `INVERTER_LIFECYCLE`: `inverter-state` AVAILABLE ↔ FAILED, scenario-owned initial value
  (refused when absent, never assumed). v8's `GENERATOR_LIFECYCLE` (and its FAILED-initial rule) is unchanged.
- **Unit events.** `unit-fail@<unit>` / `unit-restore@<unit>` FORCING handlers (value 1, dimension COUNT), in a
  `unit-event` relation. `commit_v9` applies the events the step holds at the step's start (`point-applied-once`),
  before v8's lifecycle; a fail of a FAILED unit, a restore of a unit not FAILED, or an unknown unit refuses.
- **Units (§4.3).** Generators and inverters in component code order; the Site's plant, tank and control policy are
  read by v8's own readers from the lead units (`_lead_context`); another unit may restate the policy, never differ.
  The view adds each unit's state, running time and rating and P = max(0, demand + battery acceptance − available
  solar); `decide_v9` runs `decide_v8` for the Site (battery request, whether the set runs), then asks the shortest
  non-empty prefix of non-FAILED units whose summed rating ≥ P to run; a unit outside it keeps running to its minimum
  runtime, a STARTING one keeps starting. `due_v9` runs v8's start delay per unit.
- **Resolution (`_resolve_units`).** The RUNNING units act as one set in v8's `cycle_charge_split`: usable rating =
  the largest set output at which no unit exceeds its own (fuel-capped) rating, set minimum = the smallest at which
  every unit is at or above its own minimum load, each unit carrying output × rating / Σ rating. Each unit burns on
  its own curve (STARTING: no-load); the tank is the Site's one. Solar is split by `pv-array-share` and clipped per
  inverter; a FAILED inverter's share is clipped whole. Per-unit flows `generator_output:<unit>`, `pv_ac:<inv>` with
  balances `generator-units`, `inverter-units`; readings per unit: `generator-output-power@<unit>`,
  `pv-ac-power@<inv>`, `pv-available-power@<inv>`; every v2-v6 measure is kept.
- **One-unit fast path.** With one generator and one inverter (inverter AVAILABLE) `prepare/due/view/decide/commit/
  resolve` hand the step to v8's callables; `EXECUTABLE_MODELS` is not registered (D-DD.127 default).

## Tests (`simulator/tests/world/test_mini_grid_v9.py`, 10 tests, about 51 s)

- Written first, commit `299afe6e9`; the run failed at collection: `AttributeError: module
  'assetops_simulator.packs.mini_grid' has no attribute 'MINI_GRID_V9_MODEL'`.
- C-DD19 (mini part): v8 and v9 on Kobo's October inputs (the writer's `frozen_inputs` on the fixture view's books,
  8929 boundaries, the generator runs): equal digest over every boundary and transition, with only v9's
  `inverter-state` entries projected out (named projection; they are asserted AVAILABLE throughout).
- The unit path forced onto Kobo's one of each for a week equals v8 in every stock, transition and interval
  measurement (evidence that the multi-unit code lifts v8's rule rather than approximating it).
- Two sets (Kobo re-rated to 20 kW plus a 24 kW test set): the second joins only after the lead, outputs in ratio
  20:24, per-unit sum = the set's output. A fail 12 min into a run lands at its step (RUNNING → FAILED), the unit
  carries nothing until the restore (FAILED → STOPPED) and the second set carries meanwhile. A failed inverter
  (11:02-style instant, 06:02) gives 0 from its step; the other keeps its half. v9 runs a one-unit fail that v8
  refuses. Refusals: restore of a running unit, an unknown unit, a missing inverter state, shares summing to 3/4+1/2.

## Plants

1. `_fast` forced to `False` (the one-unit fast path removed): C-DD19's October test FAILED
   (`a8644171... != f5c3837f...`); reverted with `git checkout`.
2. Proportional split replaced by an equal split (`kw / len(running)`): the two-set test FAILED
   (`assert (Fraction(2117, 1500) * 24) == (Fraction(2117, 1500) * 20)`); reverted with `git checkout`.

## Checks (revision 2ab413b27, code unchanged since)

- Focused: `simulator/tests/world/test_mini_grid_v9.py` 10 passed in 50.9 s.
- Reach set (pre-flight §4, DD3b, once, `--db-lane`): 28 files of the pre-flight's DD3b list (every one present) plus the v9 file: **414 passed, 0 failed**, 1 warning, 182 s of test time (7 min 50 s wall time with the lane queue). No main rerun needed: nothing failed. `.agent/main-baseline/23d2cd9f6.md` lists DD3c's backend files, not these.
- `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON=main venv): passed. `tools/checks/statement_catalogue.py`:
  exit 0. `check-agent-workflow.ps1`: passed. `check-decision-index.py`: OK.

## DD3b1 fix round (D-DD.145) and DD3b2 part 1 (D-DD.128)

- Tests added to `test_mini_grid_v9.py`: P is never negative (min 0, max > 0 on Kobo 1-2 Oct with two sets) and a
  fuel-limited two-set segment never burns more than the tank (tank 0.3 L, runs dry, never below 0). Both pass on
  the built pack (the behaviour was DD3b1's), so each was proven by a plant (3, 4 below). Requested-power floor and
  litres cap were already in the code; the pack is unchanged.
- Kit (D-DD.128) in Lakeside's `/2` file; `pv-array-share` (+ basis) registered as a Foundation property (unit %,
  INVERTER, words and statement cases). `test_dd3b2_units.py` 3 tests, failed 3/3 on the old file first.
- Plants: 3. `max(0, ...)` removed from `view_v9`: the floor test FAILED (`assert Fraction(-32193, 1000) == 0`).
  4. The scaling of litres to the tank removed: the fuel test FAILED (`INTEGRATION_BOUND_FAILURE ... take the stock to
  -37/300 against a LOWER bound of 0`). Both reverted with `git checkout`.
- Checks at f16d759a8: `test_mini_grid_v9.py -k never` 2 passed; `test_dd3b2_units.py`, `test_dd1_operator_files.py`,
  `test_sc1_statements.py` 414 passed; `test_dd3_telemetry.py`, `test_dd3_site_inputs_cli.py`,
  `test_dd3_datasheet_check.py`, `test_dd1_check.py` 34 passed after the F re-pin. Architecture guard passed;
  statement catalogue exit 0. No Postgres run yet (DD3b2 incomplete; one `--db-lane` run at its end).

## Moved figures

No world figure yet. Pins moved: Lakeside's F digest `4e36563d...` -> `25345568...` (tank ratings and the kit enter
the foundation; D-DD.93 re-pin). DD3b1 changes no writer input and no world figure: Kobo's fuel, candidate and bridge are DD3b2/DD3b3's
(D-DD.97, D-DD.104, D-DD.131).

## Known Deviations

1. **Unit events are not POINT forcings in the kernel's terms (D-DD.127 says POINT, indexed by step, D-DD.75).**
   The kernel gives a POINT forcing a zero-length span: `_forcing_index` skips it (`end <= start`,
   `kernel/execute.py:288`) and no step context, nor phase A's `due` context (`exposures=()`), ever carries it. So a
   pack cannot read a POINT forcing, and the scope (pack and tests only) excludes a kernel change. Builder default:
   v9 reads the events from the step's exposures in `commit` (phase F), applied at the step's start, so the writer
   declares each as a WINDOW of one minute at the instant, which reaches exactly the step that holds it (the same
   step `point-applied-once` names). Consequences: the sample and view at the failing step's start still show the
   unit as it was; the controller reacts from the next step. **Question for the Architect:** keep this, or make the
   kernel expose POINT forcings at `point_due_at` (a kernel change and version move, outside DD3b's units)? If the
   kernel later exposes them, `_unit_events` reads them unchanged.
2. P (the requested generator power selecting the running set) is not defined numerically in §4.3 ("v8's rule");
   builder default: the demand plus the battery's acceptance at T (taper and headroom) less available solar. v8
   never needed it (one set runs whole).
3. A fuel-limited multi-unit segment caps each unit on its rating share of the tank; when the no-load burn exceeds
   the tank, the litres are scaled to the tank (v8's single-unit rule, lifted). Not reached by any Site's run.
4. A restored generator returns to STOPPED and can be asked to start from the next step.

5. **`/1` file unchanged (D-DD.128 says `/2` and `/1`).** `lakeside-power.v1.onboarding.json` carries no properties
   for any Site (format 1 has ratings only) and the writer SKIPs `/1`; adding the kit there would invent a shape.
   Question for the Architect: confirm `/2` alone.
6. **D-DD.146 applied to the plan**: C-DD6's Kisiwa (state evidence) and Mto (power evidence) clauses go live in
   DD3b2's step 8 (handoff); not yet built.

## Next

DD3b2: writer units (`supported()`, `NEEDS` `per_unit`, v8/v9 by Site, `UNIT_EVENTS` table with `M` parity, the
kit and tank ratings, sun calendar, hidden defaults, D-DD.97 shape, D-DD.104 warm-up), the pure runs, C-DD21.
