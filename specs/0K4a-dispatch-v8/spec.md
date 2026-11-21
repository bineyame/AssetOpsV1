# 0K4a: `mini-grid` v8, the generator takes the load (implementer spec)

Status: in_review (implementer, 2026-11-21; packet `packet.md`), rev 2 (Architect, Claude, 2026-11-21): handshake answered (D-0K4.19, D-0K4.20, D-0K4.22, D-0K4.25),
build-ready. **2.5 units.**
Discovery review (W5): a new mechanism in the simulator's dispatch, whose litres feed a money figure. Non-screen. No
migration. No database. `USER_REVIEW_REQUIRED: false` (v8's profile words reach only the simulator lab's run setup). Rulings: `specs/0K4-dispatch-model-review/
rulings.md` (D-0K4.2, D-0K4.3, D-0K4.4; the fuel and taper laws D-0K4.5, D-0K4.6 come from 0K4b; handshake answers
D-0K4.19, D-0K4.20, D-0K4.22). Reviewer guide: `reviewer-guide.md`. Questions: `handshake.md`, `handshake-I.md`.

**Rev 2 (handshake).** `kobo_draft` gains v8 (fixture edit). `cycle_charge_split` raises no `ValueError` and notes
below minimum only when the `D + C` cap binds (S10). N3 and N5 assert only what the rule guarantees. A reverse
view/segment mismatch keeps v7's rule with its note (N13). One trajectory digest helper pins v7 (N9) and v8 (N12).
N11 uses the port's real request. v8's backend words are SC-1 statements behind 0K4b's `served_text` seam (§2.7).

- **What it is.** A new model version, `mini-grid` v8: v7 with the generator carrying the load and charging the
  battery while it runs (cycle charging), the battery helping only above what PV and the generator can give, the
  generator held at its minimum load by charging first and then curtailing PV, and 0K4b's fuel curve and charge taper
  wired in. v1-v7 do not change.
- **Why next.** Review §3 row 3: "the battery serves load ahead of a running generator" causes 15 of the 16 failed
  dawns and is the fault an operator's engineer sees at once. Critical path, lane 1, first (D-0K4.1).
- **Builds on (`main`, `fa13f254f`):** `simulator/assetops_simulator/packs/mini_grid.py` (whole file; `decide` 503-611,
  `resolve` 631-910, `resolve_v2` 964-1007, `resolve_v3` 1041-1073, `resolve_v4` 1100-1124, `decide_v5` 1159-1196,
  `resolve_v6` 1221-1241, `MINI_GRID_V7_MODEL` 1289-1298); 0K4b's `packs/generator_curve.py` and
  `runs/profiles.py:GENERATOR_CURVE_NEEDS` (merged before commit 3); `backend/assetops_backend/runs/profiles.py:1375-
  1400, 2195-2207` (`MINI_GRID_V7_MODEL`, `MODEL_PROFILES`); `host/execution_adapter.py:113-140`
  (`EXECUTABLE_MODELS`); `host/forward_replay.py:56` (`REPLAY_MODELS`); `host/tests/kobo_season.py` (`base_run`,
  `season_inputs`, `season_site`); `host/tests/kobo_assumed.py` (0K4b).

## 0. Before you start

- **Start** when the shared handshake has no open question. Branch `task/0K4a-dispatch-v8` off `main`; worktree
  `/opt/assetecon/AssetOpsV1-0k4a`; symlink `frontend/node_modules`. Commits 1 and 2 need only `main`; before commit
  3, merge `main` with 0K4b on it.
- **Pre-flight print (packet, first section):** on `main` plus only commit 1's new `host/tests/trajectory_digest.py`
  (no product edit yet), `trajectory_digest` of the v7 8-day Kobo season site run (`base_run(8)` with the default
  `site_edit=season_site`, `season_inputs(run, 8)`, `execute(...)`), kept as N9's literal (D-0K4.20); the
  same run's 05:00 local SOC and generator state on day 4 (the dawn after the first overcast day: expect below 35 with
  the generator RUNNING, D-0K2.17); and the names of the battery AC, PV AC, generator output and load measurement
  addresses on the Kobo template (`battery-ac-power@battery-pcs` and so on, as `daytime` constants spell them).
