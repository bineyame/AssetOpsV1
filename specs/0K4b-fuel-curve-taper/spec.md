# 0K4b: the generator's fuel curve and the battery's charge taper (implementer spec)

Status: live, rev 1 (Architect, Claude, 2026-11-21); handshake next, shared with 0K4a (D-0K4.17). **1.5 units.**
Discovery review (W5): a new physical law whose litres feed a money figure. Non-screen. No migration. No database.
`USER_REVIEW_REQUIRED: false` (nothing served). Rulings: `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.5,
D-0K4.6, D-0K4.7; the family rulings D-0K4.1 to D-0K4.18). Reviewer guide: `reviewer-guide.md`.

- **What it is.** The two physical laws `mini-grid` v8 needs, written once as a pure module, plus the three Foundation
  properties they read and the assumed Kobo values as a test fixture. No model version is made here: 0K4a assembles v8
  from this module (D-0K4.2), so nothing on `main` runs these laws until 0K4a merges.
- **Why next.** Review §3 rows 4-6: fuel with no idle burn, no part-load penalty and no taper all understate a lower
  stop setting. Lane 2, first (D-0K4.1); 0K4a's commit 3 waits for this merge.
- **Builds on (`main`, `fa13f254f`):** `simulator/assetops_simulator/packs/minigrid.py` (`_coefficient`,
  `_percentage`, `PhysicallyUnacceptable` via `packs/fuel.py`), `packs/mini_grid.py` (`_positive`, for the pattern),
  `contracts/assetops_contracts/execution_contract.py:465-479` (`CANONICAL_UNITS`: `L/h` freezes as `VOLUME_RATE` in
  `L/min`, value / 60), `backend/assetops_backend/sites/models.py:262-352` (the property catalogue), `backend/
  assetops_backend/runs/profiles.py:1140-1230` (`_need`), `host/tests/kobo.py` (`component`), `tools/demo_combined_kobo.py:
  138-145` (the owner's 3.3 L/h, `GENERIC_DEFAULT`).

## 0. Before you start

- **Start** when the shared 0K4a/0K4b handshake has no open question. Branch `task/0K4b-fuel-curve` off `main`;
  worktree `/opt/assetecon/AssetOpsV1-0k4b`; symlink `frontend/node_modules` from the main checkout.
- **Pre-flight print (packet, first section):** the frozen value and canonical unit that a Kobo draft run
  (`kobo_draft("kobo-mini-grid-prolonged", timestep_minutes=5, model_profile="mini-grid", model_profile_version=7,
  site_edit=assumed_site)`) carries for `generator-no-load-fuel-rate`, if any (v7 does not need it, so expect none;
  say so); and that `assumed_site` leaves every v7 Kobo digest test green (`host/tests/test_registered_kobo_execution.py`).
- **Files.** New: `simulator/assetops_simulator/packs/generator_curve.py`, `simulator/tests/test_generator_curve.py`,
  `host/tests/kobo_assumed.py`, `backend/tests/test_0k4b_properties.py`. Edited: `backend/assetops_backend/sites/
  models.py` (catalogue rows only, §2.3), `backend/assetops_backend/runs/profiles.py` (one new tuple, §2.4, used by no
  profile yet). Nothing under `config/`, `contracts/`, `host/forward_replay.py`, `packs/mini_grid.py` or any guard.
- **Heavy tools** through the slot pool (`tools/heavy-slot.sh -- ...`). Simulator tests run whole (T2 rule:
  `pytest simulator/tests`, never `-k`). No database; never ports 5490 or 8990.
- **No user-facing text.** Property display names are catalogue data (§2.3), not served sentences.

## 1. Outcome and gate questions

Does the fuel law give the declared no-load rate at no load, `SFC x rating` an hour at full load and the straight line
between, with STARTING burning the no-load rate and STOPPED and FAILED nothing? Does a frozen `L/h` value arrive as
`L/min` and burn the right litres in a 5-minute step? Does charge acceptance stay at the PCS limit up to the taper
start and fall linearly above it to a floor of one twentieth, so that the last 10 points take longer than the 10 before
them? Are a curve below the energy content of diesel, a negative slope, a non-positive no-load rate and a taper start
outside (0, 100] refused? Does the Foundation accept the three new properties and their bases on the right
components, and refuse a basis outside the set?

## 2. Design

### 2.1 `simulator/assetops_simulator/packs/generator_curve.py` (pure; imports `fractions`, `packs.minigrid`, `packs.fuel` only)

```python
NO_LOAD_FUEL_RATE = "generator-no-load-fuel-rate"     # frozen in L/min (CANONICAL_UNITS "L/h" -> "L/min", /60)
MINIMUM_LOAD = "generator-minimum-load"               # % of the generator's rating
TAPER_START = "battery-charge-taper-start"            # % state of charge
DIESEL_ENERGY_KWH_PER_L = Fraction(10)                # declared model constant (diesel about 9.9-10 kWh/L)
MIN_SFC_L_PER_KWH = 1 / DIESEL_ENERGY_KWH_PER_L       # below this a generator would make energy from nothing
TAPER_FLOOR_SHARE = Fraction(1, 20)                   # acceptance never falls below 1/20 of the limit
HUNDRED = Fraction(100)
ON_STATES = frozenset({"STARTING", "RUNNING"})

