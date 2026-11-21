# 0M: Mto's demand-on-headroom replay through the same port (implementer spec)

Status: spec rev 1, handshake pending. Architect (Claude), 2026-11-21, on the owner's delegation
(`owner/owner-away-architect-decides-2026-11-21.md`; pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4).
Spike M (`delivery-plan.md` §2 row `0M`: "Mto's demand-on-headroom replay through the same adapter"; lane C,
`two-week-build-plan.md` §0.2 days 10 to 12). **3.5 units.** Discovery review (W5): a new mechanism whose litres and
kWh feed a money figure (design §4.3). Non-screen. No migration. No database. `USER_REVIEW_REQUIRED: false`
(nothing served); the figures go to the owner beside the design values (D-0K2.13, owner-away row 37).

- **What it is.** The product-side demand study `6g` will call: a customer's load profile (kW, local window, week
  days) is added to one of the Site's loads in a whole-window replay through `ForwardReplayPort`, beside the same
  window without it, and the study reports what the customer costs the Site: extra litres (by month), extra
  generator energy, unserved energy, starts, the dawn bound, and, from the observed series, the days on which the
  Site's PV headroom could not carry the customer and the kWh beyond it. It also replays the Site at a reduced
  inverter limit (Mto's failed INV-MT-02) with and without the customer.
- **Why next.** Design §4.3: the huller's 68 L, 225 kWh and 3 days without headroom, and the 5 L a day at half
  inverter capacity, are design values until spike M reproduces them (decision D6); `6g` (Mto's demand decisions)
  depends on `0M`.
- **Builds on:** everything 0K2 builds on, and **0K2 itself** (D-0M.1): `backend/assetops_backend/runs/
  replay_study.py` (`ObservedSeries`, `StudyFrame`, `Calibration`, `MonthFigure`, `StudyDay`, `StudyRefused`,
  `STUDY_STATUSES`, and the §2.5 helpers `study_days`, `admissible_days`, `start_state`, `checked`, `calibrate`,
  `count_starts`, `burns`, `step_local_times`, `by_month`, `dawn_outcome`); `host/tests/kobo_season.py`
  (`base_run`, `season_site`, `season_inputs`, `observed_series`, `SEASON_START`, `TIMEZONE`).
- **Decisions:** `rulings.md` (D-0M.1 to D-0M.11). **Reviewer guide:** `reviewer-guide.md`. **Handshake:**
  `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** 0K2 is merged to `main` (`git merge-base --is-ancestor <0K2 merge> main`), and this handshake has no
  open question. The handshake may run before 0K2 merges; the build may not (D-0M.1). If 0K2's merged helpers differ
  from 0K2 spec §2.5, that is a mid-build question.
- **Branch** `task/0M-mto-headroom-replay` off `main`; worktree `/opt/assetecon/AssetOpsV1-0m`; symlink
  `frontend/node_modules` from the main checkout.
- **Pre-flight print (packet, first section).** `mto_base_run(8).execution_status` and
  `mto_base_run(8, inverter_limit_kw=Fraction(25)).execution_status` (both READY on `main` `a53a77a2e`, probed); the
  frozen initial values of the Mto run at `pv-rated-power`, `inverter-ac-limit`, `battery-energy-capacity`,
  `battery-reserve-state-of-charge`, `generator-rated-power`, `generator-specific-fuel-consumption`; the 8-day site
  run's fuel used and generator kWh. The Architect's probe: baseline 74.47 L; huller 2 of 6 customer days without
  headroom, 128 of 450 kWh beyond it, +51.40 L; welder 6 of 6, 180 of 180 kWh, +45.36 L; reduced capacity +0.24 L a
  day; no unserved energy. A different status or initial value is a mid-build question; different figures are not.
- **Read:** `rulings.md`; design `domain-and-decision-models.md` §3.10 and §4.3 (in the pack); the manifest's Mto
  block (`demo-site-scenario-manifest.yaml`, `site: Mto`, the `physical` line and options `MTO-HULLER`,
  `MTO-WELDING`); 0K2's `spec.md` §2 and §3 and its merged `runs/replay_study.py`.
- **Heavy tools** through the slot pool only, as 0K2 §0: host tests on `host/tests/test_0m_mto_headroom.py`, backend
  tests on `backend/tests/test_0m_headroom_replay.py` and `backend/tests/test_0k1_replay_port_seam.py`; the 61-day
  run with `--label 0M-season`, cap 12 minutes (twice the expected 6). No database, no ports 5490 or 8990, no Docker.
- **Files.** New: `backend/assetops_backend/runs/headroom_replay.py`, `backend/tests/test_0m_headroom_replay.py`,
  `host/tests/mto.py`, `host/tests/test_0m_mto_headroom.py`, `tools/mto_headroom_study.py`. Edited:
  `backend/tests/test_0k1_replay_port_seam.py` (the allow-list gains the two new backend files, as D-0K2.14).
  Nothing under `simulator/`, `contracts/`, `config/`, `host/forward_replay.py`, `runs/replay_port.py`,
  `runs/replay_study.py`, `host/tests/kobo_season.py` or any guard.
- **No user-facing text** (D-0M.11): nothing is served; D-SC1.28 does not apply.

## 1. Outcome and gate questions

On a calibrated baseline, what does connecting the huller (15 kW, 10:00-15:00 local, weekdays) cost Mto, read from a
whole-window replay with it beside one without it: extra litres by month, extra generator energy, unserved energy,
starts and dawn readings? On how many of its days could the observed PV headroom not carry it, and by how many kWh?
Does the welder (10 kW, 18:00-21:00) find no headroom at all, every kWh beyond it? With one of Mto's two inverters
failed (a 25 kW limit), how many litres a day does the Site burn extra with no customer, and what does the huller
cost then? Is every figure read from the port's projections and the observed series, with no price and no law?

## 2. Design

### 2.1 Types (`backend/assetops_backend/runs/headroom_replay.py`)

Imports exactly: `__future__`, `dataclasses`, `datetime`, `fractions`, `assetops_backend.runs.models`,
`assetops_backend.runs.replay_port`, `assetops_backend.runs.replay_study`, `assetops_contracts.forward_replay`.

```python
MIN_DEMAND_DAYS = 28                      # design §4.3: >= 28 days over the customer's window
CUSTOMER_EVIDENCE = frozenset({"SIGNED", "VERBAL"})    # carried, never judged here (D-0M.9)
CAPACITIES = frozenset({"FULL", "REDUCED"})
HEADROOM_REFUSALS = frozenset({"CUSTOMER_ID_INVALID", "CUSTOMER_WINDOW_INVALID", "CUSTOMER_LOAD_UNKNOWN",
                               "REDUCED_CAPACITY_INVALID"})
RESERVED_CASE_IDS = frozenset({"baseline", "reduced"})

@dataclass(frozen=True)
class CustomerLoad:
    customer_id: str                      # CASE_ID form and not reserved; also the case id ("mto-huller")
    kw: Fraction                          # average kW while connected
    local_start: time; local_end: time    # [start, end) inside one local day
    weekdays: frozenset[int]              # Monday = 0 (D-0M.5)
    host_load_id: str                     # the Site load the customer joins (D-0M.4)
    evidence: str                         # CUSTOMER_EVIDENCE
@dataclass(frozen=True)
class ReducedCapacity:
    run: SimulationRun                    # the base run frozen with the reduced inverter limit
    inverter_limit_kw: Fraction           # that run's inverter-ac-limit (the Site's Foundation, as the caller reads it)
@dataclass(frozen=True)
class DemandOutcome:
    case_id: str                          # customer_id at FULL, "reduced-<customer_id>" at REDUCED
    customer_id: str; evidence: str; capacity: str
    customer_days: tuple[str, ...]        # local dates with at least one customer step
    customer_kwh: Fraction
    days_without_headroom: tuple[str, ...]
    kwh_beyond_headroom: Fraction
    extra_fuel_l: Fraction; extra_fuel_l_by_month: tuple[MonthFigure, ...]
    extra_generator_kwh: Fraction; extra_unserved_kwh: Fraction
    extra_starts: int; extra_running_steps: int
    litres_per_customer_kwh: Fraction | None              # None when customer_kwh == 0
    dawn_days_below: int; worst_dawn_soc_pct: Fraction; dawn_verdict: str
@dataclass(frozen=True)
class CapacityOutcome:                    # the reduced limit against full capacity, no customer
    case_id: str                          # "reduced"
    inverter_limit_kw: Fraction
    extra_fuel_l: Fraction; extra_fuel_l_per_day: Fraction; extra_fuel_l_by_month: tuple[MonthFigure, ...]
    extra_generator_kwh: Fraction; extra_unserved_kwh: Fraction
    dawn_days_below: int; worst_dawn_soc_pct: Fraction; dawn_verdict: str
@dataclass(frozen=True)
class HeadroomResult:
    base_run_id: str; status: str; input_class: str     # status in STUDY_STATUSES
    window_start: str; days: int
    calibration: Calibration | None       # None only when SAMPLE_TOO_SHORT
    baseline_fuel_l: Fraction | None      # set only when CALIBRATED
    demand: tuple[DemandOutcome, ...]     # customers at FULL in given order, then at REDUCED; () unless CALIBRATED
    capacity: CapacityOutcome | None      # set when CALIBRATED and `reduced` given
    projections: tuple[ForwardReplayProjection, ...]   # baseline, customers, reduced, reduced customers
    evidence_class: str = "MODELLED"
class HeadroomRefused(Exception):
    def __init__(self, code: str, subject: str, detail: str) -> None   # code in HEADROOM_REFUSALS, else ValueError

def headroom_study(port: ForwardReplayPort, run: SimulationRun, observed: ObservedSeries,
                   customers: tuple[CustomerLoad, ...], frame: StudyFrame, *,
                   reduced: ReducedCapacity | None = None, min_days: int = MIN_DEMAND_DAYS) -> HeadroomResult
```

Construction (`__post_init__`): `kw` and `inverter_limit_kw` are `Fraction`s (`TypeError` otherwise, as D-0K1.9);
`local_start`, `local_end` are `datetime.time`; `weekdays` a `frozenset` of `int`; `evidence` in `CUSTOMER_EVIDENCE`
(`ValueError`); `HeadroomResult.status` in `STUDY_STATUSES`. Value judgements are refusals (§2.2 step 1), so their
reason reaches the caller as a code.

### 2.2 `headroom_study`, in this order (the first failure stops; nothing later runs)

1. **Customers**, each in the given order: `customer_id` not a `CASE_ID` fullmatch, in `RESERVED_CASE_IDS`, starting
   `reduced-`, or repeated: `CUSTOMER_ID_INVALID` subject the id. `kw <= 0`; a time whose minute is not a multiple
   of 5 or whose second is not 0; `local_end <= local_start`; `weekdays` empty or outside 0-6:
   `CUSTOMER_WINDOW_INVALID` subject the id. `host_load_id` not among `observed.loads`' ids:
   `CUSTOMER_LOAD_UNKNOWN` subject the id. `reduced` given with `inverter_limit_kw <= 0`:
   `REDUCED_CAPACITY_INVALID` subject `reduced`.
2. **0K2's window, sample and start:** `days = study_days(observed, frame)`; `ok = admissible_days(observed, days)`;
   `len(ok) < min_days`: return `status="SAMPLE_TOO_SHORT"`, `calibration=None`, no projection, **no port call**;
   `start = start_state(observed)`. (`frame.min_litre_days` is not read here; `min_days` is the demand sample.)
3. **Baseline:** one whole-window call `ForwardReplayRequest("baseline", pv, loads, start)`, `checked(...)`;
   `calibrate(observed, baseline, ok)`; failed: return `status="NOT_CALIBRATED"`, the calibration, `demand=()`,
   `capacity=None`, `projections=(baseline,)`, **no further call**. Port refusals propagate unchanged.
4. **Customers at full capacity:** for each, one whole-window call with case id `customer_id`, the same PV and
   start, and `loads` equal to the observed loads except `host_load_id`, whose `kw[i]` becomes `kw[i] + c_i`
   (§2.3); every other load passed unchanged, in the observed order. `checked(...)`.
5. **Reduced capacity** (only if `reduced`): `pv_r[i] = min(pv[i], inverter_limit_kw)` (D-0M.8); one call
   `port.forward_replay(reduced.run, ForwardReplayRequest("reduced", pv_r, loads, start))`, `checked(...)`; then
   each customer as step 4 on `reduced.run` with `pv_r`, case id `reduced-<customer_id>`.
6. **Outcomes** (§2.3); return `status="CALIBRATED"`.

The port is called `1 + k` times (`k` customers), plus `1 + k` with `reduced`; once when not calibrated; never on a
short sample or a refusal of step 1 or 2. A reduced run is a counterfactual and is not calibrated (D-0M.10).

### 2.3 Rules (exact `Fraction`s; `H = Fraction(5, 60)`; local times from `step_local_times(observed, frame)`)

- **Customer steps:** `c_i = customer.kw` when the step's local weekday is in `weekdays` and its local start time `t`
  has `local_start <= t < local_end`; else `0`. `customer_days` = local dates with a customer step;
  `customer_kwh = Σ c_i × H`.
- **Observed headroom** at the capacity's PV (`pv` at FULL, `pv_r` at REDUCED; D-0M.6): `h_i = max(0, pv_i −
  Σ_load kw_i)` over the observed loads (without the customer). A customer date is **without headroom** when any of
  its customer steps has `h_i < c_i`; `kwh_beyond_headroom = Σ_{c_i > 0} max(0, c_i − h_i) × H`.
- **Extra figures**, the customer's projection `p` against its capacity's no-customer projection `q` (the baseline
  at FULL, `reduced` at REDUCED; D-0M.7): `extra_fuel_l = p.fuel_burned_l − q.fuel_burned_l`;
  `extra_fuel_l_by_month = by_month(burns(p)[i] − burns(q)[i], local_times)`; `extra_generator_kwh`,
  `extra_unserved_kwh`, `extra_running_steps` as `p − q` of the projection totals; `extra_starts` by
  `count_starts` on both; `litres_per_customer_kwh = extra_fuel_l / customer_kwh`; the dawn figures are
  `dawn_outcome(p, days, local_times, frame)`.
- **Capacity outcome:** `reduced` against the baseline: `extra_fuel_l`, by month from `burns`, `extra_fuel_l_per_day
  = extra_fuel_l / days`, `extra_generator_kwh`, `extra_unserved_kwh`, and the dawn figures of `reduced`.
- Nothing applies a price, tariff, SFC, inverter law beyond the `min` of step 5, or dispatch rule.

## 3. Fixtures (`host/tests/mto.py`; declared, D-0M.2, D-0M.3)

```python
MTO_FACTS = (("pv-array", "pv-rated-power", 50), ("battery", "battery-energy-capacity", 150),
             ("battery", "reserve-state-of-charge", 30), ("generator", "generator-rated-power", 30),
             ("generator", "specific-fuel-consumption", 0.33))     # document numbers; the manifest's Mto `physical` line
MTO_RATINGS = (("pv-array", 50), ("battery", 150), ("generator", 30))           # each component's `rating.value`
MTO_LOAD_SCALE = Fraction(1, 2)          # Mto delivered 6,000 kWh in October; the Kobo profile is about 11,580 a month
def mto_site(inverter_limit_kw: Fraction = Fraction(50)):   # -> a site_edit: season_site(doc); MTO_FACTS by
    ...                                  #   set_property; MTO_RATINGS; pv-inverter inverter-ac-limit and its rating
def mto_base_run(days: int, *, inverter_limit_kw: Fraction = Fraction(50)) -> SimulationRun
    # base_run(days, site_edit=mto_site(inverter_limit_kw))
def mto_season(run, days) -> FrozenWorldInputs   # season_inputs(run, days, load_scale=MTO_LOAD_SCALE)
HULLER = CustomerLoad("mto-huller", Fraction(15), time(10), time(15), frozenset(range(5)), "load-mill", "SIGNED")
WELDER = CustomerLoad("mto-welder", Fraction(10), time(18), time(21), frozenset(range(5)), "load-mill", "VERBAL")
MTO_FRAME = StudyFrame(timezone=TIMEZONE, battery_capacity_kwh=Fraction(150))
```

`MTO_FACTS` are document numbers, written by `set_property` as the template writes its own (the product parses
them). The site keeps the template fixture's `KOBO-001` id (`kobo_draft` fixes it); results
carry `base_run_id`, never a Site name. Facts Mto does not state keep the Kobo template's values (PCS limits 30 kW,
start 35%, stop 90%, minimum runtime 30 minutes, start delay 5 minutes, conversion efficiency 95%); the packet
lists them.

## 4. Tests (written first)

`backend/tests/test_0m_headroom_replay.py` (a stub port as in 0K2's B tests; no kernel, no database):
- **M1 customer steps are local:** window from `2026-08-31T21:00:00Z` (1 Sep 2026 is a Tuesday local); the huller's
  first step is 07:00Z on 1 Sep; Saturday 5 Sep has none; the request's `load-mill` equals the observed plus 15 at
  exactly those steps; every other load equal, by id, with the observed loads given in reverse order.
- **M2 headroom:** a 15 kW customer over the 60 steps of 10:00-15:00; PV minus load 20 kW at every customer step of
  day 1, 10 kW on day 2, −3 kW on day 3: days 2 and 3 without headroom; `kwh_beyond_headroom = 60 × 5 × H + 60 × 15
  × H` (25 + 75 kWh; a negative headroom counts as 0).
- **M3 extra figures** from scripted projections: extra fuel and its months, generator, unserved, running steps,
  starts, litres per kWh; a customer with `weekdays={5}` on a Tuesday-to-Friday window: `customer_kwh == 0` and
  `litres_per_customer_kwh is None`.
- **M4 reduced:** the reduced baseline's PV request equals `min(obs, 25)` on every step (51.0 → 25, 12.5 → 12.5);
  a reduced customer is compared with the reduced baseline, not the full one (scripted so the two give different
  answers); `extra_fuel_l_per_day == extra_fuel_l / days`.
- **M5 refusals, each with zero port calls:** `"baseline"`, `"reduced-x"`, a repeated id, `"Bad Id"`
  (`CUSTOMER_ID_INVALID`); `kw` 0, 10:02, end equal to start, weekdays `{}` and `{7}` (`CUSTOMER_WINDOW_INVALID`);
  `"load-pump"` (`CUSTOMER_LOAD_UNKNOWN`); limit 0 (`REDUCED_CAPACITY_INVALID`); a sample under `min_days`
  (`SAMPLE_TOO_SHORT`); then NOT_CALIBRATED: exactly one call.
- **M6 calls:** `1 + k` without `reduced`, `2 + 2k` with it; every request of `n` steps.
- **M7 construction and seam:** a `float` `kw`, `evidence="UNKNOWN"`, `HeadroomRefused("NOPE", "", "")` raise;
  `headroom_replay.py` imports exactly §2.1's set (an `ast` scan).

`host/tests/test_0m_mto_headroom.py` (the kernel, an 8-day Mto season, v7; about 1.5 minutes). Expected values
come from the test's own reader (W2): customer steps by fixed offset (local = UTC + 3, weekday from the date),
headroom from the observed series by its own loop, extra litres from the two projections' `fuel_start_l` by its own
loop.
- **H1 calibrated:** `headroom_study(HostForwardReplay(), run, observed, (HULLER, WELDER), MTO_FRAME,
  reduced=ReducedCapacity(mto_base_run(8, inverter_limit_kw=Fraction(25)), Fraction(25)), min_days=8)` is
  `CALIBRATED`; the calibration's figures equal the reader's.
- **H2 huller:** every `DemandOutcome` figure equals the reader's; preconditions: at least one customer day without
  headroom and one with; `extra_fuel_l != 0`.
- **H3 welder anchor:** `kwh_beyond_headroom == customer_kwh` and `days_without_headroom == customer_days` (no PV
  after 18:00, so no headroom), `extra_fuel_l > 0`.
- **H4 reduced:** the capacity outcome equals the reader's; for each customer the REDUCED dates without headroom
  include the FULL ones (`pv_r <= pv` step by step).
- **H5 the request:** through a recording port, the huller's `load-mill` series is the observed one plus the
  reader's customer steps; the other loads are the observed ones.
- **H6 pins:** `MTO_FACTS`, `MTO_RATINGS` and the inverter limits 50 and 25 against the manifest's Mto values
  (written in the test with their manifest line); `HULLER` and `WELDER` against `MTO-HULLER` and `MTO-WELDING`
  (15 kW 10:00-15:00, 10 kW 18:00-21:00); `MTO_LOAD_SCALE == 1/2`; `MIN_DEMAND_DAYS == 28`; September and October
  2026 each have 22 weekdays.
- **H7 sample:** default `min_days` (28) on 8 days: `SAMPLE_TOO_SHORT`, zero port calls.

**Edited** `backend/tests/test_0k1_replay_port_seam.py`: `allowed` gains `runs/headroom_replay.py` and
`backend/tests/test_0m_headroom_replay.py`.

**The 61-day study** (`tools/mto_headroom_study.py --days 61 --out <file>`, paths as 0K2's tool): the Mto season
and site run, the observed series, `headroom_study` with `(HULLER, WELDER)`, the reduced run at 25 kW and the default
`min_days`; one JSON (`"p/q"` and a 3-decimal reading) to `/opt/assetecon/evidence/0M/<run>/study.json`; one line
per case. About 7 kernel runs of 17,568 steps, about 6 minutes. Exit 0 done, 2 refused.

**Regression:** 0K2's `host/tests/test_0k2_kobo_season.py` and `backend/tests/test_0k2_replay_study.py`, the 0K1
seam test, the dependency-direction guard, check-all (fast) once, `python tools/select-tests.py --base main`.
**Guard shown failing:** a scratch copy of `runs/headroom_replay.py` importing `host.forward_replay` fails
`tools/checks/dependency-direction.ps1`.

## 5. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.5) | §2.1, §2.2, §2.3; M1-M7; the seam-test edit | 1 |
| 2 (1.25) | §3 fixtures; H1-H7 | 1 |
| 3 (0.75) | the tool and the 61-day run; regression; guard failing; check-all; packet | 0 to 1 |

Total 3.5. Packet `specs/0M-mto-headroom-replay/packet.md`: the pre-flight print; the 61-day result per case (and per
month) beside the design values (huller in October: 3 days without headroom, 225 kWh "from battery or genset", 68 L;
welder: every kWh diesel, 0.33 L a kWh; reduced capacity: 5 L a day); the calibration figures; the Kobo-template
facts kept; run count and wall time; the guard run; the mid-build count.

## 6. Done (questions; each can fail)

1. Is the customer added to exactly its host load at exactly its local steps, and is every figure read from
   whole-window replays against the right no-customer replay (full or reduced)?
2. Do the headroom days and kWh beyond headroom equal an independent reader's, with the welder finding none at all?
3. Is the reduced run fed `min(PV, limit)` and nothing else changed, and its outcome equal to the reader's?
4. Is every refusal given before the port is called, a short sample never replayed, and a failed calibration followed
   by no other replay?
5. Is there no price, tariff, SFC or law in `headroom_replay.py`, and does every result carry SIMULATED and MODELLED?
6. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 7. Out of scope

Money (tariff × kWh, fuel × price, collection cost, connection cost, value, break-even: `6g` on the valuation
identity); `NO_CUSTOMER_EVIDENCE` and the latent-demand factor (`3.10`, `6g`; the evidence word is only carried,
D-0M.9); the PRODUCTIVE_LOAD scenario as the option's calculation record (`6g`); the inverter restore date and the
LOI lapse (`6g`, `6a`); a second Mto inverter as its own component; reading the series from accepted readings
(`0K3`, D-0K2.1); any label or design-value replacement (held, owner-away row 37); any screen or served text.

## 8. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | 0M depends on 0K1 only (delivery plan) | It starts on 0K2's merge: one calibration rule (D-0M.1) |
| Q2 | Which plant is Mto? | The Kobo template edited to the manifest's Mto facts; the named hybrid template does not resolve on mini-grid v5-v7 (D-0M.2) |
| Q3 | Mto's series | Kobo's season day types and calendar with loads × ½ (D-0M.3) |
| Q4 | "Days without headroom" | From the observed series: PV available minus load below the customer's kW at any customer step (D-0M.6) |
| Q5 | "22 days a month" | Monday to Friday local (D-0M.5) |
| Q6 | The welder has only verbal evidence | Replayed as the negative control; its evidence word is carried; refusing value is `6g`'s (D-0M.9) |
