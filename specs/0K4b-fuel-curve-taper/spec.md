# 0K4b: the generator's fuel curve and the battery's charge taper (implementer spec)

Status: live, rev 2 (Architect, Claude, 2026-11-21): handshake answered (D-0K4.19 to D-0K4.21, D-0K4.25), build-ready.
**2.0 units.**
Discovery review (W5): a new physical law whose litres feed a money figure. Non-screen. No migration. No database.
`USER_REVIEW_REQUIRED: false` (the four new names reach the Foundation read only for a Site
that declares the keys; no shipped Site does). Rulings: `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.5,
D-0K4.6, D-0K4.7; handshake answers D-0K4.19 to D-0K4.21; the family rulings D-0K4.1 to D-0K4.25). Reviewer guide:
`reviewer-guide.md`. Questions: `handshake.md`, `handshake-I.md`.

**Rev 2 (handshake).** Every new served word is SC-1 (D-0K4.19): the property names are vocabulary entries, the need
statements are a statement, and both reach their reads through `served_text` (§2.6). F11 runs the contract's own
conversion, F12 pins the constants, P1-P3 parse inline and P5 checks the fixture on the host side (D-0K4.20,
D-0K4.21). The minimum-load refusal has its own words.

- **What it is.** The two physical laws `mini-grid` v8 needs, written once as a pure module, plus the three Foundation
  properties they read and the assumed Kobo values as a test fixture. No model version is made here: 0K4a assembles v8
  from this module (D-0K4.2), so nothing on `main` runs these laws until 0K4a merges.
- **Why next.** Review §3 rows 4-6: fuel with no idle burn, no part-load penalty and no taper all understate a lower
  stop setting. Lane 2, first (D-0K4.1); 0K4a's commit 3 waits for this merge.
- **Builds on (`main`, `fa13f254f`):** `simulator/assetops_simulator/packs/minigrid.py` (`_coefficient`,
  `_percentage`, `PhysicallyUnacceptable` via `packs/fuel.py`), `packs/mini_grid.py` (`_positive`, for the pattern),
  `contracts/assetops_contracts/execution_contract.py:465-479` (`CANONICAL_UNITS`: `L/h` freezes as `VOLUME_RATE` in
  `L/min`, value / 60), `backend/assetops_backend/sites/models.py:262-352` (the property catalogue), `backend/
  assetops_backend/runs/profiles.py:953` (`_need`), `host/tests/kobo.py` (`component`), `tools/demo_combined_kobo.py:
  138-145` (the owner's 3.3 L/h, `GENERIC_DEFAULT`).

## 0. Before you start

- **Start** when the shared 0K4a/0K4b handshake has no open question. Branch `task/0K4b-fuel-curve` off `main`;
  worktree `/opt/assetecon/AssetOpsV1-0k4b`; symlink `frontend/node_modules` from the main checkout.
- **Pre-flight print (packet, first section):** the frozen value and canonical unit that a Kobo draft run
  (`kobo_draft("kobo-mini-grid-prolonged", timestep_minutes=5, model_profile="mini-grid", model_profile_version=7,
  site_edit=assumed_site)`) carries for `generator-no-load-fuel-rate`, if any (v7 does not need it, so expect none;
  say so); `host/tests/test_registered_kobo_execution.py` run unchanged (record green); and a v7 `kobo_draft(...)` run
  with and without `site_edit=assumed_site` compared boundary by boundary (stocks, interval measurements, discrete
  states): equal, or which values differ and why (D-0K4.20).
- **Files.** New: `simulator/assetops_simulator/packs/generator_curve.py`, `simulator/tests/test_generator_curve.py`,
  `host/tests/kobo_assumed.py`, `host/tests/test_0k4b_kobo_assumed.py`, `backend/tests/test_0k4b_properties.py`,
  `backend/assetops_backend/served_text.py`, `backend/assetops_backend/i18n/statements/en/foundation.py`,
  `backend/assetops_backend/i18n/statements/en/model_profile.py`, `backend/tests/statement_cases/foundation.py`,
  `backend/tests/statement_cases/model_profile.py`. Edited: `backend/assetops_backend/sites/models.py` (catalogue rows,
  §2.3; `display_name`'s type, §2.6), `backend/assetops_backend/runs/profiles.py` (one new tuple, §2.4, used by no
  profile yet; `_need`'s and `SupportedState.statement`'s type, §2.6), `backend/assetops_backend/i18n/statements/en/
  vocabulary.py` (one vocabulary), `backend/assetops_backend/sites_api.py` (one line, §2.6),
  `backend/tests/test_component_properties.py` (line 120, §2.6). Nothing under `config/`, `contracts/`,
  `host/forward_replay.py`, `packs/mini_grid.py` or any guard, and no entry in either statement baseline or the allow
  file.
- **Heavy tools** through the slot pool (`tools/heavy-slot.sh -- ...`). Simulator tests run whole (T2 rule:
  `pytest simulator/tests`, never `-k`). No database; never ports 5490 or 8990.
- **Served words are SC-1 (D-0K4.19).** The four property names and the three need statements are catalogue data in
  `i18n/statements/en/` (§2.6). The guard reports no `HAND_BUILT_NEW` for this unit; if it does, that is a mid-build
  question, never a baseline entry.

## 1. Outcome and gate questions

Does the fuel law give the declared no-load rate at no load, `SFC x rating` an hour at full load and the straight line
between, with STARTING burning the no-load rate and STOPPED and FAILED nothing? Does a frozen `L/h` value arrive as
`L/min` and burn the right litres in a 5-minute step? Does charge acceptance stay at the PCS limit up to the taper
start and fall linearly above it to a floor of one twentieth, so that the last 10 points take longer than the 10 before
them? Are a curve below the energy content of diesel, a negative slope, a non-positive no-load rate and a taper start
outside (0, 100] refused? Does the Foundation accept the three new properties and their bases on the right
components, and refuse a basis outside the set?

## 2. Design

### 2.1 `simulator/assetops_simulator/packs/generator_curve.py` (pure; imports `dataclasses`, `fractions`, `kernel.model` (`StateHandler`), `packs.minigrid`, `packs.fuel` only)

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
checks stay exact. The module holds no state and reads no context: 0K4a's resolver calls it per segment. The module
docstring says: "these are `mini-grid` v8's physics: changing one is a new model version, never an edit" (F12,
D-0K4.20). The only `60` in the module is the slope's `60 x no_load / rated`.

### 2.2 State handlers (the same module)

```python
CURVE_HANDLERS: tuple[StateHandler, ...] = (
    daytime._coefficient(NO_LOAD_FUEL_RATE, "generator-no-load-fuel-rate-coefficient", "VOLUME_RATE",
                         _positive_rate, "Litres an hour the generator burns while STARTING or RUNNING at no output."),
    daytime._coefficient(MINIMUM_LOAD, "generator-minimum-load-coefficient", "FRACTION",
                         _share_of_rating,
                         "Site policy: the least share of its rating a running generator is held at."),
    daytime._coefficient(TAPER_START, "battery-charge-taper-start-coefficient", "FRACTION",
                         _taper_start, "The state of charge above which the battery accepts less than its limit."),
)
CURVE_RELATIONS: tuple[ComponentRelation, ...]   # none new: 0K4a adds the two generator keys to the v8 "generator"
                                                 # relation and the taper key to the battery's (assembled there)