@dataclass(frozen=True)
class FuelCurve:
    no_load_l_per_min: Fraction      # r / 60
    slope_l_per_kwh: Fraction        # s = sfc - 60 x no_load_l_per_min / rated

def fuel_curve(sfc_l_per_kwh: Fraction, no_load_l_per_min: Fraction, rated_kw: Fraction) -> FuelCurve
    # raises CurveRefused(code, detail): "NO_LOAD_NOT_POSITIVE" (r <= 0), "SFC_BELOW_DIESEL_ENERGY"
    # (sfc < MIN_SFC_L_PER_KWH), "NEGATIVE_SLOPE" (s < 0); checked in that order
def fuel_litres(curve: FuelCurve, state: str, minutes: Fraction, output_kwh: Fraction) -> Fraction
    # state in ON_STATES: curve.no_load_l_per_min * minutes + curve.slope_l_per_kwh * output_kwh; else 0
    # a STARTING step has output_kwh == 0 by the lifecycle; a non-zero output in STARTING is ValueError
def output_cap_kw(curve: FuelCurve, fuel_l: Fraction, minutes: Fraction) -> Fraction | None
    # the most kW the fuel allows over `minutes`: None when slope is 0 and fuel >= no-load burn (no fuel bound);
    # 0 when fuel < no_load_l_per_min * minutes; else (fuel - no_load_l_per_min * minutes) / (slope * minutes / 60)
def charge_acceptance_kw(soc_pct: Fraction, limit_kw: Fraction, taper_start_pct: Fraction) -> Fraction
    # soc <= taper start (or taper start == 100): limit; else limit * max(TAPER_FLOOR_SHARE,
    # (HUNDRED - soc) / (HUNDRED - taper_start)); soc above 100 is ValueError
class CurveRefused(Exception):
    def __init__(self, code: str, detail: str) -> None      # code in CURVE_REFUSALS, else ValueError
CURVE_REFUSALS = frozenset({"NO_LOAD_NOT_POSITIVE", "SFC_BELOW_DIESEL_ENERGY", "NEGATIVE_SLOPE"})
```

Every argument is a `Fraction` (a `float` or `int` is `TypeError` naming the argument), so the kernel's exact balance
checks stay exact. The module holds no state and reads no context: 0K4a's resolver calls it per segment.

### 2.2 State handlers (the same module)

```python
CURVE_HANDLERS: tuple[StateHandler, ...] = (
    daytime._coefficient(NO_LOAD_FUEL_RATE, "generator-no-load-fuel-rate-coefficient", "VOLUME_RATE",
                         _positive_rate, "Litres an hour the generator burns while STARTING or RUNNING at no output."),
    daytime._coefficient(MINIMUM_LOAD, "generator-minimum-load-coefficient", "FRACTION",
                         daytime._percentage("a minimum generator load"),
                         "Site policy: the least share of its rating a running generator is held at."),
    daytime._coefficient(TAPER_START, "battery-charge-taper-start-coefficient", "FRACTION",
                         _taper_start, "The state of charge above which the battery accepts less than its limit."),
)
CURVE_RELATIONS: tuple[ComponentRelation, ...]   # none new: 0K4a adds the two generator keys to the v8 "generator"
                                                 # relation and the taper key to the battery's (assembled there)
