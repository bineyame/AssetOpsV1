"""0K3: the replay series reader over PostgreSQL (spec §3 G1, K1; §4 G1-G4b).

Two harness Sites, each on its own `pg_harness` clone (`*_pt<run>_0k3<tag>_test`), dropped in `finally`:

- MG-W402-001 (`install_mg_w402_site`, `Africa/Nairobi`): one 288-step local day, 12 October, published through the
  real ledger as planned rows in canonical decimals ("12.5" for R0's "12.50"; the envelope contract refuses
  trailing zeros) (5-minute means of the three kW roles, instants of SOC, fuel and state), values as R0's.
  The authored positive rows (6 to 10 October) are outside the window and its bracket.
- DS3's converted Kobo (`seed_database`, cloned per test): K1, one 15-minute harness day (6 October) loaded in bulk.

Expected values are literals written here (W2). Loads are compared by `load_id` and `kw` only.
Requires ASSETOPS_TEST_DATABASE_URL (backend/TESTING.md).
"""

from __future__ import annotations

import itertools
import os
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction as F
from types import SimpleNamespace
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text

    import pg_harness
    from test_ds3_bulk_load_postgres import DAY6, Db, kobo_days, seal_rows, seed_database
    from test_s1_bindings_postgres import Clock
    from test_s2_evidence_ledger_postgres import enable
    from test_w402_authored_v4_postgres import INSTALLED, RECEIVED, cases, principal, snapshot

    from assetops_backend.analytics.assessment_inputs import EvidenceQuery, RoleBinding
    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.runs.composition import build_series_reader
    from assetops_backend.runs.replay_series import (
        SeriesRefused,
        SeriesRequest,
        bound_assets,
        local_window,
        series_from_readings,
    )
    from assetops_backend.runs.replay_study import StudyDay, StudyFrame, study_days
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.composition import build_foundation_store
    from assetops_backend.sites.w402_demo import install_mg_w402_site

UTC = timezone.utc
FIVE = timedelta(minutes=5)
NAIROBI = "Africa/Nairobi"
G1_DAY = date(2026, 10, 12)
G1_START = datetime(2026, 10, 11, 21, 0, tzinfo=UTC)  # 12 Oct 00:00 in Nairobi (UTC+3)
ROLES = ("pv_available_power", "feeder_demand", "generator_power", "generator_state", "battery_soc", "fuel_level")
# MG-W402-001's channel for each replay role (backend/conversions/mg-w402-001-minigrid-roles-4.json)
PV_CH = ("pv-inverter-controller", "available-power")
PV_OUTPUT_CH = ("pv-inverter-controller", "ac-power")  # bound as pv_power
LOAD_CH = {"load-clinic": ("clinic-meter", "active-power"), "load-mill": ("mill-meter", "active-power"),
           "load-res": ("residential-meter", "active-power")}
GEN_CH = ("generator-controller", "ac-power")
STATE_CH = ("generator-controller", "status")
SOC_CH = ("battery-pcs-controller", "state-of-charge")
FUEL_CH = ("fuel-level-sensor", "fuel-level")
# R0's literal values
EXP_PV = (F(25, 2),) * 288
EXP_LOADS = (("load-clinic", (F(5, 4),) * 288), ("load-mill", (F(3),) * 288), ("load-res", (F(31, 4),) * 288))
EXP_GEN_KWH = (F(0),) * 72 + (F(2),) * 24 + (F(0),) * 192
EXP_STATE = ("STOPPED",) * 72 + ("RUNNING",) * 24 + ("STOPPED",) * 192
EXP_SOC = (F(80),) * 72 + (F(60),) * 24 + (F(80),) * 192
_CLONES = itertools.count(1)


def T(k: int) -> datetime:
    return G1_START + k * FIVE


def g1_rows() -> list:
    P = cases.Planned
    rows = []
    for k in range(288):
        running = 72 <= k < 96
        rows.append(P(*PV_CH, T(k + 1), "MEAN", "12.5", "kW", T(k)))
        for code, value in (("load-clinic", "1.25"), ("load-mill", "3"), ("load-res", "7.75")):
            rows.append(P(*LOAD_CH[code], T(k + 1), "MEAN", value, "kW", T(k)))
        rows.append(P(*GEN_CH, T(k + 1), "MEAN", "24" if running else "0", "kW", T(k)))
        rows.append(P(*STATE_CH, T(k), "STATE", "RUNNING" if running else "STOPPED", "state"))
        rows.append(P(*SOC_CH, T(k), "POINT", "60" if running else "80", "%"))
    rows.append(P(*FUEL_CH, T(0), "POINT", "15000", "L"))
    return rows


