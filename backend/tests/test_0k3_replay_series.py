"""0K3: the replay series reader on hand-written readings (spec §3 R0, §4 B1-B12). No database, no kernel.

Every expected value is a literal written here (W2): R0 is one local day in Africa/Addis_Ababa (UTC+3, no clock
change), 288 five-minute steps, PV 12.50 kW, loads 1.25 / 3.00 / 7.75 kW, the generator at 24 kW from 06:00 to 08:00
local (steps 72-95) and SOC 60 % then, 80 % otherwise, 15000 L at the start. The reader is reached through
`series_from_readings` (B1-B9), through `SeriesReader` with stub ports (B7b, B10, B11) and by a source scan (B12).
"""

from __future__ import annotations

import ast
import itertools
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

from assetops_backend.analytics.assessment_inputs import (
    AcceptedReading,
    CohortMember,
    EvidenceQueryResult,
    RoleBinding,
    Window,
    build_input_set,
    iso,
)
from assetops_backend.analytics.assessment_worker import ROLES_BY_SET
from assetops_backend.analytics.cohort import select_cohort
from assetops_backend.runs.replay_series import (
    SeriesReader,
    SeriesRefused,
    SeriesRequest,
    bound_assets,
    series_from_readings,
)
from assetops_backend.runs.replay_study import StudyDay, StudyFrame, replay_study, study_days

BACKEND = Path(__file__).resolve().parents[1]
READER = BACKEND / "assetops_backend" / "runs" / "replay_series.py"
UTC = timezone.utc
FIVE = timedelta(minutes=5)
ZONE = "Africa/Addis_Ababa"
DAY = date(2026, 10, 12)
START = datetime(2026, 10, 11, 21, 0, tzinfo=UTC)  # 12 Oct 00:00 local
WINDOW = Window(START, START + timedelta(days=1))
RECEIVED = datetime(2026, 10, 13, 8, 0, tzinfo=UTC)
TENANT, SITE = UUID(int=900), UUID(int=901)
GATEWAY, SOURCE = UUID(int=910), UUID(int=911)
# load ids run against their codes (load-res lowest), so an order by asset id is visible (plant P8)
CODES_LIST = ("pv-inverter", "generator", "battery", "fuel-tank", "load-res", "load-mill", "load-clinic",
              "generator-2", "load-other")
ASSETS = {code: UUID(int=100 + i) for i, code in enumerate(CODES_LIST)}
CODES = {ASSETS[c]: c for c in CODES_LIST if c != "load-other"}  # load-other has no registered code
PV, LOAD, GEN, STATE, SOC, FUEL = ("pv_available_power", "feeder_demand", "generator_power", "generator_state",
                                   "battery_soc", "fuel_level")
_ids = itertools.count(1)


def T(k: int, start: datetime = START) -> datetime:
    return start + k * FIVE


def reading(role, asset, *, at=None, start=None, end=None, value, unit, quality="GOOD", mode="SIMULATED",
            epoch="epoch-1") -> AcceptedReading:
    n = next(_ids)
    source_time = at if at is not None else end
    return AcceptedReading(
        evidence_id=UUID(int=10**6 + n), envelope_sha256="0" * 64, batch_id=UUID(int=7), gateway_id=GATEWAY,
        source_id=SOURCE, sequence_epoch=epoch, sequence=n, role=role, asset_id=ASSETS[asset],
        source_time=source_time, interval_start=start, interval_end=end, published_at=source_time,
        received_at=RECEIVED, accepted_at=RECEIVED, quality=quality, value=value, unit=unit,
        foundation_revision_id=UUID(int=8), binding_set_revision_id=UUID(int=9), binding_revision_id=UUID(int=10),
        source_mode=mode)


def mean(role, asset, k, value, *, s=START, **kw) -> AcceptedReading:
    return reading(role, asset, start=T(k, s), end=T(k + 1, s), value=value, unit="kW", **kw)