- **Files.** Edited: `simulator/assetops_simulator/packs/mini_grid.py` (the extraction of §2.1 and the new v8 section
  after line 1298), `backend/assetops_backend/runs/profiles.py` (`MINI_GRID_V8_MODEL` and its row in
  `MODEL_PROFILES`), `host/execution_adapter.py` (import and `EXECUTABLE_MODELS` row), `host/forward_replay.py`
  (`REPLAY_MODELS` gains `("mini-grid", 8)`, its comment citing N11), `host/tests/kobo.py` (fixture edit: the
  backend `MINI_GRID_V8_MODEL` appended to `kobo_draft`'s profile tuple at lines 131-141; v7 callers unchanged),
  `backend/assetops_backend/simulator_lab_api.py` (the seam, §2.7), `backend/assetops_backend/i18n/statements/en/
  model_profile.py` and `backend/tests/statement_cases/model_profile.py` (two statements and their cases, §2.7). New:
  `simulator/tests/test_cycle_charge_split.py`, `host/tests/trajectory_digest.py`, `host/tests/test_0k4a_dispatch_v8.py`,
  `backend/tests/test_0k4a_profile_words.py`. No entry in either statement baseline or the allow file. Nothing under `config/`, `contracts/`, `backend/assetops_backend/runs/
  replay_study.py` or any guard.
- **Heavy tools** through the slot pool: host tests by `pwsh -NoProfile -File tools/run-host-tests.ps1 --
  host/tests/test_0k4a_dispatch_v8.py`; `pytest simulator/tests` whole. No database; never ports 5490 or 8990.

## 1. Outcome and gate questions

On a night after an overcast day, does the generator start at the effective start charge and does the battery's
charge then rise on every running step until the stop? Does the battery discharge beside a running generator only
when the load is above what PV and the generator can give, and then exactly by the shortfall within its limits? Is a
running generator held at or above its minimum load by charging and then curtailing PV, and below it only when nothing
more can be absorbed? Are the start and stop rules v5's, and is a day on which the generator never runs identical to
v7 when there is no taper? Does the tank fall by exactly the fuel curve, with the kernel's balance checks whole? Are
v1-v7 trajectories and digests unchanged, and can the replay port replay a v8 run?

## 2. Design

### 2.1 A behaviour-neutral extraction (commit 1)

The measurement additions of v2, v3, v4 and v6 move into four private functions, each taking `(context, accepted)` and
returning the `replace(...)` that version's resolver makes today: `_add_v2_measures`, `_add_v3_measures`,
`_add_v4_measures`, `_add_v6_measures`. `resolve_v2` becomes `_add_v2_measures(context, resolve(context, intent))`,
`resolve_v3` `_add_v3_measures(context, resolve_v2(context, intent))`, and so on. No arithmetic, ordering or string
changes; N9 proves it. `resolve_v6` keeps its `intent` argument for the charge request, so `_add_v6_measures` takes
`(context, intent, accepted)`.

### 2.2 The split (pure, commit 1; `mini_grid.py`)

```python
@dataclass(frozen=True)
class CycleSplit:
    pv_to_load: Fraction; pv_to_battery: Fraction; curtailed_pv: Fraction
    generator_to_load: Fraction; generator_to_battery: Fraction
    battery_to_load: Fraction; unserved: Fraction
    below_minimum: bool                     # D + C < M and D + C < R: nothing more to absorb

def cycle_charge_split(demand: Fraction, pv_available: Fraction, generator_kw: Fraction, charge_kw: Fraction,
                       minimum_kw: Fraction, discharge_kw: Fraction) -> CycleSplit:
    """D-0K4.3 for one segment of a RUNNING generator, all in kW. generator_kw is the usable rating (fuel-capped),
    charge_kw the acceptance C, discharge_kw v7's discharge cap (0 at or below the reserve)."""
    D, A, R, C, M = demand, pv_available, generator_kw, charge_kw, minimum_kw
    if D > A + R:                                            # 1. generator support
        battery = min(D - A - R, discharge_kw)
        return CycleSplit(A, 0, 0, R, 0, battery, D - A - R - battery, False)
    g = min(R, max(M, D + C - A), D + C)                     # 2. cycle charging
    u = max(Fraction(0), min(A, D + C - g))
    pv_load = min(u, D)
    return CycleSplit(pv_load, u - pv_load, A - u, D - pv_load, g - (D - pv_load), 0, 0, D + C < M and D + C < R)
```

Every argument a non-negative `Fraction` (a `float` or a negative value is `ValueError`/`TypeError`, S9). `M > R` is
legal (`g` is capped by `R`; D-0K4.22) and raises nothing. The flag is true only when the `D + C` cap binds below the
minimum, so a fuel cap (`R < M`) or step 5's rerun with `generator_kw = 0` never notes "below minimum load".

### 2.3 v8's controller (`decide_v8`, commit 2)

`decide_v8(view)`: when `generator-state` is RUNNING, rewrite the view's `source-priority-rank` entries so the
generator ranks immediately before the battery when the Site's order puts it after (PV keeps its place), then call
`decide_v5` on that view; otherwise call `decide_v5` on the view unchanged. When the rewrite happened, append
`" (v8 cycle charging: a running generator is ahead of the battery)"` to the battery request's reason. The generator
run decision is therefore v5's exactly, and v5's battery request now asks to discharge only `demand - pv - rating`
and otherwise to charge from everything beyond demand.

### 2.4 v8's resolver (`resolve_v8`, commit 3)

`_resolve_cycle(context, intent)` is `resolve` (631-910) with exactly these changes; everything not named is v7's
line for line:
1. **Plant reads.** `curve = generator_curve.fuel_curve(gen.sfc, no_load, gen.rated)` with `no_load = daytime._one(
   context, NO_LOAD_FUEL_RATE, "generator")[1]` (L/min), `minimum_kw = gen.rated x daytime._one(context, MINIMUM_LOAD,
   "generator")[1] / 100`, `taper = daytime._one(context, TAPER_START, "battery")[1]`.
2. **Charge cap** (every state): `charge_cap = min(-requested, charge_acceptance_kw(soc_at_segment_start,
   plant.charge_limit, taper), by_energy)`, where `soc_at_segment_start = stored x 100 / capacity`; when the taper
   binds, `limited` gains `"charge taper above {taper} %"`.
3. **Generator cap** (RUNNING): `by_fuel = output_cap_kw(curve, fuel, minutes)`; `generator_cap = gen.rated` if
   `by_fuel is None` else `min(gen.rated, by_fuel)`; the fuel note as v7's when `by_fuel < gen.rated`.
4. **Allocation.** STOPPED, STARTING, FAILED: v7's allocation-and-charging block (`mini_grid.py:705-731` on `main`)
   unchanged (taper through the charge cap).
   RUNNING: `s = cycle_charge_split(demand, available, generator_cap, charge_cap if requested < 0 else Fraction(0),
   minimum_kw, discharge_cap if requested > 0 else Fraction(0))`; `to_load`, `to_battery` and `curtailed` from `s`;
   served is `demand - s.unserved`, shared over loads in v7's order (the loads loop, `:715-720`); `s.below_minimum` adds
   `"below minimum load: nothing more to absorb"` to `generator_limited`.
   When `requested > 0` while RUNNING but `demand <= available + generator_cap` (the view at T saw a support case the
   segment does not have), the split's branch 2 governs; `limited` gains v7's existing "differed from the view" note.
   The reverse (D-0K4.22, R6): when the view asked for charge (`requested <= 0`) but a segment has `D > A + R` (a load
   window starting inside the step), the split's branch 1 runs with `discharge_kw = 0` (v7's view-bound rule, kept),
   so `D - A - R` is unserved; `limited` gains the same "differed from the view at T" note (text as `:849-851`).