@contextmanager
def w402(extra=()):
    """A clone holding MG-W402-001 with the positive authored variant plus G1's day plus `extra`."""
    url = pg_harness.clone_database(f"0k3w{next(_CLONES)}")
    store, eng = PostgresFoundationStore(url), create_engine(url)
    ledger = PostgresEvidenceLedger(url, test_decision_clock_override=Clock(RECEIVED))
    holders = [store, eng, ledger]
    try:
        installed = install_mg_w402_site(store, tenant_slug="demo", clock=Clock(INSTALLED))
        site = installed.result.site
        enable(eng, site.id)
        doc, sha = snapshot(eng, installed.binding_set.id)
        service = BatchIngestionService(ledger, Clock(RECEIVED))
        for b in cases.build_batches(cases.load_spec(), doc, sha, "positive", extra=[*g1_rows(), *extra]):
            service.submit(principal(doc), b.body.encode("utf-8"))
        reader = build_series_reader(url)
        holders += [reader._evidence, reader._sites]
        yield SimpleNamespace(url=url, engine=eng, reader=reader, tenant=site.tenant_id, site=site.id, doc=doc)
    finally:
        pg_harness.dispose(*holders)
        pg_harness.drop_database(url)


def refused(code: str, subject: str, call, detail: str | None = None) -> SeriesRefused:
    with pytest.raises(SeriesRefused) as caught:
        call()
    assert (caught.value.code, caught.value.subject) == (code, subject), str(caught.value)
    if detail is not None:
        assert caught.value.detail == detail
    return caught.value


def _starts(states) -> int:
    return sum(1 for a, b in zip(states, states[1:]) if a != "RUNNING" and b == "RUNNING")


# --- MG-W402-001 ------------------------------------------------------------------------------------------------------


def test_g1_and_g1b_the_stored_day_reads_as_r0_and_inverter_output_is_never_pv() -> None:
    output = [cases.Planned(*PV_OUTPUT_CH, T(k + 1), "MEAN", "9", "kW", T(k)) for k in range(288)]  # G1b (9.00 kW, canonical "9")
    with w402(output) as db:
        read = db.reader.read(SeriesRequest(db.tenant, db.site, G1_DAY, 1, RECEIVED + timedelta(hours=1)))
        with db.engine.connect() as c:
            sources = set(c.execute(text(
                "SELECT DISTINCT source_id FROM accepted_evidence WHERE site_id = :s AND source_time >= :a "
                "AND source_time <= :b AND role IN ('pv_available_power', 'feeder_demand', 'generator_power', "
                "'generator_state', 'battery_soc', 'fuel_level')"),
                {"s": db.site, "a": G1_START, "b": G1_START + timedelta(days=1)}).scalars())
    s = read.series
    assert s.interval_start == "2026-10-11T21:00:00Z" and s.timestep_minutes == 5
    assert s.pv_available_kw == EXP_PV  # G1b (9.00 kW, canonical "9"): the 9.00 kW inverter output is not read
    assert tuple((x.load_id, x.kw) for x in s.loads) == EXP_LOADS
    assert s.generator_kwh == EXP_GEN_KWH and s.generator_state == EXP_STATE and s.soc_pct == EXP_SOC
    assert s.start_fuel_l == F(15000) and s.input_class == "SIMULATED"
    assert read.timezone == "Africa/Nairobi" and read.load_role == "feeder_demand"
    assert read.window.start == G1_START and read.window.end == G1_START + timedelta(days=1)
    assert read.readings_used == 2017 and read.off_grid == ()
    assert sources and sources <= {m.source_id for m in read.cohort}
    # the mean ending at window.end is read (D-0K3.17)
    assert s.pv_available_kw[287] is not None and s.generator_kwh[287] is not None
    assert all(x.kw[287] is not None for x in s.loads)
    assert study_days(s, StudyFrame("Africa/Nairobi", F(100))) == (StudyDay("2026-10-12", 0, 288),)
    # the packet's totals beside R0's: PV 300 kWh, loads 30 / 72 / 186 kWh, generator 48 kWh, 1 start, min SOC 60
    assert sum(s.pv_available_kw) * F(5, 60) == 300
    assert [sum(x.kw) * F(5, 60) for x in s.loads] == [30, 72, 186]
    assert sum(s.generator_kwh) == 48 and _starts(s.generator_state) == 1 and min(s.soc_pct) == 60