def r0(s: datetime = START, *, pv_role: str = PV, mode: str = "SIMULATED") -> list[AcceptedReading]:
    out = []
    for k in range(288):
        running = 72 <= k < 96
        out.append(mean(pv_role, "pv-inverter", k, "12.50", s=s, mode=mode))
        out.append(mean(LOAD, "load-clinic", k, "1.25", s=s, mode=mode))
        out.append(mean(LOAD, "load-mill", k, "3.00", s=s, mode=mode))
        out.append(mean(LOAD, "load-res", k, "7.75", s=s, mode=mode))
        out.append(mean(GEN, "generator", k, "24.000" if running else "0", s=s, mode=mode))
        out.append(reading(STATE, "generator", at=T(k, s), value="RUNNING" if running else "STOPPED", unit="state",
                           mode=mode))
        out.append(reading(SOC, "battery", at=T(k, s), value="60.0" if running else "80.0", unit="%", mode=mode))
    out.append(reading(FUEL, "fuel-tank", at=s, value="15000.0", unit="L", mode=mode))
    return out


def binding(role, asset, *, valid_from=datetime(2026, 10, 1, tzinfo=UTC), valid_to=None) -> RoleBinding:
    return RoleBinding(role, ASSETS[asset] if asset is not None else None, valid_from, valid_to, UUID(int=20),
                       UUID(int=next(_ids)), "minigrid-roles-4")


def r0_bindings(*, pv_role: str = PV) -> list[RoleBinding]:
    return [binding(pv_role, "pv-inverter"), binding(LOAD, "load-clinic"), binding(LOAD, "load-mill"),
            binding(LOAD, "load-res"), binding(GEN, "generator"), binding(STATE, "generator"),
            binding(SOC, "battery"), binding(FUEL, "fuel-tank")]


BOUND = bound_assets(r0_bindings(), CODES, WINDOW)

# --- the expected values, literal -----------------------------------------------------------------------------------
EXP_PV = (F(25, 2),) * 288
EXP_LOADS = (("load-clinic", (F(5, 4),) * 288), ("load-mill", (F(3),) * 288), ("load-res", (F(31, 4),) * 288))
EXP_GEN_KWH = (F(0),) * 72 + (F(2),) * 24 + (F(0),) * 192
EXP_STATE = ("STOPPED",) * 72 + ("RUNNING",) * 24 + ("STOPPED",) * 192
EXP_SOC = (F(80),) * 72 + (F(60),) * 24 + (F(80),) * 192


def placed(readings, bound=BOUND, window=WINDOW):
    return series_from_readings(readings, bound, CODES, window)


def refused(code: str, subject: str, call, detail: str | None = None) -> SeriesRefused:
    with pytest.raises(SeriesRefused) as caught:
        call()
    assert (caught.value.code, caught.value.subject) == (code, subject), str(caught.value)
    if detail is not None:
        assert caught.value.detail == detail
    return caught.value


def without(readings, role, asset, *steps):
    times = {T(k) for k in steps}
    return [r for r in readings if not (r.role == role and r.asset_id == ASSETS[asset]
                                        and (r.interval_start or r.source_time) in times)]


def only_role_removed(readings, role):
    return [r for r in readings if r.role != role]


# --- B1 ------------------------------------------------------------------------------------------------------------


def test_b1_r0_is_read_exactly() -> None:
    out = placed(r0())
    s = out.series
    assert s.pv_available_kw == EXP_PV
    assert tuple((x.load_id, x.kw) for x in s.loads) == EXP_LOADS
    assert s.generator_kwh == EXP_GEN_KWH and s.generator_kwh[72] == F(2)
    assert s.generator_state == EXP_STATE
    assert s.soc_pct == EXP_SOC
    assert s.start_fuel_l == F(15000)
    assert s.input_class == "SIMULATED"
    assert out.readings_used == 2017 and out.off_grid == ()
    assert s.interval_start == "2026-10-11T21:00:00Z" and s.timestep_minutes == 5
    # the mean ending at window.end is read (D-0K3.17)
    assert s.pv_available_kw[287] == F(25, 2) and s.generator_kwh[287] == F(0)
    assert all(x.kw[287] is not None for x in s.loads)


# --- B2 tiling ------------------------------------------------------------------------------------------------------


def _minutes(parts, k=10, quality=None):
    out = []
    for i, (a, b, value) in enumerate(parts):
        q = "GOOD" if quality is None or quality[i] == "GOOD" else quality[i]
        out.append(reading(PV, "pv-inverter", start=T(k) + timedelta(minutes=a), end=T(k) + timedelta(minutes=b),
                           value=value, unit="kW", quality=q))
    return out