5. **Fuel.** `burned = fuel_litres(curve, state.value, Fraction(end - start), generator_energy)`; if `burned > fuel`,
   `burned = fuel` and `generator_limited` gains `"fuel in tank ({fuel} L) below the no-load burn"` (the generator
   delivers 0 that segment: rerun the split with `generator_kw = 0`).
6. **New flows and balance.** `fuel_energy` (tank to `gen.generator`) = `burned x DIESEL_ENERGY_KWH_PER_L`;
   `generator_conversion_loss` (`gen.generator` to `"losses"`) = `fuel_energy - generator_output`; balance
   `BalanceIdentity("generator-fuel", ("fuel_energy",), ("generator_output", "generator_conversion_loss"))`.
7. **Fuel stock account.** `StockAccount(gen.fuel_address, fuel - fuel_at_start, DIESEL_ENERGY_KWH_PER_L, (),
   ("fuel_energy",))`.
8. **Notes.** `(CURVE_FUEL_NOTE,)` alone, replacing `LINEAR_FUEL_NOTE` (`:909`), never beside it; v7's "RUNNING with
   nothing to absorb" note stays where v7 sets it (`:852-853`); with `CURVE_FUEL_NOTE = "fuel follows the generator's declared curve: the no-load
   rate over every starting or running minute plus the slope to the full-load consumption over accepted energy"`.