def test_g2_a_15_minute_mean_is_refused() -> None:
    at = datetime(2026, 10, 12, 7, 0, tzinfo=UTC)  # 10:00 local
    coarse = cases.Planned(*PV_CH, at + timedelta(minutes=15), "MEAN", "12.5", "kW", at)
    with w402([coarse]) as db:
        refused("READER_RESOLUTION", "pv_available_power@2026-10-12T07:00:00.000000Z",
                lambda: db.reader.read(SeriesRequest(db.tenant, db.site, G1_DAY, 1, RECEIVED + timedelta(hours=1))),
                "coarser than the 5-minute step")


def test_g3_readings_not_yet_known_are_an_empty_cohort() -> None:
    with w402() as db:
        refused("READER_COHORT", "EMPTY",
                lambda: db.reader.read(SeriesRequest(db.tenant, db.site, G1_DAY, 1, RECEIVED - timedelta(hours=1))))


# --- DS3's converted Kobo -------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def seed():
    url, kit, _ = seed_database("0k3s")
    try:
        yield url, kit
    finally:
        pg_harness.drop_database(url)


@pytest.fixture()
def kobo(seed):
    url, kit = seed
    clone = Db(pg_harness.clone_database(f"0k3k{next(_CLONES)}", url))
    clone.kit = kit
    holders = []
    try:
        clone.load(kobo_days(kit, [DAY6]))
        clone.holders = holders
        yield clone
    finally:
        pg_harness.dispose(*holders)
        clone.close()


def _known(db) -> datetime:
    return db.rows("SELECT max(decided_at) FROM ingestion_disposition")[0][0]


def _kobo_read(db):
    reader = build_series_reader(db.url)
    db.holders += [reader._evidence, reader._sites]
    p = db.kit.principal
    return reader.read(SeriesRequest(p.tenant_id, p.site_id, date(2026, 10, 6), 1, _known(db)))


def test_g4_kobo_is_refused_on_its_configuration(kobo) -> None:
    refused("READER_ROLE_UNBOUND", "pv_available_power", lambda: _kobo_read(kobo))


def test_g4a_kobo_own_inverter_output_is_not_available_pv(kobo) -> None:
    rows = [("pv-inverter-controller", "ac-power", DAY6 + timedelta(minutes=15 * i), "5") for i in range(96)]
    kobo.load(seal_rows(kobo.kit, rows, {}))
    assert kobo.rows("SELECT count(*) FROM accepted_evidence WHERE role = 'pv_power'")[0][0] == 96
    refused("READER_ROLE_UNBOUND", "pv_available_power", lambda: _kobo_read(kobo))


def test_g4b_kobo_own_readings_meet_a_readings_refusal(kobo) -> None:
    p = kobo.kit.principal
    sites = build_foundation_store(kobo.url)
    evidence = build_postgres_assessment_store(kobo.url)
    kobo.holders += [sites, evidence]
    zone = sites.find_site_by_id(p.tenant_id, p.site_id).timezone
    assert zone == "Africa/Addis_Ababa"  # pre-flight (c): Kobo's zone is Addis Ababa, UTC+3 like Nairobi (mid-build Q1)
    codes = {a.id: a.asset_code for a in sites.registrations(p.tenant_id, p.site_id).assets}
    window = local_window(date(2026, 10, 6), 1, zone)
    assert window.start == datetime(2026, 10, 5, 21, 0, tzinfo=UTC)
    result = evidence.query_evidence(EvidenceQuery(p.tenant_id, p.site_id, "replay-series", window, _known(kobo),
                                                   roles=ROLES))
    assert result.readings and not any(b.role == "pv_available_power" for b in result.bindings)
    inverter = next(i for i, c in codes.items() if c == "pv-inverter")
    test_only = RoleBinding("pv_available_power", inverter, datetime(2026, 1, 1, tzinfo=UTC), None, UUID(int=1),
                            UUID(int=2), "test-only")
    bound = bound_assets((*result.bindings, test_only), codes, window)
    refused("READER_RESOLUTION", "feeder_demand:load-clinic@2026-10-06T00:00:00.000000Z",
            lambda: series_from_readings(result.readings, bound, codes, window),
            "an instant where an interval mean is needed")