def test_b2_means_that_tile_a_step_average_exactly() -> None:
    base = without(r0(), PV, "pv-inverter", 10)
    ones = [(m, m + 1, str(10 + m)) for m in range(5)]
    s = placed(base + _minutes(ones)).series
    assert s.pv_available_kw[10] == F(12)
    assert s.pv_available_kw[9] == s.pv_available_kw[11] == F(25, 2)
    s = placed(base + _minutes([(0, 2, "10"), (2, 5, "15")])).series
    assert s.pv_available_kw[10] == F(13)
    s = placed(base + _minutes([p for p in ones if p[0] != 2])).series
    assert s.pv_available_kw[10] is None and s.pv_available_kw[9] == s.pv_available_kw[11] == F(25, 2)
    s = placed(base + _minutes(ones, quality=["GOOD", "GOOD", "SUSPECT", "GOOD", "GOOD"])).series
    assert s.pv_available_kw[10] is None and s.pv_available_kw[9] == s.pv_available_kw[11] == F(25, 2)
    s = placed(base + _minutes([(0, 1, "10.1"), (1, 5, "1.3")])).series  # decimals no float holds exactly
    assert s.pv_available_kw[10] == F(101, 10) / 5 + F(13, 10) * 4 / 5


# --- B3 resolution --------------------------------------------------------------------------------------------------


def test_b3_resolution() -> None:
    base = without(r0(), PV, "pv-inverter", 3, 4, 5)
    coarse = reading(PV, "pv-inverter", start=T(3), end=T(6), value="12.50", unit="kW")
    refused("READER_RESOLUTION", f"pv_available_power@{iso(T(3))}", lambda: placed(base + [coarse]),
            "coarser than the 5-minute step")
    point = reading(PV, "pv-inverter", at=T(5), value="12.50", unit="kW")
    refused("READER_RESOLUTION", f"pv_available_power@{iso(T(5))}", lambda: placed(base + [point]),
            "an instant where an interval mean is needed")
    soc_mean = reading(SOC, "battery", start=T(5), end=T(6), value="80.0", unit="%")
    refused("READER_RESOLUTION", f"battery_soc@{iso(T(5))}", lambda: placed(r0() + [soc_mean]),
            "an interval where an instant is needed")
    across = reading(PV, "pv-inverter", start=datetime(2026, 10, 11, 20, 55, tzinfo=UTC),
                     end=datetime(2026, 10, 11, 21, 5, tzinfo=UTC), value="12.50", unit="kW")
    refused("READER_RESOLUTION", "pv_available_power@2026-10-11T20:55:00.000000Z",
            lambda: placed(without(r0(), PV, "pv-inverter", 0) + [across]), "crosses the window edge")
    late = reading(PV, "pv-inverter", start=T(287) + timedelta(minutes=2), end=T(288) + timedelta(minutes=2),
                   value="12.50", unit="kW")
    refused("READER_RESOLUTION", f"pv_available_power@{iso(T(287) + timedelta(minutes=2))}",
            lambda: placed(r0() + [late]), "crosses the window edge")


# --- B4 conflicts ---------------------------------------------------------------------------------------------------


def test_b4_conflicts() -> None:
    base = r0()  # made first: the added reading sorts after R0's at one placement (evidence id)
    second = reading(PV, "pv-inverter", start=T(7) + timedelta(minutes=1), end=T(8), value="13", unit="kW")
    refused("READER_READINGS_CONFLICT", f"pv_available_power@{iso(T(7) + timedelta(minutes=1))}",
            lambda: placed(base + [second]))
    same = reading(SOC, "battery", at=T(7), value="80.0", unit="%")
    refused("READER_READINGS_CONFLICT", f"battery_soc@{iso(T(7))}", lambda: placed(base + [same]))


