# 0K3: the replay series read from stored readings (implementer spec)

Status: spec rev 1, handshake not started. Architect (Claude), 2026-11-21, on the owner's delegation
(`owner/owner-away-architect-decides-2026-11-21.md`). Queued by D-0K2.1 ("reading that series from accepted
readings ... a queued unit, `0K3` (about 2 units)"). **2 units.** Discovery review (W5): a new mechanism on the
evidence seam whose series feed a litre figure that becomes money in `6c`. Non-screen. No migration, no served
text, no guard change. `USER_REVIEW_REQUIRED: false` (nothing served). Decisions: `rulings.md` (D-0K3.1 to
D-0K3.9). Reviewer guide: `reviewer-guide.md`. Handshake: `handshake.md`.

- **What it is.** A producer for 0K2's seam: `SeriesReader.read` turns a Site's accepted readings over whole local
  days into the `ObservedSeries` that `replay_study` takes, or refuses with a code and a subject. It reads only what
  is stored and accepted, places each reading on the 5-minute grid by its own interval or instant, and fills nothing.
- **Why now, and what it waits for (D-0K3.1).** No stored 5-minute Kobo series of 61 days exists (D-DS4.1: no world
  telemetry this fortnight; DS3 holds two 15-minute harness days). So 0K3 builds the reader and every refusal now,
  proven on harness fixtures and on the 0K2 season published as readings, and changes no consumer. It does **not**
  run a study on stored readings: that waits for (a) a Site with the six roles bound and 61 days of 5-minute readings
  (DS2's writer at a configured world Site, or a pilot's EMS export), (b) for Kobo itself, a binding of
  `pv_available_power` (D-0K3.4, owner-away row 48), and (c) `6c`, which calls the reader with the Site's frozen base
  run.
- **Builds on (on `main`):** `backend/assetops_backend/runs/replay_study.py` (`ObservedSeries`, `StudyFrame`,
  `replay_study`), `contracts/assetops_contracts/forward_replay.py` (`LoadSeries`),
  `backend/assetops_backend/analytics/assessment_inputs.py` (`AcceptedReading`, `RoleBinding`, `EvidenceQuery`,
  `EvidenceQueryResult`, `Window`, `CohortMember`, `build_input_set`), `analytics/cohort.py` (`select_cohort`),
  `analytics/assessment_worker.py` (`ROLES_BY_SET`), `analytics/dispatch_v3.py` (`ON_STATES`, `OFF_STATES`),
  `analytics/composition.py` (`build_postgres_assessment_store`), `sites/composition.py` (`build_foundation_store`),
  `sites/foundation_records.py` (`FoundationStore.find_site_by_id`, `.registrations`).

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question. 0K2 is merged (`3b4f06052`); no other gate.
- **Branch** `task/0K3-replay-series` off `main`; worktree `/opt/assetecon/AssetOpsV1-0k3`; symlink
  `frontend/node_modules` from the main checkout.
- **Pre-flight print (packet, first section).** (a) On a `pg_harness` clone with MG-W402-001 installed
  (`test_w402_authored_v4_postgres.install`), for each of the six roles of §2.1 the snapshot's binding (device,
  signal, asset code); ingest one planned row per role (§4 G1's kinds) for 2026-10-12 00:00 to 00:05 local and print
  each accepted reading's `(role, interval_start is None, unit, source_mode)`. Expected: the three kW roles with an
  interval and unit `kW`; `battery_soc` `%`, `fuel_level` `L`, `generator_state` `state`, each without an interval;
  `SIMULATED`. A refusal, or a different shape, is a handshake question. (b) On a clone with DS3's converted Kobo
  (`test_ds3_bulk_load_postgres.seed_database`), the roles of its current binding set and the Site's zone. Expected:
  no `pv_available_power`. (c) `find_site_by_id(...).timezone` of both Sites.
- **Read:** `rulings.md`; 0K2 `spec.md` §2.1 and §2.2; `host/tests/kobo_season.py:150-172` (`observed_series`);
  `analytics/assessment_inputs.py:46-200, 340-361`; `analytics/cohort.py:62-80`; `tools/w402_mini_depth_cases.py:
  61-160, 177-196`; `backend/tests/test_w402_reads_postgres.py:45-95`; `backend/tests/test_ds3_bulk_load_postgres.py:
  41-116`; `backend/tests/test_0k1_replay_port_seam.py`.
- **Heavy tools** through the slot pool only (`tools/heavy-slot.sh -- ...`; `--db` for the Postgres file):
  backend tests `test_0k3_replay_series.py`, `test_0k1_replay_port_seam.py`, `test_0k2_replay_study.py`; host tests
  by `pwsh -NoProfile -File tools/run-host-tests.ps1 -- host/tests/test_0k3_series_equivalence.py`; the Postgres
  file on its own `pg_harness` clones (`*_pt<run>_0k3<n>_test`), each dropped in `finally`. Never ports 5490 or 8990,
  the walkthrough DB or Docker.
- **Files.** New: `backend/assetops_backend/runs/replay_series.py`, `backend/tests/test_0k3_replay_series.py`,
  `backend/tests/test_0k3_replay_series_postgres.py`, `host/tests/test_0k3_series_equivalence.py`. Edited:
  `backend/assetops_backend/runs/composition.py` (one builder), `backend/tests/test_0k1_replay_port_seam.py` (the
  allow-list only, D-0K3.8). Nothing under `simulator/`, `contracts/`, `config/`, `runs/replay_study.py`,
  `host/forward_replay.py` or any guard; no migration.
- **No user-facing text** (D-0K3.9): `SeriesRefused.detail` is a developer diagnostic; D-SC1.28 does not apply.

## 1. Outcome and gate questions

Given a Site, whole local days and a knowledge cutoff, does the reader return the `ObservedSeries` of exactly the
accepted readings of the six replay roles, each placed on the 5-minute grid by its own interval or instant, with no
value invented, moved or spread? Does it refuse, with its code and subject, a role that is not bound, a reading
coarser than the step, a conflict, a unit or value it cannot read, an ambiguous cohort and a mixed input class,
before any study runs? When 0K2's simulated season is published as readings, does the reader return the season's own
series, field for field? Does every series say what it is: RECORDED for live readings, SIMULATED for simulated ones?

## 2. Design

### 2.1 Types and constants (`backend/assetops_backend/runs/replay_series.py`)

Imports exactly: `__future__`, `dataclasses`, `datetime`, `fractions`, `re`, `typing`, `uuid`, `zoneinfo`,
`assetops_backend.analytics.assessment_inputs`, `assetops_backend.analytics.assessment_worker`,
`assetops_backend.analytics.cohort`, `assetops_backend.analytics.dispatch_v3`, `assetops_backend.runs.replay_study`,
`assetops_contracts.forward_replay` (test B10 pins the set). No adapter import; no clock read.

```python
STEP = timedelta(minutes=5)
PV, LOAD, GEN_POWER = "pv_available_power", "feeder_demand", "generator_power"
SOC, FUEL, GEN_STATE = "battery_soc", "fuel_level", "generator_state"
REPLAY_ROLES = (PV, LOAD, GEN_POWER, GEN_STATE, SOC, FUEL)      # the query's roles, and the refusal order
MEAN_ROLES = frozenset({PV, LOAD, GEN_POWER})                    # an interval mean, kW
INSTANT_ROLES = frozenset({SOC, FUEL, GEN_STATE})                # a reading at a step's start
ONE_ASSET_ROLES = (PV, GEN_POWER, GEN_STATE, SOC, FUEL)          # exactly one bound asset each; LOAD: one or more
UNITS = MappingProxyType({PV: "kW", LOAD: "kW", GEN_POWER: "kW", SOC: "%", FUEL: "L", GEN_STATE: "state"})
STATES = dispatch_v3.ON_STATES | dispatch_v3.OFF_STATES          # RUNNING, STOPPED, STARTING, FAILED
INPUT_CLASS_BY_MODE = MappingProxyType({"LIVE": "RECORDED", "SIMULATED": "SIMULATED"})
DECIMAL = re.compile(r"-?[0-9]{1,15}(\.[0-9]{1,9})?")
MAX_DAYS = 366
SERIES_ANALYTIC_ID, SERIES_VERSION = "replay-series", "replay-series-1"   # the input set's identity
QUERY_DOMAIN = "replay-series"                                   # a label: query_evidence does not filter on it
READER_REFUSALS = frozenset({
    "READER_WINDOW_INVALID", "READER_SITE_UNKNOWN", "READER_ROLE_UNBOUND", "READER_BINDING_CHANGED",
    "READER_ASSET_UNKNOWN", "READER_COHORT", "READER_RESOLUTION", "READER_READINGS_CONFLICT", "READER_UNIT",
    "READER_VALUE", "READER_STATE_UNKNOWN", "READER_INPUT_CLASS", "READER_START_FUEL_UNKNOWN"})

class SeriesRefused(Exception):
    def __init__(self, code: str, subject: str, detail: str) -> None   # code in READER_REFUSALS, else ValueError

@dataclass(frozen=True)
class SeriesRequest:
    tenant_id: UUID
    site_id: UUID
    first_local_date: date            # the first local day, in the Site's zone
    days: int                         # whole local days, 1 to MAX_DAYS
    knowledge_at: datetime            # aware; readings accepted at or before it (6c: its lease instant)
    cohort: tuple[CohortMember, ...] | None = None   # None: the default selection

@dataclass(frozen=True)
class PlacedSeries:
    series: ObservedSeries
    readings_used: int                # readings that set a step's value (GOOD or not)
    off_grid: tuple[tuple[str, int], ...]   # (role, count) of instants not on a step start: not read (D-0K3.3)

@dataclass(frozen=True)
class SeriesRead:
    series: ObservedSeries
    timezone: str                     # the Site's zone; the caller's StudyFrame uses it
    window: Window                    # UTC [local midnight of the first day, local midnight after the last)
    input_sha256: str                 # build_input_set's identity of the readings and configuration read
    cohort: tuple[CohortMember, ...]  # the selected members
    readings_used: int
    off_grid: tuple[tuple[str, int], ...]
    load_role: str = LOAD             # what the load series is (D-0K3.5)

class EvidenceSource(Protocol):
    def query_evidence(self, query: EvidenceQuery) -> EvidenceQueryResult: ...
class SiteRecords(Protocol):
    def find_site_by_id(self, tenant_id: UUID, site_id: UUID): ...      # .timezone
    def registrations(self, tenant_id: UUID, site_id: UUID): ...        # .assets: .id, .asset_code

def local_window(first_local_date: date, days: int, zone: str) -> Window
def bound_assets(bindings: Sequence[RoleBinding], asset_codes: Mapping[UUID, str],
                 window: Window) -> Mapping[str, tuple[UUID, ...]]           # §2.2 step 3
def series_from_readings(readings: Sequence[AcceptedReading], bound: Mapping[str, tuple[UUID, ...]],
                         asset_codes: Mapping[UUID, str], window: Window) -> PlacedSeries   # §2.3

class SeriesReader:
    def __init__(self, evidence: EvidenceSource, sites: SiteRecords) -> None
    def read(self, request: SeriesRequest) -> SeriesRead                  # §2.2
```

`runs/composition.py` gains `build_series_reader(database_url: str) -> SeriesReader`, returning
`SeriesReader(build_postgres_assessment_store(database_url), build_foundation_store(database_url))` (imports of the
two builders, nothing else).

### 2.2 `SeriesReader.read`, in this order (the first failure raises; nothing is queried before step 3)

1. **Request.** `days` an `int` (not `bool`) in `1..MAX_DAYS`, `first_local_date` a `date` (not a `datetime`),
   `knowledge_at` aware: else `READER_WINDOW_INVALID`, subject `days`, `first_local_date` or `knowledge_at`.
2. **Site.** `site = sites.find_site_by_id(tenant_id, site_id)`; `None`: `READER_SITE_UNKNOWN` subject the site id.
   `zone = site.timezone`; not resolvable by `ZoneInfo`: `READER_WINDOW_INVALID` subject `timezone`. `window =
   local_window(first_local_date, days, zone)`: start `datetime.combine(first_local_date, time(0), ZoneInfo(zone))`,
   end the same for `first_local_date + timedelta(days=days)`, both to UTC. `asset_codes = {a.id: a.asset_code for a
   in sites.registrations(tenant_id, site_id).assets}`.
3. **Query.** `result = evidence.query_evidence(EvidenceQuery(tenant_id, site_id, QUERY_DOMAIN, window,
   knowledge_at, cohort=request.cohort, roles=REPLAY_ROLES))` (one call; the default bracket).
4. **Bindings.** `bound = bound_assets(result.bindings, asset_codes, window)`, before the cohort (configuration is
   checked before readings, so an unbound role is named whatever the readings are):
   - per role in `REPLAY_ROLES` order, the distinct `asset_id`s of bindings of that role whose `[valid_from,
     valid_to)` overlaps the window (`valid_to` `None` is open);
   - none: `READER_ROLE_UNBOUND` subject the role;
   - a role of `ONE_ASSET_ROLES` with more than one asset: `READER_BINDING_CHANGED` subject the role;
   - a `LOAD` asset that is `None` or absent from `asset_codes`: `READER_ASSET_UNKNOWN` subject `feeder_demand:<asset
     id>`. (Load ids are asset codes, D-0K3.5; the other roles need no code.)
5. **Cohort.** `selection = select_cohort(result.readings, window, request.cohort, result.attestations)`; not
   `selection.usable`: `READER_COHORT` subject `selection.status`. `inputs = build_input_set(result, selection,
   analytic_id=SERIES_ANALYTIC_ID, model_version=SERIES_VERSION, roles_by_set=ROLES_BY_SET)`.
6. **Series.** `placed = series_from_readings(inputs.readings, bound, asset_codes, window)` (§2.3).
7. Return `SeriesRead(placed.series, zone, window, inputs.input_sha256, selection.members, placed.readings_used,
   placed.off_grid)`.

### 2.3 `series_from_readings`: placing readings on the grid (exact; D-0K3.2, D-0K3.3)

Let `n = (window.end - window.start) / STEP` (an integer for whole local days of any zone whose offsets are whole
minutes of 5; otherwise `READER_WINDOW_INVALID` subject `steps`), `t_k = window.start + k × STEP`. Readings are
taken in the order `(REPLAY_ROLES.index(role), asset code or "", placed_at, str(evidence_id))`; a reading whose role
is not in `REPLAY_ROLES` or whose asset is not in `bound[role]` is skipped. The first refusal raises. `iso` is
`assessment_inputs.iso`; a subject is `<role>@<iso>`, or `feeder_demand:<code>@<iso>` for a load.

1. **Window edge.** A reading with `COALESCE(interval_end, source_time) <= window.start` or `COALESCE(interval_start,
   source_time) >= window.end` is outside (the bracket) and skipped. A mean that starts before `window.start` and ends
   after it, or starts before `window.end` and ends after it: `READER_RESOLUTION` (detail "crosses the window
   edge").
2. **Shape.** A `MEAN_ROLES` reading with no interval: `READER_RESOLUTION` (detail "an instant where an interval mean
   is needed"). An `INSTANT_ROLES` reading with an interval: `READER_RESOLUTION` (detail "an interval where an instant
   is needed").
3. **Unit and value** (only when `quality == "GOOD"`): `unit != UNITS[role]`: `READER_UNIT`. For a numeric role,
   `value` `None` or not fullmatching `DECIMAL`: `READER_VALUE`; else `Fraction(value)`. For `GEN_STATE`, `value` not
   in `STATES`: `READER_STATE_UNKNOWN`. A reading of any other quality sets nothing (its step stays `None`) and is not
   checked for unit or value.
4. **Means.** Step `k = (interval_start - window.start) // STEP`. The interval must lie inside `[t_k, t_{k+1})` with
   `interval_end > interval_start`; one that ends after `t_{k+1}` (a coarser mean, e.g. 15 minutes):
   `READER_RESOLUTION` (detail "coarser than the 5-minute step"). The step's means, sorted by start, must not
   overlap (a start before the previous end: `READER_READINGS_CONFLICT`). The step's value is `Σ value × (end −
   start) / STEP` (an exact `Fraction` of seconds) when the means are all GOOD and tile `[t_k, t_{k+1})` exactly
   (first start `t_k`, each end the next start, last end `t_{k+1}`); otherwise `None` (a gap or a non-GOOD part; no
   fill).
5. **Instants.** `source_time` equal to some `t_k`: that step's reading; two readings at one `t_k` of one role and
   asset: `READER_READINGS_CONFLICT`. An instant not on a step start is not read: it counts in `off_grid` for its
   role, and no step takes it.
6. **The series.** `pv_available_kw[k]` from `PV`; `loads` one `LoadSeries(code, kw)` per bound `LOAD` asset, by
   ascending code; `generator_kwh[k] = gen_kw[k] × Fraction(5, 60)` (`None` stays `None`); `generator_state[k]` the
   state text; `soc_pct[k]`; `start_fuel_l` the `FUEL` reading at `t_0`, else `READER_START_FUEL_UNKNOWN` subject
   `fuel_level` (the study needs a start stock; the fuel at any other step is not used). `interval_start =
   iso(window.start)`, `timestep_minutes = 5`.
7. **Input class.** Over the readings that set a value (GOOD and placed): every `source_mode` in
   `INPUT_CLASS_BY_MODE` and one class among them, else `READER_INPUT_CLASS` subject `mixed` or the unknown mode;
   no such reading at all: `READER_COHORT` subject `EMPTY`. `input_class` is that class.

The reader validates and places; it never computes a dispatch, a fuel law, an average across steps, a carry-forward
of a state or a value from another role. Missing values stay `None`: the study treats a day without generator energy,
state or charge as inadmissible, and the port refuses a PV or load gap as `INPUT_GAP` (D-0K2.6).

## 3. Fixtures (the tests' own; W2)

- **R0** (backend, no database): Site zone `Africa/Addis_Ababa` (UTC+3, no clock change), local day 2026-10-12,
  window 2026-10-11T21:00Z to 2026-10-12T21:00Z, 288 steps. Assets: `pv-inverter`, `generator`, `battery`,
  `fuel-tank`, `load-clinic`, `load-mill`, `load-res` (fixed UUIDs). One `RoleBinding` per (role, asset) for the six
  roles, valid from 2026-10-01. Readings written by a test helper `reading(role, asset, *, at=None, start=None,
  end=None, value, unit, quality="GOOD", mode="SIMULATED")` that fills every other `AcceptedReading` field with fixed
  dummies. Values (all exact decimals): PV `"12.50"` kW each step; loads clinic `"1.25"`, mill `"3.00"`, res `"7.75"`;
  generator `"24.000"` kW for steps 72-95 (06:00 to 08:00 local) and `"0"` otherwise; state `RUNNING` at steps 72-95,
  `STOPPED` otherwise; SOC `"60.0"` at steps 72-95, `"80.0"` otherwise; fuel `"15000.0"` at step 0.
- **G1** (Postgres, MG-W402-001, `Africa/Nairobi`): the same 288-step day for local 2026-10-12, as planned rows
  through `w402_mini_depth_cases.build_batches(spec, doc, sha, "positive", extra=rows)`: kind `MEAN` with
  `interval_start = t_k`, `source_time = t_k + 5 min` for the three kW roles; `POINT` at `t_k` for SOC and fuel;
  `STATE` at `t_k` for the generator; device and signal of each from the snapshot's binding for that role and asset.
  Values as R0. The authored positive rows (6 to 10 October) are outside the window and its bracket.
- **K1** (Postgres, DS3's converted Kobo): `kobo_days(kit, [DAY6])` loaded by `Db.load`: 15-minute instants of
  generator status, three feeders and charge, and no PV.
- **S8** (host): 0K2's 8-day season (`test_0k2_kobo_season.site("8")`), published by the test's own writer as
  readings: for step `i`, PV and each load as a 5-minute mean `[t_i, t_{i+1})` of `_q(B[i+1].interval_measurement(
  <address>) / HOURS, 1/100)` kW (loads as `feeder_demand` of asset codes `load-clinic`, `load-mill`, `load-res`);
  generator power as a mean of `_q(B[i+1].interval_measurement(GEN_OUT), 1/1000) × 12` kW; SOC `_q(B[i].stock(SOC),
  1/10)` and generator state `B[i].discrete_state_for_step(GEN)` at `t_i`; fuel `_q(B[0].stock(TANK), 1/10)` at
  `t_0`; all `SIMULATED`. Addresses are spelled in the test (`kobo_season`'s constants may be imported; its
  `observed_series` is the expected value, never the writer).

## 4. Tests (written first)

`backend/tests/test_0k3_replay_series.py` (no database):
- **B1** R0 through `series_from_readings`: every field equals the literal expected tuples (288 values each; the
  loads ordered `load-clinic`, `load-mill`, `load-res`); `generator_kwh` at step 72 is `Fraction(2)`;
  `start_fuel_l == Fraction(15000)`; `input_class == "SIMULATED"`; `readings_used == 288 × 7 + 1` (2,017); `off_grid == ()`.
- **B2** Tiling: step 10's PV as five 1-minute means `"10"`, `"11"`, `"12"`, `"13"`, `"14"` gives `Fraction(12)`; as
  a 2-minute and a 3-minute mean `"10"`, `"15"` gives `Fraction(13)`; with the third minute missing, `None`; with one
  minute `SUSPECT`, `None`; neighbouring steps unchanged.
- **B3** Resolution: a 15-minute PV mean over steps 3-5 → `READER_RESOLUTION` subject `pv_available_power@<t_3>`; a
  PV instant; an SOC mean; a mean from 20:55Z to 21:05Z on 11 October (across the start); each its detail.
- **B4** Conflicts: two overlapping 5-minute PV means in step 7; two SOC instants at `t_7` (equal values too) →
  `READER_READINGS_CONFLICT`.
- **B5** Unit, value, state: PV unit `"W"` → `READER_UNIT`; SOC `"80,0"`, `"1e3"`, a 40-digit value and `None` →
  `READER_VALUE`; state `"IDLE"` → `READER_STATE_UNKNOWN`; the same bad values on a non-GOOD reading refuse nothing
  and leave the step `None`.
- **B6** Off grid: SOC instants at `t_k + 2 min` for every step and none at `t_k` → `soc_pct` all `None`, `off_grid
  == (("battery_soc", 288),)`, no refusal.
- **B7** Bindings (`bound_assets`): no PV binding → `READER_ROLE_UNBOUND` `pv_available_power`; a second generator
  asset whose binding overlaps the window → `READER_BINDING_CHANGED` `generator_power`; one ending before the window
  is ignored; a load asset with no code → `READER_ASSET_UNKNOWN`.
- **B8** Input class: all `LIVE` → `RECORDED`; one GOOD SIMULATED reading among LIVE → `READER_INPUT_CLASS` `mixed`;
  mode `"REPLAY"` → `READER_INPUT_CLASS` `REPLAY`; a non-GOOD reading of another mode does not count.
- **B9** Start fuel: no fuel reading at `t_0` (one at `t_1`) → `READER_START_FUEL_UNKNOWN`.
- **B10** The reader with stub ports: the one query carries `REPLAY_ROLES`, the window of R0 and `knowledge_at`;
  step order — an unbound PV with an AMBIGUOUS cohort refuses `READER_ROLE_UNBOUND`; with PV bound, AMBIGUOUS →
  `READER_COHORT` `AMBIGUOUS`; an unknown site refuses before any query (stub records zero calls); `days` 0, 367,
  `True`, a `datetime` date, a naive `knowledge_at`, zone `"Mars/Base"` each `READER_WINDOW_INVALID`;
  `input_sha256` equals `build_input_set(...)`'s on the same result; `timezone` is the site's. The module's imports
  are exactly §2.1's set (AST).
- **B11** Seam: `replay_study(stub_port, run, read.series, StudyFrame("Africa/Addis_Ababa", Fraction(100)))` on the
  1-day R0 series returns `SAMPLE_TOO_SHORT` with zero port calls (the reader adds no consumer change).
- **B12** No value is made: `replay_series.py` holds no `float(`, `round(`, `interpolat` or `ffill` (source scan), and B2/B6 prove no step takes a value from another step.

`backend/tests/test_0k3_replay_series_postgres.py` (its own clones):
- **G1** MG-W402-001, fixture G1, `build_series_reader(url).read(SeriesRequest(t, s, date(2026, 10, 12), 1, RECEIVED
  + 1 h))`: the series equals R0's expected values (zone Nairobi, window 2026-10-11T21:00Z); `input_class ==
  "SIMULATED"`; `timezone == "Africa/Nairobi"`; the cohort holds the G1 sources.
- **G2** The same Site with one 15-minute PV mean added at 10:00 local → `READER_RESOLUTION`.
- **G3** `knowledge_at = RECEIVED - 1 h` (after the install, before the decision clock: bindings visible, readings
  not) → `READER_COHORT` `EMPTY`.
- **G4** DS3's converted Kobo with K1 → `READER_ROLE_UNBOUND` `pv_available_power` (the harness day is read as far
  as configuration and refused honestly).

`host/tests/test_0k3_series_equivalence.py` (kernel):
- **T1** S8 through `series_from_readings` equals `observed_series(trajectory, 2304)` field by field (loads compared by
  `load_id`); `input_class == "SIMULATED"`.
- **T2** `replay_study(HostForwardReplay(), run, series, frame, grid=())` with the frame of `test_0k2_kobo_season.py:70-71`
  and `min_litre_days=8` returns the same `Calibration` as the same call on `observed_series(...)`.

`backend/tests/test_0k1_replay_port_seam.py`: the allow-list gains exactly `runs/replay_series.py` and
`tests/test_0k3_replay_series.py` (D-0K3.8).

## 5. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.0) | §2.1, §2.3, `local_window`, `bound_assets`; B1-B9, B12; the seam-test edit | 1 |
| 2 (1.0) | §2.2 `SeriesReader`, `build_series_reader`; B10, B11; G1-G4; T1-T2; select-tests set; check-all; packet | 1 to 2 |

Packet `specs/0K3-replay-series-reader/packet.md`: the pre-flight print; G1's series totals (PV, each load,
generator kWh, starts, min SOC) beside R0's literal ones; T1's field-by-field result; the refusal table (code,
subject, which test); each plant with the test that failed; what 0K3 waits for (§0 "Why now"); the mid-build count.

## 6. Done (questions; each can fail)

1. Does the reader return exactly the stored series on R0, G1 and the published season (T1), with loads by asset
   code and generator energy from generator power over the step?
2. Is each reading placed by its own interval or instant, a 1-minute mean tiling a step averaged exactly, and a
   coarser, crossing or conflicting reading refused with its subject?
3. Is nothing filled: a gap, a non-GOOD part or an off-grid instant leaves the step `None`, counted where stated?
4. Are configuration refusals (unbound, changed, unknown asset) given before the cohort, and the cohort's own status
   named when it is not usable?
5. Does every series carry RECORDED or SIMULATED from the readings' own source mode, refusing a mix?
6. Does the study take the reader's series unchanged (B11, T2), with no consumer edited?
7. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 7. Out of scope

Running a study on stored readings (waits for a stored 61-day series, D-0K3.1); `6c` and its base-run choice;
splitting a 15-minute mean into 5-minute steps (D-0K3.2, row 48); reading `pv_power` as available PV (D-0K3.4, row
45); `feeder_requested_power` as the load (D-0K3.5, queue Q4); a state carried forward between change events (D-0K3.3,
queue Q3); a sampling-jitter tolerance; a tool mode reading from the store; any screen or served text.

## 8. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | Build the reader before stored series exist? | Yes, the reader and its refusals, proven on harness fixtures and the published season; the study on stored readings waits (D-0K3.1) |
| Q2 | Readings coarser than 5 minutes (UP-1's 15-minute CSV) | Refused, never split (D-0K3.2; row 48, owner to weigh in) |
| Q3 | A state or level reported only on change, or off the grid | Not read; counted as off-grid; a carry-forward rule waits for a real feed (D-0K3.3) |
| Q4 | Load as requested or delivered power | Delivered (`feeder_demand`, the required role); stated on every read (D-0K3.5) |
| Q5 | `pv_power` where `pv_available_power` is not bound | Refused: output is not availability (D-0K3.4; row 48, owner to weigh in) |
| Q6 | Live readings' class | `LIVE` reads as RECORDED; a mix is refused (D-0K3.6) |
