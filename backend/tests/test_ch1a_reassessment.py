"""CH-1a L0 (fix round 1, M1): the input fingerprint names the selected analytic run or revision and the
pending flag, so a re-assessment over the same evidence, or a job completing, appends the next revision."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from assetops_backend.chain.builder import SnapshotBuilder
from assetops_backend.chain.composition import load_coverage_policy, load_operating_calendar
from assetops_backend.chain.grading import PENDING
from assetops_backend.chain.measure_impls import build_measure_set
from assetops_backend.chain.ports import SiteRef

UTC = timezone.utc
TENANT, SITE_ID, ASSET = uuid4(), uuid4(), str(uuid4())
DAY = date(2026, 10, 27)  # a Tuesday: EV's declared day
T0 = datetime(2026, 10, 27, 8, tzinfo=UTC)


class MemStore:
    def __init__(self) -> None:
        self.rows: dict = {}

    def latest(self, key):
        rows = self.rows.get(key)
        return None if not rows else (rows[-1].revision, rows[-1].input_fp)

    def append(self, row) -> None:
        self.rows.setdefault(row.key(), []).append(row)


class Reader:
    """Mutable stored state; only what the six adapters read."""

    def __init__(self) -> None:
        self.run, self.pending, self.hour_rev = "run-a", False, "rev-a"
        self.dispatch_sel = "sel-a"

    def foundation_assets(self, ctx, component_type):
        return [ASSET]

    def readings(self, ctx, roles, lo, hi):
        return [{"evidence_id": "ev-1", "role": roles[0], "asset_id": ASSET, "source_time": lo + timedelta(minutes=5),
                 "value": "4.1"}]

    def selected_windows(self, ctx, analytic_ids):
        lo = ctx.period_start_utc
        return [(lo, lo + timedelta(minutes=65), self.run)]

    def cold_temperature(self, ctx, lo, hi):
        return {"policy": {"room_asset_id": ASSET}, "gaps": [], "points": [{"evidence_id": "ev-1"}]}

    def cold_backup_chain(self, ctx, lo, hi):
        return {"state": "OBSERVED", "chains": [{"result": "OBSERVED_SUCCESS", "steps": [{"evidence_ids": ["ev-1"]}]}]}

    def ev_window(self, ctx, lo, hi):
        return {"selected": True, "meter": [(lo, lo + timedelta(minutes=30))], "status": [],
                "energy": {"complete_kwh": "5.000"}, "denominator": {"started": 1, "completed": 1},
                "money": None, "evidence_ids": ["ev-1"]}

    def renewable_pending(self, ctx):
        return self.pending

    def renewable_hours(self, ctx):  # CH-9: one measured daylight hour at the period start
        lo = ctx.period_start_utc
        return {"measured": True, "missing": [], "hours": [{"from": lo, "to": lo + timedelta(hours=1), "head": {
            "revision_id": self.hour_rev, "evidence_ids": ["ev-1"],
            "result": {"coverage": {"gaps": []},
                       "hour": {"decision": "ELIGIBLE", "headroom_kw": {"low": "1", "high": "2"}}}}}]}

    def dispatch_days(self, ctx):
        iv = {"id": "iv-1", "result": {"generator_asset_id": ASSET, "interval": {"first_on": ctx.period_start_utc},
                                        "portions_minutes": {"candidate": 10, "indeterminate": 0}}}
        return [{"status": "CURRENT", "selection": {"run_id": self.dispatch_sel}, "intervals": [iv]}]

    def run_evidence_intervals(self, ctx, run_ids):
        lo = ctx.period_start_utc
        return [("ev-1", lo, lo + timedelta(hours=1))]

    def pending_jobs(self, ctx, domains):
        return self.pending


def _build(reader, store, measure: str, site_code: str, site_type: str):
    builder = SnapshotBuilder(store, build_measure_set(reader), load_coverage_policy(), load_operating_calendar())
    return builder.build(TENANT, SiteRef(TENANT, SITE_ID, site_code, site_type, "UTC"), DAY, measure)


CASES = [
    ("avoidable_gen_min", "KOBO-001", "MINIGRID", "dispatch_sel", "sel-b"),
    ("daylight_headroom_kw", "KOBO-001", "MINIGRID", "hour_rev", "rev-b"),
    ("chamber_temp_c", "COLD-LAB-001", "COLDCHAIN", "run", "run-b"),
    ("backup_start_chain", "COLD-LAB-001", "COLDCHAIN", "run", "run-b"),
    ("charging_kwh", "EV-LAB-001", "EV_CHARGING", "run", "run-b"),
]


@pytest.mark.parametrize(("measure", "code", "kind", "attr", "new"), CASES, ids=[c[0] for c in CASES])
def test_reassessment_over_same_evidence_adds_a_revision(measure, code, kind, attr, new) -> None:
    reader, store = Reader(), MemStore()
    first = _build(reader, store, measure, code, kind)
    assert [w.written for w in first] == [True] and first[0].row.revision == 1
    assert [w.written for w in _build(reader, store, measure, code, kind)] == [False]  # unchanged: nothing written
    setattr(reader, attr, new)  # same evidence ids, a different selected run / revision
    again = _build(reader, store, measure, code, kind)
    assert [w.written for w in again] == [True] and again[0].row.revision == 2


@pytest.mark.parametrize(("measure", "code", "kind"), [c[:3] for c in CASES if c[0] != "charging_kwh"] + [
    ("charging_kwh", "EV-LAB-001", "EV_CHARGING")], ids=[c[0] for c in CASES])
def test_pending_then_completed_with_the_same_evidence_adds_a_revision(measure, code, kind) -> None:
    reader, store = Reader(), MemStore()
    reader.pending = True
    first = _build(reader, store, measure, code, kind)
    assert first[0].row.grade == PENDING and first[0].row.revision == 1
    reader.pending = False  # the job completed; the evidence ids are exactly the ones already counted
    done = _build(reader, store, measure, code, kind)
    assert [w.written for w in done] == [True] and done[0].row.revision == 2 and done[0].row.grade != PENDING


def test_cold_values_declare_the_assessed_window_basis() -> None:
    reader, store = Reader(), MemStore()
    for measure in ("chamber_temp_c", "backup_start_chain"):
        row = _build(reader, store, measure, "COLD-LAB-001", "COLDCHAIN")[0].row
        assert row.value["basis"] == "assessed_window"