`resolve_v8(context, intent) = _add_v6_measures(context, intent, _add_v4_measures(context, _add_v3_measures(context,
_add_v2_measures(context, _resolve_cycle(context, intent)))))`. `prepare_v8(context)` = `prepare(context)` then the
three plant reads of step 1, mapping `CurveRefused(code, detail)` to `CouplingRefused("PHYSICAL_RESOLUTION_FAILURE",
f"{NO_LOAD_FUEL_RATE}@{gen.generator}", f"{code}: {detail}")`.

### 2.5 The version (commit 3)

```python
FUEL_TANK_STOCK_V8 = replace(FUEL_TANK_STOCK_V7, statement=(
    "The fuel in the tank, initialized by the scenario, moved by the generator's fuel curve while it starts or runs "
    "and by any frozen declared cause, such as a recorded operational action."))
V8_SENTENCE = (" Version eight runs the generator as a cycle charger: while it runs it carries the load and charges "
    "the battery, the battery helps only above what solar and the generator give, the generator is held at its "
    "minimum load by charging and then by curtailing solar, fuel follows its declared curve, and charging tapers "
    "near full.")
MINI_GRID_V8_COUPLING = replace(MINI_GRID_V6_COUPLING, prepare=prepare_v8, decide=decide_v8, resolve=resolve_v8)
MINI_GRID_V8_MODEL = replace(MINI_GRID_V7_MODEL, model_profile_version=8,
    statement=MINI_GRID_V7_MODEL.statement + V8_SENTENCE,
    handlers=tuple(FUEL_TANK_STOCK_V8 if h.handler_id == FUEL_TANK_STOCK_V8.handler_id else h
                   for h in MINI_GRID_V7_MODEL.handlers) + generator_curve.CURVE_HANDLERS,
    component_relations=<v7's, with the "generator" relation's state_keys gaining NO_LOAD_FUEL_RATE and MINIMUM_LOAD,
                         and the battery relation (the one holding the battery's energy capacity key) gaining TAPER_START>,
    coupling=MINI_GRID_V8_COUPLING)
```

The simulator's `V8_SENTENCE` and `FUEL_TANK_STOCK_V8` statement stay `str` (the SC-1 scan does not read `simulator/`,
D-0K4.19 item 6). Backend: `MINI_GRID_V8_MODEL = replace(MINI_GRID_V7_MODEL, model_profile_version=8,
statement=message("model_profile.description", profile=State("MINI_GRID_V8")), supported_states=<v7's, the
fuel-tank-volume state's statement replaced by message("model_profile.state", state=State("FUEL_TANK_VOLUME_CURVE"))>
+ GENERATOR_CURVE_NEEDS, foundation_needs=MINI_GRID_V7_MODEL.foundation_needs + ("generator-no-load-fuel-rate",
"generator-minimum-load", "battery-charge-taper-start"))`, appended to `MODEL_PROFILES` after v7. Host:
`EXECUTABLE_MODELS` gains the simulator's `MINI_GRID_V8_MODEL`; `REPLAY_MODELS` gains `("mini-grid", 8)`. The kernel's
profile pairing (`ProfilePairMismatch`) must accept the pair; if it refuses, that is a mid-build question.

### 2.6 Fixtures (`host/tests/test_0k4a_dispatch_v8.py`)

