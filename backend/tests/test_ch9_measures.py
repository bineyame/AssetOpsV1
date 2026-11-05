"""CH-9 L0: the `daylight_headroom_kw` and `critical_served` adapters over a fake chain reader (§9 R5/R9, CH9-R2
Q2/Q5/Q7). Coverage is what the grader reads; the value is what the board and the thread read."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from assetops_backend.chain.measure_impls import CriticalServed, RenewableHeadroom
from assetops_backend.chain.measures import MEASURES, measures_for
from assetops_backend.chain.ports import DayCtx

UTC = timezone.utc
DAY = date(2026, 10, 20)
LO = datetime(2026, 10, 19, 21, tzinfo=UTC)  # Addis local midnight
CTX = DayCtx(uuid4(), uuid4(), "KOBO-001", "MINIGRID", "Africa/Addis_Ababa", DAY, LO, LO + timedelta(days=1), None)


def _h(n: int) -> tuple[datetime, datetime]:
    return LO + timedelta(hours=n), LO + timedelta(hours=n + 1)


def _seconds(spans) -> float:
    return sum((b - a).total_seconds() for a, b in spans)


class Reader:
    def __init__(self, hours=(), missing=(), service=()) -> None:
        self.hours, self.missing, self.service = list(hours), list(missing), list(service)

    def renewable_pending(self, ctx):
        return False

    def pending_jobs(self, ctx, domains):
        return False

    def renewable_hours(self, ctx):
        return {"measured": True, "hours": self.hours, "missing": self.missing}

    def service_hours(self, ctx):
        return self.service


def _renewable(n: int, decision: str | None, low="5", high="7", gaps=()) -> dict:
    a, b = _h(n)
    return {"from": a, "to": b, "head": {"revision_id": f"r{n}", "evidence_ids": [f"e{n}"], "result": {
        "coverage": {"gaps": list(gaps)}, "hour": {"decision": decision, "headroom_kw": {"low": low, "high": high}}}}}


def test_specs() -> None:
    assert "noon_headroom_kw" not in MEASURES
    d, c = MEASURES["daylight_headroom_kw"], MEASURES["critical_served"]
    assert (d.period, d.threshold, d.adapter) == ("operating_hours", 1.0, "mini.daylight_headroom@1")
    assert (c.period, c.threshold, c.adapter, c.subject_kind) == ("operating_hours", 0.8, "mini.critical_served@1",
                                                                   "SITE")
    assert {"daylight_headroom_kw", "critical_served"} <= {m.key for m in measures_for("MINIGRID")}


def test_daylight_headroom_folds_its_hours() -> None:
    a = RenewableHeadroom(Reader([_renewable(6, "ELIGIBLE", "5", "7"), _renewable(7, "ELIGIBLE", "4", "9"),
                                  _renewable(8, "EXCLUDED", "1", "2")]))
    got = a.inputs(CTX, "SITE")
    assert _seconds(got.covered) == 24 * 3600  # every period hour covered: night hours are covered, not daylight
    assert a.measure(CTX, "SITE", got) == {"low_kw": "4", "high_kw": "7", "decision": "ELIGIBLE", "window_hours": 2}
    assert "revision:r8" in got.ids and "e6" in got.ids


def test_daylight_headroom_missing_hour_is_uncovered() -> None:
    # A missing hour (not fully covered by pv readings) and a daylight hour with no selected revision both leave
    # the period short, so the day grades below COMPLETE (threshold 1.0) and the value names no headroom.
    a = RenewableHeadroom(Reader([_renewable(6, "ELIGIBLE"), {"from": _h(7)[0], "to": _h(7)[1], "head": None}],
                                 missing=[_h(9)]))
    got = a.inputs(CTX, "SITE")
    assert _seconds(got.covered) == 22 * 3600
    assert a.measure(CTX, "SITE", got)["decision"] is None


def test_daylight_headroom_conflict_and_no_heads() -> None:
    a = RenewableHeadroom(Reader([_renewable(6, "ELIGIBLE"), _renewable(7, "CONFLICT")]))
    out = a.measure(CTX, "SITE", a.inputs(CTX, "SITE"))
    assert (out["decision"], out["result_state"]) == (None, "CONFLICT")
    empty = RenewableHeadroom(Reader()).inputs(CTX, "SITE")
    assert (empty.covered, empty.payload) == ([], None)


def _row(role: str, code: str, label: str, delivered, assessment: str, request: str, unserved="absent",
         gaps=()) -> dict:
    """One stored `mini_service` load row in the shape of a real polish head (`load-clinic` / `load-mill` /
    `load-res`, 2026-10 Kobo). `unserved="absent"` is a `mini-service/1` row, which has no such key."""
    row = {"role": role, "asset_id": str(uuid4()), "asset_code": code, "load_label": label,
           "delivered_kw": delivered, "assessment": assessment, "requested_evidence_state": request,
           "coverage": {"gaps": list(gaps), "source_count": 1, "observed_seconds": 3600, "required_seconds": 3600},
           "evidence_ids": [str(uuid4())]}
    if unserved != "absent":
        row["unserved_kwh"] = unserved
    return row


def _clinic(delivered=6, assessment="SUPPORTED", unserved=0.5, gaps=()) -> dict:
    request = "ACCEPTED" if assessment == "SUPPORTED" else "MISSING"
    return _row("CRITICAL", "load-clinic", "Health clinic", delivered, assessment, request, unserved, gaps)


def _unclassified() -> list[dict]:
    # The real shape: measured delivery, no request evidence, so UNKNOWN with a null unserved figure.
    return [_row("UNCLASSIFIED", "load-mill", "Grain mill", 16.333333333333332, "UNKNOWN", "MISSING", None),
            _row("UNCLASSIFIED", "load-res", "Residential feeder", 14, "UNKNOWN", "MISSING", None)]


def _service(n: int, rows: list[dict] | None = None) -> dict:
    a, b = _h(n)
    rows = [_clinic(), *_unclassified()] if rows is None else rows
    # The all-load card is null (not every row is SUPPORTED) and the critical card disagrees with the row on purpose:
    # the adapter must read neither.
    result = {"status": "LIMITED", "cards": {"delivered_load_kw": 36.33, "interruptions_seen": None,
                                             "critical_delivered_kw": 99, "unserved_kwh": None},
              "critical_delivered_coverage": None, "rows": rows, "limitations": [], "coverage": {"gaps": []}}
    return {"from": a, "to": b, "head": {"revision_id": f"s{n}", "evidence_ids": [f"v{n}"], "result": result}}


def test_critical_served_supported_critical_with_unknown_unclassified_is_counted() -> None:
    # CH9-R4 F1, the key case: the CRITICAL row SUPPORTED, the UNCLASSIFIED rows UNKNOWN with no request.
    a = CriticalServed(Reader(service=[_service(n) for n in range(24)]))
    got = a.inputs(CTX, "SITE")
    assert _seconds(got.covered) == 24 * 3600
    assert a.measure(CTX, "SITE", got) == {"served_kwh": "144", "demand_kwh": "156.0", "unserved_kwh": "12.0"}


def test_critical_served_truth_table() -> None:
    gap = {"from": (_h(3)[0] + timedelta(minutes=30)).isoformat(), "to": _h(3)[1].isoformat()}
    unc = _unclassified()
    hours = [_service(n) for n in range(24)]
    hours[1] = {"from": _h(1)[0], "to": _h(1)[1], "head": None}                 # no service head: uncovered
    hours[2] = _service(2, [_clinic(assessment="LIMITED", unserved=None), *unc])  # CRITICAL LIMITED: uncovered
    hours[3] = _service(3, [_clinic(gaps=[gap]), *unc])                          # half an hour of row coverage
    hours[4] = _service(4, [_clinic(assessment="UNKNOWN", unserved=None), *unc])  # CRITICAL UNKNOWN: uncovered
    hours[5] = _service(5, [_clinic(), _clinic(), *unc])                          # two CRITICAL rows: uncovered
    hours[6] = _service(6, unc)                                                    # no CRITICAL row: uncovered
    hours[7] = _service(7, [_clinic(unserved="absent"), *unc])                    # a `/1` head: uncovered
    hours[8] = _service(8, [_clinic(unserved=None), *unc])                        # unserved not stated: uncovered
    a = CriticalServed(Reader(service=hours))
    got = a.inputs(CTX, "SITE")
    assert _seconds(got.covered) == (16 + 0.5) * 3600
    out = a.measure(CTX, "SITE", got)
    # 17 counted hours: served 6 kWh and unserved 0.5 kWh each; demand = served + unserved.
    assert out == {"served_kwh": "102", "demand_kwh": "110.5", "unserved_kwh": "8.5"}
    assert "revision:s0" in got.ids and not {"revision:s1", "revision:s2", "revision:s7"} & set(got.ids)


def test_critical_served_eight_hour_day_is_partial_share() -> None:
    # CH9-R2 Q6: an 8-hour story day covers 8/24 of Kobo's declared 24 h, below the 0.8 threshold.
    a = CriticalServed(Reader(service=[_service(n) for n in range(6, 14)]))
    got = a.inputs(CTX, "SITE")
    assert _seconds(got.covered) / (24 * 3600) < MEASURES["critical_served"].threshold
    assert CriticalServed(Reader(service=[])).inputs(CTX, "SITE").payload is None
