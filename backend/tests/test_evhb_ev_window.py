"""EV-HB (D-E5.48 card EV-HB, `AssetOpsV1-plan2/.agent/build-sheet-OWN-GAPS-2026-11-08.md`): every EV story day
records the depot's whole declared charging hours, Tuesday 08:00-16:00 UTC, instead of the first hour only.

The charging sessions (08:01-08:31) and the fault-day fault keep their values byte for byte; the connector status
minutes outside them are idle heartbeats (UNPLUGGED, or FAULTED after the fault-day latch). With PB-3 the whole
declared day is connector-status-known, so `charging_kwh` grades COMPLETE where the one-hour day graded LOW.

Also (PB-3 review, Low): AVAILABLE and DISABLED, declared connector states (`sites/binding_roles.py`), are known
zero-energy status, not unknown time.

The generated story days (heartbeat, sessions, kWh, grade) are tested in `host/tests/test_evhb_generated_days.py`
(backend tests may not import the simulator). Here: the day list, the producer's window swaps, the state sets, and
the Postgres test, which runs the producer's `run_day` (gateway, Batch V2, the EV worker) on one ordinary and
one fault story day of an 8-hour window and grades them with the real chain builder. Skipped (never passed) without
`ASSETOPS_TEST_DATABASE_URL`.
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
for extra in (ROOT / "tools", ROOT / "host", ROOT / "host" / "tests", ROOT / "gateway" / "tests"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import demo_combined_ev as dev  # noqa: E402
import demo_story_days as sd  # noqa: E402
from assetops_backend.analytics import ev_availability  # noqa: E402
from assetops_backend.chain import grading  # noqa: E402
from assetops_backend.chain.ports import SiteRef  # noqa: E402
from assetops_backend.scenarios import ev_parsing  # noqa: E402
from assetops_backend.sites.binding_roles import EV_CONNECTOR_STATES  # noqa: E402

UTC = timezone.utc
#: A story date (Friday): EV days S-14, S-7 (`normal`) and S (`fault`) fall back to Tue 20 Oct, 27 Oct and 3 Nov.
S = datetime(2026, 11, 6, tzinfo=UTC)
#: The w205b pins of the registered one-hour replays (`test_w205b_ev_replay_postgres.RAW_ACCEPTED_KWH`).
KWH = {"normal": "30", "fault": "15"}
MINUTE = timedelta(minutes=1)


def _ev_days() -> list[sd.DayRun]:
    return [d for d in sd.resolve(sd.load(), S) if d.site == "ev" and d.has_run]


def _declared_hours() -> tuple[str, str]:
    import json

    doc = json.loads((ROOT / "config" / "chain" / "operating-calendar-v1.json").read_text(encoding="utf-8"))
    [hours] = doc["sites"]["EV-LAB-001"]["hours"]
    assert doc["sites"]["EV-LAB-001"]["days"] == ["TUE"]
    return hours["from"], hours["to"]


# ---- the day list and the producer's window ------------------------------------------------------------------


def test_every_ev_story_kind_records_the_declared_charging_hours() -> None:
    """The v4 EV story kinds record the calendar's declared hours, received 30 min after they close (as the
    one-hour day was received 30 min after 09:00). `late` (add-day only, never a story day) keeps its one hour:
    its record is held to a 09:05 release, which a 16:00 first cutoff would no longer make late."""
    lo, hi = _declared_hours()
    kinds = sd.load()["kinds"]["ev"]
    for name in ("normal", "fault"):
        k = kinds[name]
        assert (k["start"], k["end"], k["received_at"]) == (f"D+0d {lo}", f"D+0d {hi}", "D+0d 16:30"), name
    assert (kinds["late"]["start"], kinds["late"]["end"]) == ("D+0d 08:00", "D+0d 09:00")
    assert {e["kind"] for e in sd.load()["sites"]["ev"]} == {"normal", "fault"}


def test_story_window_is_the_day_entry_and_the_parser_takes_it() -> None:
    days = _ev_days()
    assert [d.kind for d in days] == ["normal", "normal", "fault"]
    for day in days:
        lo, hi = dev.story_window(day)
        assert (lo, hi) == (day.start, day.end)
        assert (lo.time().isoformat(), hi.time().isoformat(), lo.weekday()) == ("08:00:00", "16:00:00", 1)
        definition = dev.story_definition(day)
        assert (definition.start, definition.end) == (sd.iso(lo), sd.iso(hi))
    # the module constant is restored after each parse
    assert ev_parsing.EV_WINDOW["end"] == "2026-10-06T09:00:00Z"


def test_swaps_move_every_window_clock_to_the_recorded_day() -> None:
    """The w205b/w504 constants follow the recorded window: decisions at its close (+5 min late), the attestation
    1 min before it, the evidence window equal to it; all restored afterwards."""
    import test_w205b_ev_replay_postgres as w205b

    registered = SimpleNamespace(**{n: getattr(w205b, n) for n in (
        "INSTALL_AT", "SETUP_AT", "WINDOW", "RELEASE", "ATTEST_FROM", "ATTEST_TO", "FIRST_DECISION", "LATE_DECISION",
        "ATTESTED_AT")}, RunSetupService=lambda *a, **kw: None)
    P = SimpleNamespace(E_START=datetime(2026, 10, 6, 8, tzinfo=UTC), E_END=datetime(2026, 10, 6, 9, tzinfo=UTC))
    before = dict(vars(registered)), dict(vars(P)), dict(ev_parsing.EV_WINDOW)
    day = _ev_days()[-1]
    lo, hi = dev.story_window(day)
    saved = dev._swaps(registered, P, day, lo - timedelta(hours=2))
    try:
        assert registered.WINDOW == {"start": sd.iso(lo), "end": sd.iso(hi), "end_exclusive": True}
        assert {k: ev_parsing.EV_WINDOW[k] for k in ("start", "end")} == {"start": sd.iso(lo), "end": sd.iso(hi)}
        assert (P.E_START, P.E_END) == (lo, hi)
        assert (registered.FIRST_DECISION, registered.LATE_DECISION, registered.RELEASE) == (
            hi, hi + timedelta(minutes=5), sd.iso(hi + timedelta(minutes=5)))
        assert registered.ATTESTED_AT == hi - MINUTE
        assert registered.ATTEST_FROM <= lo and registered.ATTEST_TO > hi
    finally:
        dev._restore(registered, P, saved)
    assert (dict(vars(registered)), dict(vars(P)), dict(ev_parsing.EV_WINDOW)) == before


# The generated story days (heartbeat, sessions, kWh, grade) are tested host side, where the simulator may be
# imported: `host/tests/test_evhb_generated_days.py`.


class _Store:  # a snapshot store that writes nothing (the Postgres test grades without appending)
    def latest(self, key):
        return None

    def append(self, row) -> None:
        pass


# ---- PB-3 review Low: AVAILABLE and DISABLED are known zero-energy states ------------------------------------


def _t(h: int, m: int = 0) -> datetime:
    return datetime(2026, 11, 10, h, m, tzinfo=UTC)


def test_every_declared_connector_state_but_charging_is_zero_energy() -> None:
    assert set(EV_CONNECTOR_STATES) - {"CHARGING"} == set(grading.ZERO_ENERGY_STATES)
    assert set(ev_availability.REPORTED_STATES) == set(EV_CONNECTOR_STATES)


@pytest.mark.parametrize("state", ["AVAILABLE", "DISABLED"])
def test_available_and_disabled_count_as_known_status(state: str) -> None:
    day = {"c1": {"states": [(_t(8), _t(12), state), (_t(12), _t(16), "UNPLUGGED")], "meter": []},
           "c2": {"states": [(_t(8), _t(16), "UNPLUGGED")], "meter": []}}
    assert grading.covered_seconds(grading.status_known_spans(day), _t(8), _t(16)) == 8 * 3600
    foundation = {"content": {"components": [{"component_id": "c1", "component_type": "EV_CONNECTOR", "properties": [
        {"property_key": "ev-status-cadence", "value": "1", "unit": "min"}]}]}}
    row = {"role": "ev_connector_state", "asset_id": "A1", "connector_id": None, "value": state, "use": "SUPPORT",
           "quality": "GOOD", "reason": None, "source_time": _t(8), "sent_at": _t(8),
           "received_at": _t(8) + timedelta(seconds=1), "evidence_id": "e1"}
    assert ev_availability.status_spans(foundation, [("c1", "A1")], [row], _t(8), _t(9)) == {
        "A1": [(_t(8), _t(8, 1), state)]}
    # availability classification is unchanged: AVAILABLE is available, DISABLED unavailable
    assert ev_availability.CATEGORY[state] == (ev_availability.AVAILABLE if state == "AVAILABLE"
                                              else ev_availability.UNAVAILABLE)


# ---- Postgres: the producer's run_day on an 8-hour ordinary and fault day ------------------------------------

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_run_day_records_and_grades_the_declared_day(tmp_path) -> None:
    """D-E5.48 3(c), at test scale: two EV story days (S-7 `normal`, S `fault`) through the producer's own
    `run_day` (registered Draft, host, gateway subprocess, Batch V2, the EV worker, the exact selection) on one
    database, then the chain builder on the stored rows: COMPLETE on the 8 declared hours, the w205b kWh, and the
    session states and fault instant of the one-hour day."""
    import pg_harness
    import test_w205b_ev_replay_postgres as w205b
    from sqlalchemy import create_engine, text

    from assetops_backend.chain.composition import build_snapshot_builder

    seal_once = w205b.SEAL_ONCE
    pg_harness.fresh_database()
    days = _ev_days()[1:]
    install_at = days[0].start - timedelta(days=1)
    try:
        out = [dev.run_day(URL, tmp_path, day, install_at) for day in days]
        dev.publish_tariff(URL, install_at + timedelta(minutes=30))
    finally:
        w205b.SEAL_ONCE = seal_once
    for day, got in zip(days, out):
        lo, hi = dev.story_window(day)
        assert got["evidence_window"] == {"from": sd.iso(lo), "to": sd.iso(hi)}
        assert got["dispositions"].get("ACCEPTED", 0) > 0 and set(got["dispositions"]) == {"ACCEPTED"}, got
    engine = create_engine(URL)
    try:
        with engine.connect() as c:
            tenant, site = c.execute(text("SELECT s.tenant_id, s.id FROM site s WHERE s.site_code_key = 'ev-lab-001'")).one()
            sessions = c.execute(text(
                "SELECT DISTINCT ON (e.id) r.state, r.start_at, r.end_at, r.supported_kwh FROM ev_session e "
                "JOIN ev_session_revision r ON r.session_id = e.id WHERE e.site_id = :s "
                "ORDER BY e.id, r.revision_no DESC"), {"s": site}).all()
    finally:
        engine.dispose()
    got_sessions = sorted((r.start_at, r.end_at, r.state, f"{r.supported_kwh:.3f}") for r in sessions)
    want = []
    for day in days:
        lo = day.start
        if day.kind == "fault":
            want.append((lo + MINUTE, lo + 16 * MINUTE, "OBSERVED_ABORT", "15.000"))
        else:
            want.append((lo + MINUTE, lo + 31 * MINUTE, "COMPLETED", "30.000"))
    assert got_sessions == sorted(want)
    # the tariff publication enqueues the EV money recompute (0026 trigger); the prepare's ticks drain it with the
    # EV worker, as here
    from test_w206_ev_store_postgres import _dispose

    from assetops_backend.analytics.composition import build_ev_assessment_worker

    worker = build_ev_assessment_worker(URL)
    try:
        drained = worker.run_pending(tenant_id=tenant, site_id=site)
    finally:
        _dispose(worker)
    assert all(o.status == "DONE" for o in drained), [(o.status, o.error) for o in drained]
    import subprocess

    from demo_combined import TICK

    for _ in range(2):  # the prepare's scheduled tick (`demo_combined.TICK`) drains the money consequence
        done = subprocess.run([sys.executable, *TICK, "--no-prebuild"], capture_output=True, text=True, timeout=600,
                              env={**os.environ, "DATABASE_URL": URL}, cwd=str(ROOT))
        assert done.returncode == 0, (done.stdout[-2000:], done.stderr[-2000:])
    ref = SiteRef(tenant, site, "EV-LAB-001", "EV_CHARGING", "UTC")
    builder = build_snapshot_builder(URL, store=_Store())
    for day in days:
        [written] = builder.build(tenant, ref, day.start.date(), "charging_kwh")
        row = written.row
        assert (row.required_seconds, row.covered_seconds, row.grade) == (8 * 3600, 8 * 3600, grading.COMPLETE), row
        assert row.value["kwh"] in (KWH[day.kind], f"{KWH[day.kind]}.000"), row.value
        print("EV-HB", day.day, day.kind, row.grade, row.covered_seconds, row.value, row.money, len(drained))
        # the declared 0.30 USD/kWh: USD 9.00 on an ordinary day, USD 4.50 on the fault day (15 kWh), as before
        assert row.money is not None and row.money.get("currency") == "USD", row.money
        assert Decimal(str(row.money["amount"])) == {"normal": Decimal("9.00"), "fault": Decimal("4.50")}[day.kind]
    assert Counter(d.kind for d in days) == {"normal": 1, "fault": 1}
    # PB-1b: a whole-UTC-day EV read (the board link) shows the one analysed period, the recorded window; the fault
    # day's Finding is anchored inside it
    from assetops_backend.analytics.composition import build_ev_read_service

    reads = build_ev_read_service(URL)
    try:
        for day in days:
            lo, hi = dev.story_window(day)
            midnight = lo.replace(hour=0)
            snap, _ = reads.within(lambda c: reads.open_on(c, tenant, site, "EV-LAB-001", midnight,
                                                           midnight + timedelta(days=1), None))
            # the EV worker's job window closes 5 min after the recorded window (08:00-09:05 over 08:00-09:00 before
            # EV-HB); `widest_periods` lists it alone, so the shown period is 08:00-16:05
            assert (snap["lo"], snap["hi"]) == (lo, hi + 5 * MINUTE), (day.day, snap["lo"], snap["hi"])
    finally:
        reads.dispose()
    engine = create_engine(URL)
    try:
        with engine.connect() as c:
            anchors = c.execute(text("SELECT anchor_start FROM finding WHERE site_id = :s AND domain = 'ev_charging'"),
                                {"s": site}).scalars().all()
    finally:
        engine.dispose()
    fault = next(d for d in days if d.kind == "fault")
    assert anchors == [fault.start + MINUTE], anchors  # one Finding, on the interrupted session (start 08:01)