```

`_positive_rate` refuses `<= 0` with `PhysicallyUnacceptable` ("a no-load fuel rate of {v} L/min is not positive");
`_taper_start` refuses outside `(0, 100]` ("a taper start of {v} % is not a state of charge above 0 and at most 100").

### 2.3 Foundation catalogue (`backend/assetops_backend/sites/models.py`)

Add, after the FUEL-1 block, with a comment citing D-0K4.4 and D-0K4.6:

| Key | `unit` | `kind` | `display_name` | Carrier (`MINIGRID_PROPERTY_CARRIERS`) |
|---|---|---|---|---|
| `generator-minimum-load` | `%` | `CONTROL` | Generator minimum load | GENERATOR |
| `generator-minimum-load-basis` | `state` | `CONTROL` | Generator minimum load basis | GENERATOR |
| `battery-charge-taper-start` | `%` | `PHYSICAL` | Battery charge taper start | BATTERY |
| `battery-charge-taper-start-basis` | `state` | `PHYSICAL` | Battery charge taper start basis | BATTERY |

`STATE_PROPERTY_VALUES` gains both basis keys with `frozenset({"GENERIC_DEFAULT", "MANUFACTURER_DATASHEET",
"SITE_TEST"})`. `generator-no-load-fuel-rate` and its basis exist already (FUEL-1 A1) and are not touched.

### 2.4 Profile needs, not yet used (`backend/assetops_backend/runs/profiles.py`)

```python
#: 0K4b (D-0K4.4 to D-0K4.6): the three Foundation needs `mini-grid` v8 adds. 0K4a puts them on MINI_GRID_V8_MODEL.
GENERATOR_CURVE_NEEDS: tuple[SupportedState, ...] = (
    _need("generator-no-load-fuel-rate", "GENERATOR", "generator-no-load-fuel-rate", "L/h",
          "Litres an hour the generator burns while starting or running at no output."),
    _need("generator-minimum-load", "GENERATOR", "generator-minimum-load", "%",
          "Site policy: the least share of its rating a running generator is held at."),
    _need("battery-charge-taper-start", "BATTERY", "battery-charge-taper-start", "%",
          "The state of charge above which the battery accepts less than its charge limit."),
)
```

### 2.5 The assumed Kobo values (`host/tests/kobo_assumed.py`)

```python
ASSUMED_BASIS = "GENERIC_DEFAULT"
ASSUMED_PROPERTIES = {
    "generator": (("generator-no-load-fuel-rate", 3.3, "L/h"), ("generator-no-load-fuel-rate-basis", ASSUMED_BASIS, "state"),
                  ("generator-minimum-load", 30, "%"), ("generator-minimum-load-basis", ASSUMED_BASIS, "state")),
    "battery": (("battery-charge-taper-start", 95, "%"), ("battery-charge-taper-start-basis", ASSUMED_BASIS, "state")),
}
ASSUMPTION_NOTE = ("assumed until Kobo's sheets arrive: generic no-load fuel rate 3.3 L/h for a 40 kW set (owner value "
                   "2026-11-07), minimum load 30 % of rating, lithium iron phosphate battery tapering above 95 %")
def assumed_site(document) -> None
    # appends each row to component(document, id)["properties"] as {"property_key", "value", "unit",
    # "source": "SITE", "source_version": 1}; a key already present is KeyError (never overwritten silently)