`site = lambda d: (season_site(d), assumed_site(d))`; `run8(days) = base_run(days, version=8, site_edit=site)`;
`run7(days) = base_run(days, version=7, site_edit=site)` (v7 ignores the extra properties). Inputs from
`season_inputs(run, days, overcast=...)`; a start SOC other than 48 by `dataclasses.replace` of the
`battery-state-of-charge@battery` initial value; extra load windows by appended `ForcingInput`s copied from the run's
first forcing at that address (the `season_inputs` pattern). The test's reader is its own (W2): SOC `B[i].stock`,
energies `B[i+1].interval_measurement`, state `B[i].discrete_state_for_step`, all exact.

### 2.7 The words, through SC-1 (commit 3; D-0K4.19)

`i18n/statements/en/model_profile.py` (0K4b's file) gains:

```python
    "model_profile.description": {
        "slots": {"profile": {"type": "state", "values": ["MINI_GRID_V8"]}},
        "variants": [
            {"id": "cycle_charging", "when": {"is": ["profile", "MINI_GRID_V8"]},
             "text": "As the previous mini-grid version, except that the generator runs as a cycle charger: while it "
                     "runs it carries the load and charges the battery, the battery helps only above what solar and "
                     "the generator give, the generator is held at its minimum load by charging and then by "
                     "curtailing solar, fuel follows its declared curve, and charging tapers near full."},
        ],
        "exhaustive": "profile",
        "rephrase": "never",
    },
    "model_profile.state": {
        "slots": {"state": {"type": "state", "values": ["FUEL_TANK_VOLUME_CURVE"]}},
        "variants": [
            {"id": "fuel_tank_volume_curve", "when": {"is": ["state", "FUEL_TANK_VOLUME_CURVE"]},
             "text": "The fuel in the tank, initialized by the scenario, moved by the generator's fuel curve while it "
                     "starts or runs and by any frozen declared cause, such as a recorded operational action."},
        ],
        "exhaustive": "state",
        "rephrase": "never",
    },
```

v8's backend statement no longer repeats v7's text: it says what changed from the previous version, which the lab lists
beside it (a variant id holds no digit; the catalogue refuses one). `statement_cases/model_profile.py` gains one case per
variant with these two texts. `ModelProfile.statement: str | Message`. `simulator_lab_api.run_profile_summary`
(`:880`, `:889`): `"statement": served_text(profile.statement)` and `"statement": served_text(state.statement)`; no
other read changes. Both literals were loaded and rendered in a scratch copy of `i18n` (D-0K4.19).

## 3. Tests (written first)

`simulator/tests/test_cycle_charge_split.py` (pure, literal expected values, kW):

| Case | D, A, R, C, M, dis | pv load, pv bat, curt | gen load, gen bat | bat load, unserved | below min |
|---|---|---|---|---|---|
| S1 support | 75, 0, 40, 30, 12, 30 | 0, 0, 0 | 40, 0 | 30, 5 | no |
| S2 night charge | 13, 0, 40, 30, 12, 0 | 0, 0, 0 | 13, 27 | 0, 0 | no |
| S3 with PV | 20, 15, 40, 30, 12, 0 | 15, 0, 0 | 5, 30 | 0, 0 | no |
| S4 minimum load, curtail | 15, 50, 40, 30, 12, 0 | 15, 18, 17 | 0, 12 | 0, 0 | no |
| S5 nothing to absorb | 5, 50, 40, 2, 12, 0 | 0, 0, 50 | 5, 2 | 0, 0 | yes |
| S6 fuel-capped | 13, 0, 10, 30, 12, 30 | 0, 0, 0 | 10, 0 | 3, 0 | no |
| S7 at the boundary | 40, 0, 40, 30, 12, 30 | 0, 0, 0 | 40, 0 | 0, 0 | no |
| S10 no rating, M > R | 5, 15, 0, 2, 12, 0 | 5, 2, 8 | 0, 0 | 0, 0 | no |

- **S8 invariants** over every combination of D in {0, 5, 13, 40, 75}, A in {0, 15, 50}, R in {0, 10, 40},
  C in {0, 2, 30}, M in {0, 12}, dis in {0, 30} (every combination, `M > R` included): every field non-negative;
  `pv_to_load + pv_to_battery + curtailed == A`; `pv_to_battery + generator_to_battery <= C`; `battery_to_load > 0`
  only if `D > A + R`; `pv_to_load + generator_to_load + battery_to_load + unserved == D`; `below_minimum` only if
  `D + C < M` and `D + C < R`.
- **S9** a `float` argument or a negative one raises.

`host/tests/test_0k4a_dispatch_v8.py` (the kernel; about a minute; `functools.cache` on each run):
- **N1 started at 35 %, the charge rises.** `run8(2)`, overcast day 0: the first STOPPED to STARTING step of night 1 has
  SOC at or below 35; it is STARTING for exactly one step; on every following RUNNING step until the stop, SOC at the
  next boundary is above SOC at this one, unless it is 100.
- **N2 no discharge beside the generator.** On every RUNNING step of N1's run with demand at most PV available plus 40
  kW (the reader's own sums), the battery AC energy is at most 0 (charging or idle).
- **N3 dawn after an overcast day** (D-0K4.22, R3). On N1's inputs: (a) precondition, v7's 05:00 local SOC of day 1
  is below 35 (the fault is reproduced on v7); (b) with `s0` v8's SOC at the boundary that ends night 1's STARTING
  step, every boundary from there to 05:00 has SOC at least `s0`; (c) v8's 05:00 SOC is above v7's.
- **N4 generator support.** `run8(1)`, start SOC 34, loads res 25, clinic 10, mill 40 kW over 01:00-01:30 local (offsets
  60 to 90; each season window at the three load addresses that overlaps `[60, 90)` is cut into its parts before 60 and
  after 90 at its own value, and one window `[60, 90)` per load is added, so no two windows force one address): on each of those six RUNNING steps, generator energy `10/3` kWh, battery AC `+5/2` kWh (PCS-limited), and
  unserved `5/12` kWh; precondition: SOC above 30 at 01:30.
- **N5 minimum load.** `run8(2)`, overcast day 0, `site_stop_pct=Fraction(100)`: on every RUNNING step, generator energy
  is at least `1` kWh (12 kW for 5 minutes) unless that step's generator note says "below minimum load"; with the
  reader's own `C = min(A + 40 - D, 30 x f(soc), (200 - stored) / (95/100 x 5/60))`, `f(soc) = 1` at or below 95 and
  `max(1/20, (100 - soc) / 5)` above it (D-0K4.22, R4), on every RUNNING step where `D + C - A < 12 <= D + C`,
  generator energy is exactly `1` kWh and PV AC energy is below PV available (curtailment).
  Precondition: at least one such step exists; if none, that is a mid-build question (the fixture is not tuned).
- **N6 stopped days are v7's.** `run8(1)` and `run7(1)`, start SOC 80 (no start), taper start overridden to 100: PV AC,
  battery AC, every load served and SOC equal at every step, and the tank does not move in either.
- **N6b taper on solar charging.** `run8(1)`, start SOC 80, clear day, taper 95 (no start): on every step whose SOC at
  its start is above 95 and whose battery AC is negative (charging), the charge drawn is at most the reader's own
  `30 x max(1/20, (100 - soc) / 5) x 5/60` kWh, and equal to it on at least one step (precondition: SOC passes 95).
- **N7 start and stop rules.** In N1's and N5's runs, every STOPPED to STARTING step has SOC at or below
  `min(35, reserve + 5)`, and every RUNNING to STOPPED step follows at least 30 minutes RUNNING with SOC at or above
  the stop in effect.
- **N8 the tank follows the curve.** In N1's run, the tank's total fall equals the reader's
  `sum(33/600 x 5 for each STARTING or RUNNING step) + 2175/10000 x sum(generator kWh)` exactly, and the run is
  COMPLETED (no balance violation); every step's resolution notes include `CURVE_FUEL_NOTE` and never
  `LINEAR_FUEL_NOTE` (D-0K4.22, I6).
- **N9 v1-v7 untouched.** `trajectory_digest` of the v7 8-day season run (`site_edit=season_site`) equals the
  pre-flight literal; every existing host and simulator
  test passes unchanged (the extraction of §2.1 changes nothing).
- **N10 refusals.** A v8 run whose Foundation has no `generator-no-load-fuel-rate` is refused at run creation naming
  the missing Foundation need; one with `specific-fuel-consumption` 0.09 is refused with `PHYSICAL_RESOLUTION_FAILURE`
  at `generator-no-load-fuel-rate@generator`, detail starting `SFC_BELOW_DIESEL_ENERGY`.
- **N11 the replay port takes v8** (D-0K4.22, I4). `observed = kobo_season.observed_series(<N1's trajectory>, 576)`;
  `HostForwardReplay().forward_replay(run8(2), ForwardReplayRequest(BASELINE, observed.pv_available_kw,
  observed.loads, start_state(observed), ...))`, built as `runs/replay_study.py:516` builds it: not refused, 576
  steps, `generator_kwh` within 1 % of the site run's (a smoke check; calibration is 0K4d's). v8 is not added to T1.
- **N12 v8 pinned** (D-0K4.20). `trajectory_digest` of `base_run(8, version=8, site_edit=site)` on `season_inputs(run,
  8)` equals a literal printed in the packet; docstring "a change here is a new model version, never an edit".
- **N13 the reverse mismatch** (D-0K4.22, R6). `run8(1)`, start SOC 34, res 25 and clinic 10 kW all night and the mill
  40 kW over offsets `[62, 90)` (windows cut as N4 cuts them): on the step `[60, 65)`, unserved energy is exactly
  `7/4` kWh (`35 x 3/60`), battery AC energy at most 0, and the step's `limited` notes hold the "differed from the
  view at T" text; on each step of `[65, 90)`, N4's per-step figures hold.

`backend/tests/test_0k4a_profile_words.py` (no database): **W1** `run_profile_summary(MINI_GRID_V8_MODEL)` serves the
`cycle_charging` text as `statement`, the `fuel_tank_volume_curve` text on the fuel-tank state and 0K4b's three need
sentences, each a `str`; **W2** every other profile's summary is byte-equal to `main`'s (the seam passes legacy `str`
unchanged).

**Regression:** `pytest simulator/tests` (whole), `host/tests/test_0k1_forward_replay.py`, `host/tests/
test_0k2_kobo_season.py`, `host/tests/test_registered_kobo_execution.py`, the profile-pairing tests that list
`MODEL_PROFILES`, check-all (fast) once, `python tools/select-tests.py --base main`.

## 4. Units

| Commit | Content |
|---|---|
| 1 (1.0) | §2.1 extraction, §2.2 split; `host/tests/trajectory_digest.py`; S1-S10; N9 |
| 2 (0.5) | §2.3 `decide_v8` with its own pure test (a RUNNING view with order PV, battery, generator gives the support or charge request of v5 on order PV, generator, battery) |
| 3 (1.0) | after 0K4b on `main`: §2.4, §2.5, §2.7, the backend, host and `kobo.py` rows; N1-N8, N10-N13, W1-W2; regression; packet |

Packet `specs/0K4a-dispatch-v8/packet.md`: the pre-flight print; for N1's night, a per-step table (time, state, SOC,
generator kWh, battery AC, PV curtailed) from STARTING to STOPPED; N3's two dawn readings (v7 and v8, both SIMULATED,
as a model-change reconciliation, D-0K4.11); N5's curtailment steps; the fuel identity of N8; the regression output;
the mid-build count.

## 5. Done (questions; each can fail)

1. Does the charge rise on every running step after a night start, and is there no discharge beside the generator
   unless the load exceeds PV plus the rating?
2. Is generator support exact (shortfall within PCS and reserve limits, the rest unserved)?
3. Is the minimum load held by charging then curtailing, and broken only when nothing more can be absorbed?
4. Are the start and stop rules v5's, and is a no-start day equal to v7's without taper?
5. Does the tank fall by exactly the curve, with every kernel balance whole?
6. Are v1-v7 unchanged (digest and every existing test), is v8's own digest pinned, and does the replay port run v8?
6b. Are v8's backend words SC-1 statements served through `served_text`, with no baseline or allow entry added?
7. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 6. Out of scope

Load following, high-load starts, quiet hours, night charging to a lower stop (queue Q2-Q4); editing the Kobo template
or moving any world to v8 (0K4f, D-0K4.13); the season (0K4c); figures and admission (0K4d); any screen; migrating the legacy profile
statements to SC-1 (queue Q9).