```

`_positive_rate` refuses `<= 0` with `PhysicallyUnacceptable` ("a no-load fuel rate of {v} L/min is not positive");
`_share_of_rating` refuses outside `[0, 100]` ("a minimum generator load of {v} % is not a share of the generator's
rating"; D-0K4.21, R6: `daytime._percentage` would say "of a battery");
`_taper_start` refuses outside `(0, 100]` ("a taper start of {v} % is not a state of charge above 0 and at most 100").

### 2.3 Foundation catalogue (`backend/assetops_backend/sites/models.py`)

Add, after the FUEL-1 block, with a comment citing D-0K4.4 and D-0K4.6:

| Key | `unit` | `kind` | `display_name` | Carrier (`MINIGRID_PROPERTY_CARRIERS`) |
|---|---|---|---|---|
| `generator-minimum-load` | `%` | `CONTROL` | `_name("generator_minimum_load")` | GENERATOR |
| `generator-minimum-load-basis` | `state` | `CONTROL` | `_name("generator_minimum_load_basis")` | GENERATOR |
| `battery-charge-taper-start` | `%` | `PHYSICAL` | `_name("battery_charge_taper_start")` | BATTERY |
| `battery-charge-taper-start-basis` | `state` | `PHYSICAL` | `_name("battery_charge_taper_start_basis")` | BATTERY |

`_name(key) = message("foundation.property_name", property=Word("foundation_property", key))`, defined once in
`sites/models.py` beside the catalogue (imports `message`, `Word` from `assetops_backend.i18n`). The English is in §2.6.

`STATE_PROPERTY_VALUES` gains both basis keys with `frozenset({"GENERIC_DEFAULT", "MANUFACTURER_DATASHEET",
"SITE_TEST"})`. `generator-no-load-fuel-rate` and its basis exist already (FUEL-1 A1) and are not touched.

### 2.4 Profile needs, not yet used (`backend/assetops_backend/runs/profiles.py`)

```python
#: 0K4b (D-0K4.4 to D-0K4.6): the three Foundation needs `mini-grid` v8 adds. 0K4a puts them on MINI_GRID_V8_MODEL.
GENERATOR_CURVE_NEEDS: tuple[SupportedState, ...] = (
    _need("generator-no-load-fuel-rate", "GENERATOR", "generator-no-load-fuel-rate", "L/h",
          message("model_profile.need", need=State("GENERATOR_NO_LOAD_FUEL_RATE"))),
    _need("generator-minimum-load", "GENERATOR", "generator-minimum-load", "%",
          message("model_profile.need", need=State("GENERATOR_MINIMUM_LOAD"))),
    _need("battery-charge-taper-start", "BATTERY", "battery-charge-taper-start", "%",
          message("model_profile.need", need=State("BATTERY_CHARGE_TAPER_START"))),
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

### 2.6 The words, through SC-1 (D-0K4.19)

`backend/assetops_backend/served_text.py` (new; the migration seam for legacy text families, deleted when the last
family is migrated, queue Q9):

```python
"""D-0K4.19: a field of a legacy text family holds a legacy `str` or an SC-1 `Message`; its serving read calls this."""
from assetops_backend.i18n import Message, render

def served_text(value: str | Message) -> str:
    return value if isinstance(value, str) else render(value)
```

- `sites/models.py`: `PropertyDefinition.display_name: str | Message`. `runs/profiles.py`: `SupportedState.statement:
  str | Message`, and `_need(..., statement: str | Message)`; `runs/profiles.py` imports `Message`, `State` and `message`
  from `assetops_backend.i18n`. No other field changes; legacy values stay `str`.
- `sites_api.py:145`: `"display_name": served_text(COMPONENT_PROPERTY_DEFINITIONS[item.property_key].display_name)`.
- `backend/tests/test_component_properties.py:120`: `assert served_text(definition.display_name).strip(), key`.
- `simulator_lab_api.run_profile_summary` is 0K4a's seam (the needs are on no profile until then).

`i18n/statements/en/vocabulary.py`, a new vocabulary appended to `VOCABULARY` (keys are the property keys in lower
snake):

```python
"foundation_property": {
    "forms": ["label", "in_sentence"],
    "order": ["generator_minimum_load", "generator_minimum_load_basis", "battery_charge_taper_start",
              "battery_charge_taper_start_basis"],
    "entries": {
        "generator_minimum_load": {"label": "Generator minimum load", "in_sentence": "generator minimum load"},
        "generator_minimum_load_basis": {"label": "Generator minimum load basis",
                                         "in_sentence": "generator minimum load basis"},
        "battery_charge_taper_start": {"label": "Battery charge taper start",
                                       "in_sentence": "battery charge taper start"},
        "battery_charge_taper_start_basis": {"label": "Battery charge taper start basis",
                                             "in_sentence": "battery charge taper start basis"},
    },
},
```

`i18n/statements/en/foundation.py` (data only, D-SC1.3):

```python
STATEMENTS = {
    "foundation.property_name": {
        "slots": {"property": {"type": "word", "vocabulary": "foundation_property", "form": "label"}},
        "variants": [{"id": "label", "text": "{property}"}],
        "rephrase": "never",
    },
}
```

`i18n/statements/en/model_profile.py` (data only; 0K4a adds two statements to this file):

```python
STATEMENTS = {
    "model_profile.need": {
        "slots": {"need": {"type": "state", "values": ["GENERATOR_NO_LOAD_FUEL_RATE", "GENERATOR_MINIMUM_LOAD",
                                                       "BATTERY_CHARGE_TAPER_START"]}},
        "variants": [
            {"id": "no_load_fuel_rate", "when": {"is": ["need", "GENERATOR_NO_LOAD_FUEL_RATE"]},
             "text": "Litres an hour the generator burns while starting or running at no output."},
            {"id": "minimum_load", "when": {"is": ["need", "GENERATOR_MINIMUM_LOAD"]},
             "text": "Site policy: the least share of its rating a running generator is held at."},
            {"id": "taper_start", "when": {"is": ["need", "BATTERY_CHARGE_TAPER_START"]},
             "text": "The state of charge above which the battery accepts less than its charge limit."},
        ],
        "exhaustive": "need",
        "rephrase": "never",
    },
}
```

Cases (hand literals, W2): `statement_cases/foundation.py`, one `Case("foundation.property_name", "label", {"property":
Word("foundation_property", k)}, <label>)` per vocabulary entry (four); `statement_cases/model_profile.py`, one case per
variant with the three sentences above. All of these literals were loaded and rendered in a scratch copy of `i18n`
(D-0K4.19, "Checked").

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
  `consume`; a minimum load of 120 is refused with exactly "a minimum generator load of 120 % is not a share of the
  generator's rating".
- **F11 the frozen path:** `value, unit, _ = frozen_canonical_value(3.3, "L/h")` (`contracts/assetops_contracts/
  execution_contract.py:1743`), `rate = normalize_authored_float(value)`: `unit == "L/min"`, `rate == Fraction(11,
  200)`, and a 5-minute STARTING step with `fuel_curve(Fraction(3, 10), rate, Fraction(40))` burns exactly
  `Fraction(11, 40)` L. No `/ 60` in the test (D-0K4.21).
- **F12 constants:** `DIESEL_ENERGY_KWH_PER_L == Fraction(10)`, `MIN_SFC_L_PER_KWH == Fraction(1, 10)`,
  `TAPER_FLOOR_SHARE == Fraction(1, 20)`, as literals (D-0K4.20).

`backend/tests/test_0k4b_properties.py` (no database, under a second):
- **P1** the Kobo template rendered into a site document (`render_site_document(site_from_template(...))`, as
  `host/tests/kobo.py:kobo_site` does), with the six rows appended inline as the test's own literal (W2), parses
  through `sites/foundation_parsing.py:parse_foundation_content` with the six rows on their components; **P2** (same
  path) a basis of `"ASSUMED"` on either new key is refused naming the key; **P3** (same path)
  `generator-minimum-load` on the battery is refused by the carrier rule; **P4** `GENERATOR_CURVE_NEEDS` names exactly
  the three keys with units `L/h`, `%`, `%`, is on no `ModelProfile` in `MODEL_PROFILES` (0K4a puts it there), and
  `served_text` of each statement equals its case sentence; **P6** `served_text` of each new key's `display_name`
  equals its label, and every pre-existing definition's `display_name` is still a `str`.

`host/tests/test_0k4b_kobo_assumed.py` (no database): **P5** `assumed_site` on a rendered Kobo document appends exactly
the six rows of `ASSUMED_PROPERTIES` on their components (`source "SITE"`, `source_version 1`), and raises `KeyError`
when a key is already present.

**Regression:** `pytest simulator/tests` (whole), `host/tests/test_registered_kobo_execution.py` and
`host/tests/test_0k2_kobo_season.py` unchanged and green, `backend/tests/test_component_properties.py`,
`backend/tests/test_sc1_statements.py`, `python tools/checks/statement_catalogue.py` (no `HAND_BUILT_NEW`, no new
allow entry), check-all (fast) once at the end, `python tools/select-tests.py --base main`.

## 4. Units

| Commit | Content |
|---|---|
| 1 (1.0) | §2.1, §2.2 and F1-F12 |
| 2 (1.0) | §2.3-§2.6, P1-P6, the cases, regression, packet |

Packet `specs/0K4b-fuel-curve-taper/packet.md`: the pre-flight print, the F3 table (litres an hour and litres per kWh
at 0, 25, 50, 75, 100 % load for Kobo's assumed curve, headed "assumed (GENERIC_DEFAULT)", no design value beside it;
the 0 % row's litres per kWh reads "not defined (no output)" and its litres an hour 3.3), the F8 step counts, the
regression output, the statement guard's output and the mid-build count.

## 5. Done (questions; each can fail)

1. Do idle, part load and full load burn what the declared curve says, with the full-load figure equal to `SFC x
   rating` and STARTING burning the no-load rate?
2. Does a frozen `L/h` value, converted by the contract's own path, burn correctly in a 5-minute step (F11), with
   the module's only `60` the slope's?
3. Does acceptance taper above the start and never below the floor, so that the last 10 points are slower?
4. Are the three curve refusals raised in order, and the handlers' range refusals raised through `consume`?
5. Does the Foundation accept the new keys and bases where they belong and refuse them elsewhere, with the shipped
   template and every v7 digest unchanged?
6. Is every new served word an SC-1 statement or vocabulary entry, with no baseline or allow entry added?
7. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 6. Out of scope

The dispatch rule and the v8 assembly (0K4a); the product's fuel law (0K4f, D-0K4.13); editing the shipped template
(D-0K4.7); any screen; migrating the existing property names or profile statements to SC-1 (queue Q9); start fuel beyond the no-load burn during STARTING (no Kobo record supports a
separate start figure).