# --- B5 unit, value, state ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("role,asset,k,bad,code", [
    (PV, "pv-inverter", 4, dict(unit="W", value="12500"), "READER_UNIT"),
    (SOC, "battery", 4, dict(unit="%", value="80,0"), "READER_VALUE"),
    (SOC, "battery", 4, dict(unit="%", value="1e3"), "READER_VALUE"),
    (SOC, "battery", 4, dict(unit="%", value="1" * 40), "READER_VALUE"),
    (SOC, "battery", 4, dict(unit="%", value=None), "READER_VALUE"),
    (STATE, "generator", 4, dict(unit="state", value="IDLE"), "READER_STATE_UNKNOWN"),
])
def test_b5_unit_value_state(role, asset, k, bad, code) -> None:
    base = without(r0(), role, asset, k)

    def make(quality):
        if role == PV:
            return reading(role, asset, start=T(k), end=T(k + 1), quality=quality, **bad)
        return reading(role, asset, at=T(k), quality=quality, **bad)

    subject = f"{role}@{iso(T(k))}"
    refused(code, subject, lambda: placed(base + [make("GOOD")]))
    s = placed(base + [make("SUSPECT")]).series
    field = {PV: s.pv_available_kw, SOC: s.soc_pct, STATE: s.generator_state}[role]
    assert field[k] is None and field[k - 1] is not None and field[k + 1] is not None


# --- B6 off the grid, nothing carried -------------------------------------------------------------------------------


@pytest.mark.parametrize("role", [SOC, STATE, FUEL])
def test_b6_an_instant_off_a_step_start_is_not_read(role) -> None:
    asset, unit, value = {SOC: ("battery", "%", "80.0"), STATE: ("generator", "state", "STOPPED"),
                          FUEL: ("fuel-tank", "L", "15000.0")}[role]
    base = only_role_removed(r0(), role)
    steps = range(288) if role != FUEL else (0,)
    late = [reading(role, asset, at=T(k) + timedelta(minutes=2), value=value, unit=unit) for k in steps]
    if role == FUEL:
        refused("READER_START_FUEL_UNKNOWN", "fuel_level", lambda: placed(base + late))
        return
    out = placed(base + late)
    field = out.series.soc_pct if role == SOC else out.series.generator_state
    assert field == (None,) * 288
    assert out.off_grid == ((role, 288),)


def test_b6b_k1_shape_every_third_step_is_not_carried() -> None:
    base = only_role_removed(only_role_removed(r0(), SOC), STATE)
    extra = []
    for j in range(96):
        extra.append(reading(SOC, "battery", at=T(3 * j), value="10.0" if j % 2 else "20.0", unit="%"))
        extra.append(reading(STATE, "generator", at=T(3 * j), value="RUNNING" if j % 2 else "STOPPED", unit="state"))
    out = placed(base + extra)
    exp_soc, exp_state = [], []
    for j in range(96):
        exp_soc += [F(10) if j % 2 else F(20), None, None]
        exp_state += ["RUNNING" if j % 2 else "STOPPED", None, None]
    assert out.series.soc_pct == tuple(exp_soc)
    assert out.series.generator_state == tuple(exp_state)
    assert out.off_grid == ()


# --- B7 bindings ----------------------------------------------------------------------------------------------------


def test_b7_bindings() -> None:
    no_pv = [b for b in r0_bindings() if b.role != PV]
    refused("READER_ROLE_UNBOUND", "pv_available_power", lambda: bound_assets(no_pv, CODES, WINDOW))
    changed = r0_bindings() + [binding(GEN, "generator-2", valid_from=datetime(2026, 10, 12, 6, tzinfo=UTC))]
    refused("READER_BINDING_CHANGED", "generator_power", lambda: bound_assets(changed, CODES, WINDOW))
    earlier = r0_bindings() + [binding(GEN, "generator-2", valid_to=datetime(2026, 10, 5, tzinfo=UTC))]
    assert bound_assets(earlier, CODES, WINDOW)[GEN] == (ASSETS["generator"],)
    unknown = r0_bindings() + [binding(LOAD, "load-other")]
    refused("READER_ASSET_UNKNOWN", f"feeder_demand:{ASSETS['load-other']}", lambda: bound_assets(unknown, CODES, WINDOW))
    refused("READER_ASSET_UNKNOWN", "feeder_demand:None",
            lambda: bound_assets(r0_bindings() + [binding(LOAD, None)], CODES, WINDOW))
    assert bound_assets(r0_bindings(), CODES, WINDOW)[LOAD] == (ASSETS["load-clinic"], ASSETS["load-mill"],
                                                                ASSETS["load-res"])


# --- the stub ports -------------------------------------------------------------------------------------------------


