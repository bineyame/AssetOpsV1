"""PB-3 (D-E5.29 card, `.agent/architect-answer-non-kobo-sites-2026-11-10.md` PB-3): EV event-driven grading.

For a metered-when-charging measure (`charging_kwh`), covered time is connector-status-known time: a connector
whose reported state carries no energy (unplugged, plugged, authorizing, faulted) is known at zero energy; a charging
connector is known only where a meter interval covers it. The Site is covered where every connector is known. The
basis is declared per measure in `config/chain/coverage-policy-v1.json`; every other measure keeps meter/interval
coverage.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import pytest

from assetops_backend.analytics import ev_availability
from assetops_backend.chain import grading
from assetops_backend.chain.builder import SnapshotBuilder
from assetops_backend.chain.composition import load_coverage_policy, load_operating_calendar
from assetops_backend.chain.measure_impls import ChargingEnergy
from assetops_backend.chain.policy import ChainConfigError
from assetops_backend.chain.ports import DayCtx, InputSet, SiteRef

UTC = timezone.utc
TUE = date(2026, 11, 10)  # a Tuesday: EV-LAB-001 declares TUE 08:00-16:00


def _t(h: int, m: int = 0) -> datetime:
    return datetime(2026, 11, 10, h, m, tzinfo=UTC)


IDLE_DAY = {  # one ordinary session on c1, both connectors report their state all day
    "c1": {"states": [(_t(8), _t(9), "UNPLUGGED"), (_t(9), _t(9, 1), "PLUGGED"), (_t(9, 1), _t(9, 31), "CHARGING"),
                      (_t(9, 31), _t(16), "UNPLUGGED")],
           "meter": [(_t(9, 1), _t(9, 16)), (_t(9, 16), _t(9, 31))]},
    "c2": {"states": [(_t(8), _t(16), "UNPLUGGED")], "meter": []},
}


def test_idle_known_status_counts_as_zero_energy_coverage() -> None:
    spans = grading.status_known_spans(IDLE_DAY)
    assert grading.covered_seconds(spans, _t(8), _t(16)) == 8 * 3600
    # the meter alone covers 30 min of the 8 h: LOW on meter-interval time, COMPLETE on status-known time
    meter = [s for c in IDLE_DAY.values() for s in c["meter"]]
    policy = load_coverage_policy()
    assert grading.classify_day(True, 8 * 3600, grading.covered_seconds(meter, _t(8), _t(16)), False,
                                policy.bands, 0.8) == grading.LOW
    assert grading.classify_day(True, 8 * 3600, grading.covered_seconds(spans, _t(8), _t(16)), False,
                                policy.bands, 0.8) == grading.COMPLETE


def test_charging_without_a_meter_interval_is_not_covered() -> None:
    day = {"c1": {"states": [(_t(8), _t(9), "CHARGING"), (_t(9), _t(16), "UNPLUGGED")], "meter": [(_t(8), _t(8, 30))]},
           "c2": {"states": [(_t(8), _t(16), "UNPLUGGED")], "meter": []}}
    assert grading.covered_seconds(grading.status_known_spans(day), _t(8), _t(16)) == 7 * 3600 + 30 * 60


def test_site_is_covered_only_where_every_connector_is_known() -> None:
    day = {"c1": {"states": [(_t(8), _t(16), "UNPLUGGED")], "meter": []},
           "c2": {"states": [(_t(8), _t(10), "FAULTED"), (_t(12), _t(16), "UNPLUGGED")], "meter": []}}
    assert grading.covered_seconds(grading.status_known_spans(day), _t(8), _t(16)) == 6 * 3600
    unknown = {"c1": {"states": [(_t(8), _t(16), "UNKNOWN")], "meter": []}}
    assert grading.status_known_spans(unknown) == []
    assert grading.status_known_spans({}) == []


def test_shipped_policy_declares_status_known_for_charging_only() -> None:
    policy = load_coverage_policy()
    assert policy.basis_for("charging_kwh") == grading.BASIS_CONNECTOR_STATUS_KNOWN
    for key in ("productive_kwh", "daylight_headroom_kw", "critical_served", "avoidable_gen_min", "chamber_temp_c",
                "backup_start_chain"):
        assert policy.basis_for(key) == grading.BASIS_INTERVALS


def test_policy_rejects_an_unknown_basis(tmp_path) -> None:
    payload = {"schema": "coverage-policy", "version": 1, "policy_version": "p/1",
               "bands": {"complete": 0.8, "partial": 0.25}, "objective_min_complete_days": 3,
               "share_of_expected_days": None, "measures": {"charging_kwh": {"covered": "sometimes"}}}
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ChainConfigError):
        load_coverage_policy(path)


def test_fingerprint_moves_only_for_a_declared_basis() -> None:
    base = grading.input_fp(["a"], False, "p/1", "c/1", 1, "k@1")
    assert grading.input_fp(["a"], False, "p/1", "c/1", 1, "k@1", coverage_basis=grading.BASIS_INTERVALS) == base
    assert grading.input_fp(["a"], False, "p/1", "c/1", 1, "k@1",
                            coverage_basis=grading.BASIS_CONNECTOR_STATUS_KNOWN) != base


class _Store:
    def __init__(self) -> None:
        self.rows = []

    def latest(self, key):
        return None

    def append(self, row) -> None:
        self.rows.append(row)


class _Adapter:
    key = "ev.charging_energy@1"

    def __init__(self, status) -> None:
        self.status = status

    def subjects(self, ctx):
        return ["SITE"]

    def inputs(self, ctx, subject_ref):
        meter = [s for c in IDLE_DAY.values() for s in c["meter"]]
        return InputSet(("ev-1",), meter, False, None, self.status)

    def measure(self, ctx, subject_ref, inputs):
        return {"kwh": "30"}

    def money(self, ctx, subject_ref, value):
        return None


SITE = SiteRef(UUID(int=1), UUID(int=2), "EV-LAB-001", "EV_CHARGING", "UTC")


def test_builder_grades_charging_on_status_known_time() -> None:
    store = _Store()
    builder = SnapshotBuilder(store, {"ev.charging_energy@1": _Adapter(IDLE_DAY)}, load_coverage_policy(),
                              load_operating_calendar())
    [written] = builder.build(SITE.tenant_id, SITE, TUE, "charging_kwh")
    assert (written.row.required_seconds, written.row.covered_seconds, written.row.grade) == (
        8 * 3600, 8 * 3600, grading.COMPLETE)
    with pytest.raises(ValueError):  # a status-known measure whose adapter carries no connector status
        SnapshotBuilder(_Store(), {"ev.charging_energy@1": _Adapter(None)}, load_coverage_policy(),
                        load_operating_calendar()).build(SITE.tenant_id, SITE, TUE, "charging_kwh")


class _Reader:
    def selected_windows(self, ctx, analytics):
        return [(_t(8), _t(16), "run-1")]

    def ev_window(self, ctx, lo, hi):
        return {"selected": True, "meter": [], "status": [], "connectors": IDLE_DAY, "energy": {"complete_kwh": "30"},
                "denominator": {"started": 1, "completed": 1}, "money": None, "evidence_ids": ["e-1"]}

    def pending_jobs(self, ctx, domains):
        return False


def test_charging_adapter_carries_connector_status() -> None:
    ctx = DayCtx(tenant_id=SITE.tenant_id, site_id=SITE.site_id, site_code=SITE.site_code, domain=SITE.site_type,
                 tz="UTC", local_day=TUE, period_start_utc=_t(8), period_end_utc=_t(16), known_at=None)
    inputs = ChargingEnergy(_Reader()).inputs(ctx, "SITE")
    assert set(inputs.connector_status) == {"c1", "c2"}
    assert grading.covered_seconds(grading.status_known_spans(inputs.connector_status), _t(8), _t(16)) == 8 * 3600


def _row(value, at, evidence):
    return {"role": "ev_connector_state", "asset_id": "A1", "connector_id": None, "value": value, "use": "SUPPORT",
            "quality": "GOOD", "reason": None, "source_time": at, "sent_at": at, "received_at": at + timedelta(seconds=1),
            "evidence_id": evidence}


def test_status_spans_keep_the_reported_state_including_plugged_and_charging() -> None:
    foundation = {"content": {"components": [{"component_id": "c1", "component_type": "EV_CONNECTOR", "properties": [
        {"property_key": "ev-status-cadence", "value": "1", "unit": "min"}]}]}}
    rows = [_row("UNPLUGGED", _t(8), "e1"), _row("PLUGGED", _t(8, 1), "e2"), _row("CHARGING", _t(8, 2), "e3"),
            _row("SOMETHING", _t(8, 3), "e4")]
    spans = ev_availability.status_spans(foundation, [("c1", "A1")], rows, _t(8), _t(9))
    assert spans == {"A1": [(_t(8), _t(8, 1), "UNPLUGGED"), (_t(8, 1), _t(8, 2), "PLUGGED"),
                            (_t(8, 2), _t(8, 3), "CHARGING"), (_t(8, 3), _t(8, 4), "UNKNOWN")]}
    assert ev_availability.status_spans(None, [("c1", "A1")], rows, _t(8), _t(9)) == {}


# --- Postgres: the registered `complete` EV replay through the real read service --------------------------------

from ev_depth_cases import HI, LO, URL, chain, settled  # noqa: E402,F401


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
def test_complete_replay_is_status_known_for_its_whole_window(chain) -> None:  # noqa: F811
    """The stored `complete` run (c1 charges 08:01-08:31, c2 unplugged; a state report every minute): every second of
    the window is energy-known (PLUGGED/AUTHORIZING and UNPLUGGED at zero energy, CHARGING under its meter), and on
    this window the PB-3 coverage equals the prior meter ∪ known-availability coverage (no stored value moves)."""
    from assetops_backend.analytics.composition import build_ev_read_service
    from assetops_backend.chain.adapters.postgres_chain_inputs import instant

    built = settled(chain, "complete")
    reads = build_ev_read_service(URL)
    try:
        def work(c):
            snap, _ = reads.open_on(c, built.tenant_id, built.site_id, built.site_code, LO, HI, None)
            return (snap, ev_availability.status_spans_on(reads, c, snap),
                    ev_availability.availability_on(reads, c, snap), reads.accepted_on(c, snap))
        snap, spans, body, accepted = reads.within(work)
    finally:
        reads.dispose()
    assert snap["state"] == "CURRENT" and len(spans) == 2
    states = {s for rows in spans.values() for _a, _b, s in rows}
    assert {"UNPLUGGED", "CHARGING"} <= states and "UNKNOWN" not in states
    connectors = {asset: {"states": rows, "meter": [
        (r["interval_start"], r["interval_end"]) for r in accepted if r["role"] == "ev_connector_energy"
        and r["use"] == "SUPPORT" and r["interval_start"] is not None
        and str(r.get("asset_id")).lower() == str(asset).lower()]} for asset, rows in spans.items()}
    window = int((HI - LO).total_seconds())
    assert grading.covered_seconds(grading.status_known_spans(connectors), LO, HI) == window
    prior = [(r["interval_start"], r["interval_end"]) for r in accepted if r["role"] == "ev_connector_energy"
             and r["use"] == "SUPPORT" and r["interval_start"] is not None] + [
        (instant(x["from"]), instant(x["to"])) for row in body["connectors"] for x in row["spans"]
        if x["state"] != ev_availability.UNKNOWN]
    assert grading.covered_seconds(prior, LO, HI) == window