```

`specific-fuel-consumption` stays the template's 0.3 L/kWh (read by the curve as the full-load consumption, D-0K4.5).

## 3. Tests (written first)

`simulator/tests/test_generator_curve.py` (pure, under a second):
- **F1 no load:** Kobo's curve (`sfc 3/10`, `r = 33/600` L/min, rated 40): RUNNING, 60 minutes, 0 kWh burns exactly
  `33/10` L.
- **F2 full load:** RUNNING, 60 minutes, 40 kWh burns `12` L (= 0.3 x 40), so the declared SFC holds at rating.
- **F3 part load:** 60 minutes at 10 kWh burns `33/10 + 2175/10000 x 10` = `5.475` L; at 20 kWh `7.65` L. The
  litres per kWh fall from quarter to half to full load (precondition asserted: strictly).
- **F4 states:** STARTING for 5 minutes burns `33/600 x 5` = `0.275` L; STOPPED and FAILED burn 0 at any output;
  STARTING with output above 0 raises `ValueError`.
- **F5 refusals, in order:** `r = 0` gives `NO_LOAD_NOT_POSITIVE`; `sfc = 9/100` gives `SFC_BELOW_DIESEL_ENERGY`;
  `sfc = 1/10, r = 5 L/h, rated 40` (slope `1/10 - 1/8 < 0`) gives `NEGATIVE_SLOPE`; `CurveRefused("NOPE", "")` raises
  `ValueError`.
- **F6 fuel cap:** 0.2 L over 5 minutes gives `0` kW (below the 0.275 L no-load burn); 1 L over 5 minutes gives
  `(1 - 0.275) / (0.2175 x 5/60)` kW exactly; slope 0 with ample fuel gives `None`.
- **F7 taper:** limit 30, start 95: SOC 95 gives 30; 97.5 gives 15; 99.9 gives `30 x 1/20` (the floor binds); start 100
  gives 30 at SOC 100; SOC 100.1 raises.
- **F8 the last band is slower:** integrate `charge_acceptance_kw` in 5-minute steps with SOC moving by
  `min(acceptance x 5/60 x 95/100 / 200 x 100, 100 - soc)` (Kobo's 200 kWh, 95 % efficiency) from 80 to 90 and from 90 to 100, start
  95: the second takes more steps than the first. With start 100 both take the same count within one step.
- **F9 exactness:** a `float` argument to each function raises `TypeError` naming it.
- **F10 handlers:** `CURVE_HANDLERS` state keys equal the three constants; each refuses its out-of-range value through
  `consume`.

`backend/tests/test_0k4b_properties.py` (no database, under a second):
- **P1** a Kobo template document with `assumed_site` parses through the Foundation parser with the six rows on their
  components; **P2** a basis of `"ASSUMED"` on either new key is refused naming the key; **P3** `generator-minimum-load`
  on the battery is refused by the carrier rule; **P4** `GENERATOR_CURVE_NEEDS` names exactly the three keys with units
  `L/h`, `%`, `%` and is on no `ModelProfile` in `MODEL_PROFILES` (0K4a puts it there).

**Regression:** `pytest simulator/tests` (whole), `host/tests/test_registered_kobo_execution.py` and
`host/tests/test_0k2_kobo_season.py` unchanged and green, check-all (fast) once at the end, `python
tools/select-tests.py --base main`.

## 4. Units

| Commit | Content |
|---|---|
| 1 (1.0) | §2.1, §2.2 and F1-F10 |
| 2 (0.5) | §2.3, §2.4, §2.5, P1-P4, regression, packet |

Packet `specs/0K4b-fuel-curve-taper/packet.md`: the pre-flight print, the F3 table (litres an hour and litres per kWh
at 0, 25, 50, 75, 100 % load for Kobo's assumed curve, labelled assumed), the F8 step counts, the regression output and
the mid-build count.

## 5. Done (questions; each can fail)

1. Do idle, part load and full load burn what the declared curve says, with the full-load figure equal to `SFC x
   rating` and STARTING burning the no-load rate?
2. Does a frozen `L/h` value burn correctly in a 5-minute step (the `L/min` canonical unit is handled once, in the
   module)?
3. Does acceptance taper above the start and never below the floor, so that the last 10 points are slower?
4. Are the three curve refusals raised in order, and the handlers' range refusals raised through `consume`?
5. Does the Foundation accept the new keys and bases where they belong and refuse them elsewhere, with the shipped
   template and every v7 digest unchanged?
6. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 6. Out of scope

The dispatch rule and the v8 assembly (0K4a); the product's fuel law (0K4f, D-0K4.13); editing the shipped template
(D-0K4.7); any screen or served text; start fuel beyond the no-load burn during STARTING (no Kobo record supports a
separate start figure).