class Evidence:
    def __init__(self, readings, bindings) -> None:
        self.readings, self.bindings, self.queries = tuple(readings), tuple(bindings), []

    def query_evidence(self, query):
        self.queries.append(query)
        return EvidenceQueryResult(query=query, readings=self.readings, bindings=self.bindings, controls=(),
                                   role_sets=("minigrid-roles-4",))


def sites(zone: str = ZONE, *, known: bool = True):
    assets = [SimpleNamespace(id=i, asset_code=c) for i, c in CODES.items()]
    return SimpleNamespace(
        find_site_by_id=lambda t, s: SimpleNamespace(timezone=zone) if known and (t, s) == (TENANT, SITE) else None,
        registrations=lambda t, s: SimpleNamespace(assets=assets))


def request(**overrides) -> SeriesRequest:
    values = dict(tenant_id=TENANT, site_id=SITE, first_local_date=DAY, days=1, knowledge_at=RECEIVED)
    values.update(overrides)
    return SeriesRequest(**values)


def test_b7b_inverter_output_is_never_available_pv() -> None:
    evidence = Evidence(r0(pv_role="pv_power"), r0_bindings(pv_role="pv_power"))
    refused("READER_ROLE_UNBOUND", "pv_available_power", lambda: SeriesReader(evidence, sites()).read(request()))


# --- B8, B9 ---------------------------------------------------------------------------------------------------------


def test_b8_input_class_from_the_source_mode() -> None:
    assert placed(r0(mode="LIVE")).series.input_class == "RECORDED"
    live = without(r0(mode="LIVE"), SOC, "battery", 9)
    one = reading(SOC, "battery", at=T(9), value="80.0", unit="%", mode="SIMULATED")
    refused("READER_INPUT_CLASS", "mixed", lambda: placed(live + [one]))
    replay = reading(SOC, "battery", at=T(9), value="80.0", unit="%", mode="REPLAY")
    refused("READER_INPUT_CLASS", "REPLAY", lambda: placed(live + [replay]))
    suspect = reading(SOC, "battery", at=T(9), value="80.0", unit="%", mode="SIMULATED", quality="SUSPECT")
    assert placed(live + [suspect]).series.input_class == "RECORDED"


def test_b9_start_fuel() -> None:
    base = only_role_removed(r0(), FUEL)
    later = reading(FUEL, "fuel-tank", at=T(1), value="15000.0", unit="L")
    refused("READER_START_FUEL_UNKNOWN", "fuel_level", lambda: placed(base + [later]))
    bad = reading(FUEL, "fuel-tank", at=T(0), value="15000.0", unit="L", quality="BAD")
    refused("READER_START_FUEL_UNKNOWN", "fuel_level", lambda: placed(base + [bad]))


# --- B10 the reader with stub ports ---------------------------------------------------------------------------------


def test_b10_the_query_and_the_read() -> None:
    evidence = Evidence(r0(), r0_bindings())
    read = SeriesReader(evidence, sites()).read(request())
    [q] = evidence.queries
    assert q.roles == ("pv_available_power", "feeder_demand", "generator_power", "generator_state", "battery_soc",
                       "fuel_level")
    assert (q.window, q.knowledge_at, q.tenant_id, q.site_id, q.cohort) == (WINDOW, RECEIVED, TENANT, SITE, None)
    assert read.window == WINDOW and read.timezone == ZONE and read.load_role == "feeder_demand"
    assert read.series.pv_available_kw == EXP_PV and read.series.pv_available_kw[287] == F(25, 2)
    assert tuple((x.load_id, x.kw) for x in read.series.loads) == EXP_LOADS
    assert read.readings_used == 2017 and read.off_grid == ()
    assert read.cohort == (CohortMember(GATEWAY, SOURCE, "epoch-1"),)
    result = evidence.query_evidence(q)
    selection = select_cohort(result.readings, WINDOW, None, ())
    expected = build_input_set(result, selection, analytic_id="replay-series", model_version="replay-series-1",
                               roles_by_set=ROLES_BY_SET)
    assert read.input_sha256 == expected.input_sha256


def test_b10_order_configuration_before_the_cohort() -> None:
    other_epoch = reading(SOC, "battery", at=T(3), value="80.0", unit="%", epoch="epoch-2")
    no_pv = [b for b in r0_bindings() if b.role != PV]
    refused("READER_ROLE_UNBOUND", "pv_available_power",
            lambda: SeriesReader(Evidence(r0() + [other_epoch], no_pv), sites()).read(request()))
    refused("READER_COHORT", "AMBIGUOUS",
            lambda: SeriesReader(Evidence(r0() + [other_epoch], r0_bindings()), sites()).read(request()))


@pytest.mark.parametrize("overrides,zone,subject", [
    (dict(days=0), ZONE, "days"),
    (dict(days=93), ZONE, "days"),
    (dict(days=True), ZONE, "days"),
    (dict(first_local_date=datetime(2026, 10, 12, tzinfo=UTC)), ZONE, "first_local_date"),
    (dict(knowledge_at=datetime(2026, 10, 13, 8, 0)), ZONE, "knowledge_at"),
    ({}, "Mars/Base", "timezone"),
    (dict(first_local_date=date(2026, 10, 25)), "Europe/London", "day:2026-10-25"),
    (dict(first_local_date=date(2026, 10, 24), days=3), "Europe/London", "day:2026-10-25"),
])
def test_b10_window_refusals_query_nothing(overrides, zone, subject) -> None:
    evidence = Evidence(r0(), r0_bindings())
    refused("READER_WINDOW_INVALID", subject, lambda: SeriesReader(evidence, sites(zone)).read(request(**overrides)))
    assert evidence.queries == []


def test_b10_an_unknown_site_queries_nothing() -> None:
    evidence = Evidence(r0(), r0_bindings())
    refused("READER_SITE_UNKNOWN", str(SITE), lambda: SeriesReader(evidence, sites(known=False)).read(request()))
    assert evidence.queries == []
    with pytest.raises(ValueError):
        SeriesRefused("NOT_A_CODE", "x", "y")


def test_b10_a_quarter_hour_zone_reads() -> None:
    start = datetime(2026, 10, 11, 18, 15, tzinfo=UTC)  # 12 Oct 00:00 in Asia/Kathmandu (UTC+5:45)
    evidence = Evidence(r0(start), r0_bindings())
    read = SeriesReader(evidence, sites("Asia/Kathmandu")).read(request())
    assert read.series.interval_start == "2026-10-11T18:15:00Z"
    assert read.series.pv_available_kw == EXP_PV and read.series.soc_pct == EXP_SOC
    assert study_days(read.series, StudyFrame("Asia/Kathmandu", F(100))) == (StudyDay("2026-10-12", 0, 288),)


def test_b10_the_module_imports_exactly_its_set() -> None:
    tree = ast.parse(READER.read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            modules.update(a.name for a in node.names)
    # spec §2.1's set, plus `types` for the MappingProxyType §2.1 itself names (packet, Known Deviations)
    assert modules == {"__future__", "dataclasses", "datetime", "fractions", "re", "types", "typing", "uuid",
                       "zoneinfo", "assetops_backend.analytics", "assetops_backend.analytics.assessment_inputs",
                       "assetops_backend.analytics.assessment_worker", "assetops_backend.analytics.cohort",
                       "assetops_backend.runs.replay_study", "assetops_contracts.forward_replay"}


# --- B11 the study's own checks -------------------------------------------------------------------------------------


class Port:
    def __init__(self) -> None:
        self.requests = []

    def forward_replay(self, run, request):
        self.requests.append(request)
        raise AssertionError("no port call is expected")


def test_b11_the_study_accepts_the_series() -> None:
    read = SeriesReader(Evidence(r0(), r0_bindings()), sites()).read(request())
    frame = StudyFrame("Africa/Addis_Ababa", F(100))
    assert study_days(read.series, frame) == (StudyDay("2026-10-12", 0, 288),)
    s = read.series
    assert {len(s.pv_available_kw), len(s.generator_kwh), len(s.generator_state), len(s.soc_pct),
            *(len(x.kw) for x in s.loads)} == {288}
    port = Port()
    result = replay_study(port, SimpleNamespace(run_id="run-0k3"), s, frame)
    assert result.status == "SAMPLE_TOO_SHORT" and result.input_class == "SIMULATED"
    assert port.requests == []


# --- B12 no value is made -------------------------------------------------------------------------------------------


def test_b12_no_value_is_made() -> None:
    text = READER.read_text(encoding="utf-8")
    for banned in ("float(", "round(", "interpolat", "ffill"):
        assert banned not in text, banned
