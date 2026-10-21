"""W4-02 unit 5: pure read rules and router refusals (`D-2026-10-20-w4-02-buildspec` closure 1 Q4, Q10-Q12, Q31,
Q33; closure 4 S1, S6, N7; q6 ruling 1). The Postgres reads are in `test_w402_reads_postgres.py`."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.mini_depth.inputs import local_noon
from assetops_backend.mini_depth import rules
from assetops_backend.mini_depth.read import (
    MiniReadRefused,
    MiniReadUnavailable,
    _Head,
    _Hour,
    aggregate_job,
    aggregate_state,
    check_lineage,
    compose_renewable,
    hour_windows,
    limit_claim,
    links,
    renewable_envelope,
)
from assetops_backend.mini_depth_api import build_mini_depth_router
from assetops_backend.sites.ports import SiteStoreUnavailable

ZONE = "Africa/Nairobi"
DAYS = [date(2026, 10, d) for d in range(6, 11)]
LO = datetime(2026, 10, 7, 9, tzinfo=timezone.utc)


def _midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc) - timedelta(hours=3)


def _hour(decision: str, low: float = 18, high: float = 20) -> dict:
    positive = decision == "ELIGIBLE"
    return {"hour": {"capability_kw": {"low": 41, "high": 43} if positive else None,
                     "used_kw": 21 if positive else None,
                     "headroom_kw": {"low": low, "high": high} if positive else None, "decision": decision}}


def test_hour_windows_one_hour_and_renewable_days() -> None:
    assert [w for _, w in hour_windows("service", LO, LO + timedelta(hours=1), ZONE)][0].start == LO
    windows = hour_windows("renewable", _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)), ZONE)
    assert [d for d, _ in windows] == DAYS and all(w == local_noon(d, ZONE) for d, w in windows)
    assert len(hour_windows("renewable", _midnight(DAYS[0]), _midnight(DAYS[1]), ZONE)) == 1
    for domain, lo, hi, zone in [
        ("fuel", LO + timedelta(minutes=30), LO + timedelta(minutes=90), ZONE),  # not a local clock hour
        ("fuel", LO, LO + timedelta(hours=2), ZONE),  # a day or two hours is not one hour (closure 1 Q4)
        ("backup", LO, LO, ZONE),
        ("renewable", _midnight(DAYS[0]), _midnight(DAYS[0]) + timedelta(days=6), ZONE),  # six days
        ("renewable", LO, LO + timedelta(days=1), ZONE),  # not local midnight
        ("service", LO, LO + timedelta(hours=1), None),  # no pinned zone: never guess UTC (S8)
        ("service", LO, LO + timedelta(hours=1), "Not/AZone"),
    ]:
        with pytest.raises(MiniReadRefused) as refused:
            hour_windows(domain, lo, hi, zone)
        assert refused.value.code == "INVALID_WINDOW", (domain, lo, hi, zone)


def test_hour_windows_nonexistent_local_noon_refuses() -> None:
    # Pacific/Apia skipped 30 December 2011 entirely: that local day has no noon.
    lo = datetime(2011, 12, 29, 10, tzinfo=timezone.utc)  # local midnight 30 Dec does not exist either
    with pytest.raises(MiniReadRefused):
        hour_windows("renewable", lo, lo + timedelta(days=1), "Pacific/Apia")


def test_compose_renewable_status_and_counts() -> None:
    w = [(d, local_noon(d, ZONE)) for d in DAYS]
    five = [(d, x, _hour("EXCLUDED" if i == 0 else "ELIGIBLE", 10 + i, 12 + i)) for i, (d, x) in enumerate(w)]
    supported = compose_renewable(five)
    assert supported["status"] == "SUPPORTED"
    assert supported["cards"] == {"capability_kw": {"low": 41, "high": 43}, "used_kw": {"low": 21, "high": 21},
                                  "headroom_kw": {"low": 11, "high": 16}, "eligible_days": 4, "assessed_days": 5}
    limited = compose_renewable([*five[:2], (five[2][0], five[2][1], _hour("LIMITED")), *five[3:]])
    assert limited["status"] == "LIMITED" and limited["cards"]["assessed_days"] == 4
    conflict = compose_renewable([*five[:4], (five[4][0], five[4][1], _hour("CONFLICT"))])
    assert conflict["status"] == "LIMITED"
    missing = compose_renewable([*five[:4], (five[4][0], five[4][1], None)])
    assert missing["status"] == "UNKNOWN" and missing["cards"]["assessed_days"] == 4
    nothing = compose_renewable([(d, x, None) for d, x in w])
    assert nothing["status"] == "UNKNOWN"
    assert nothing["cards"] == dict.fromkeys(("capability_kw", "used_kw", "headroom_kw", "eligible_days",
                                              "assessed_days"))


class _Reader:
    def __init__(self, error: Exception | None = None) -> None:
        self.error, self.calls = error, []

    def read(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return {"domain": kwargs["domain"], "status": "UNKNOWN"}


def _client(reader, site_type="MINIGRID", access=lambda r, c: None, outage=False):
    site = SimpleNamespace(id=uuid4(), site_code="MG-1", site_type=site_type, timezone=ZONE)

    def imported(code):
        if outage:
            raise SiteStoreUnavailable("down")
        return site if code == "MG-1" else None

    registry = SimpleNamespace(tenant=lambda: SimpleNamespace(id=uuid4()), imported=imported)
    app = FastAPI()
    app.include_router(build_mini_depth_router(reader, registry, access))  # type: ignore[arg-type]
    return TestClient(app)


Q = {"from": "2026-10-07T09:00:00Z", "to": "2026-10-07T10:00:00Z"}
URL = "/api/sites/MG-1/performance/mini/service"


@pytest.mark.parametrize(("case", "status", "code"), [
    ("unauthenticated", 401, "UNAUTHENTICATED"),
    ("forbidden", 403, "SITE_SCOPE_FORBIDDEN"),
    ("unknown_site", 404, "SITE_NOT_FOUND"),
    ("bad_window", 422, "INVALID_WINDOW"),
    ("store_down", 503, "MINI_DEPTH_STORE_UNAVAILABLE"),
])
def test_401_403_404_422_503(case, status, code) -> None:
    reader = _Reader(MiniReadUnavailable("x") if case == "store_down" else None)
    access = {"unauthenticated": lambda r, c: 401, "forbidden": lambda r, c: 403}.get(case, lambda r, c: None)
    client = _client(reader, access=access)
    url = "/api/sites/OTHER/performance/mini/service" if case == "unknown_site" else URL
    params = {"from": "nope", "to": Q["to"]} if case == "bad_window" else Q
    response = client.get(url, params=params)
    assert response.status_code == status and response.json()["detail"]["code"] == code
    assert "rows" not in response.json() and "total_count" not in response.json()
    if status == 401:
        assert response.headers["WWW-Authenticate"] == "Bearer"
    if status in (401, 403, 404, 422):
        assert reader.calls == []  # refused before any mini store read


def test_scope_outage_is_503_not_404() -> None:
    response = _client(_Reader(), outage=True).get(URL, params=Q)
    assert response.status_code == 503 and response.json()["detail"]["code"] == "MINI_DEPTH_STORE_UNAVAILABLE"


def test_refusals_from_reader_and_missing_reader() -> None:
    for error, code in [(MiniReadRefused("INVALID_KNOWN_AT"), "INVALID_KNOWN_AT"),
                        (MiniReadRefused("INVALID_WINDOW"), "INVALID_WINDOW")]:
        response = _client(_Reader(error)).get(URL, params=Q)
        assert response.status_code == 422 and response.json()["detail"]["code"] == code
    assert _client(_Reader()).get(URL, params={"from": Q["from"]}).status_code == 422
    unconfigured = _client(None)
    assert unconfigured.get(URL, params=Q).status_code == 503  # no reader: 503, never an empty 200
    assert unconfigured.get("/api/sites/MG-1/performance/mini/capabilities").json() == []
    assert _client(_Reader()).get("/api/sites/MG-1/performance/mini/solar", params=Q).status_code == 404


def test_offset_input_is_normalized_to_utc() -> None:
    reader = _Reader()
    response = _client(reader).get(URL, params={"from": "2026-10-07T12:00:00+03:00", "to": Q["to"]})
    assert response.status_code == 200
    assert reader.calls[0]["lo"] == datetime(2026, 10, 7, 9, tzinfo=timezone.utc)


@pytest.mark.parametrize("site_type", ["COLDCHAIN", "EV_CHARGING"])
def test_non_minigrid_site_is_unknown_role_unsupported(site_type) -> None:
    reader = _Reader()
    client = _client(reader, site_type=site_type)
    for params in (Q, {"from": "garbage"}):
        body = client.get(URL, params=params).json()
        assert body["status"] == "UNKNOWN" and [x["code"] for x in body["limitations"]] == ["SITE_ROLE_UNSUPPORTED"]
        assert body["rows"] == [] and body["currentness"]["state"] == "UNKNOWN"
    assert reader.calls == []
    assert client.get("/api/sites/MG-1/performance/mini/capabilities").json() == []


def test_minigrid_capabilities_order() -> None:
    body = _client(_Reader()).get("/api/sites/MG-1/performance/mini/capabilities").json()
    assert body == [{"id": "service", "display_name": "Service"}, {"id": "fuel", "display_name": "Fuel"},
                    {"id": "renewable", "display_name": "Renewable"}, {"id": "backup", "display_name": "Backup"}]


# --- q9 rulings (`.agent/W4-02-build-spec.md` "Run 9 rulings (q9)") ----------------------------------------------


def test_q9_1_explicit_window_refusals() -> None:
    reader = _Reader()
    client = _client(reader)
    for params in ({}, {"to": Q["to"]}, [("from", Q["from"]), ("from", Q["from"]), ("to", Q["to"])],
                   {"from": "2026-10-07T09:00:00", "to": Q["to"]}, {"from": Q["from"], "to": "null"}):
        response = client.get(URL, params=params)
        assert response.status_code == 422, params
        assert response.json() == {"detail": {"code": "INVALID_WINDOW", "message": (
            "Select a valid complete site-local hour or one to five site-local days.")}}
    for known in ("garbage", "2026-10-07T09:00:00"):
        response = client.get(URL, params={**Q, "known_at": known})
        assert response.status_code == 422 and response.json()["detail"]["code"] == "INVALID_KNOWN_AT"
    response = client.get(URL, params=[("from", Q["from"]), ("to", Q["to"]), ("known_at", Q["to"]),
                                       ("known_at", Q["to"])])
    assert response.status_code == 422 and response.json()["detail"]["code"] == "INVALID_KNOWN_AT"
    assert reader.calls == []
    # An offset-normalized hour and one-to-five complete local days are the only accepted shapes.
    assert hour_windows("service", LO, LO + timedelta(hours=1), ZONE)[0][1].start == LO
    for n in range(1, 6):
        assert len(hour_windows("renewable", _midnight(DAYS[0]), _midnight(DAYS[0] + timedelta(days=n)), ZONE)) == n
    for lo, hi in ((LO, LO), (LO + timedelta(hours=1), LO), (LO, LO + timedelta(minutes=59))):
        with pytest.raises(MiniReadRefused):
            hour_windows("service", lo, hi, ZONE)


def test_q9_4_positive_claim_downgrade() -> None:
    assert limit_claim("SUPPORTED", "SOURCE_MEASURED", "CURRENT", []) == ("SUPPORTED", [])
    assert limit_claim("SUPPORTED", "SOURCE_MEASURED", "HISTORICAL", []) == ("SUPPORTED", [])  # no downgrade
    for cls, state, codes in [("UNKNOWN", "CURRENT", ["SOURCE_CLASS_UNKNOWN"]),
                              ("MIXED", "CURRENT", ["SOURCE_CLASS_MIXED"]),
                              ("SOURCE_MEASURED", "PENDING_RECOMPUTE", ["RECOMPUTE_PENDING"]),
                              ("SOURCE_MEASURED", "STALE_SOURCE", ["SOURCE_STALE"])]:
        status, limitations = limit_claim("SUPPORTED", cls, state, [])
        assert status == "LIMITED" and [x["code"] for x in limitations] == codes, (cls, state)
    status, both = limit_claim("SUPPORTED", "MIXED", "STALE_SOURCE",
                               [{"code": "SOURCE_STALE", "evidence_ids": ["b", "a"]},
                                {"code": "SOURCE_STALE", "evidence_ids": ["a", "c"]}])
    assert status == "LIMITED"
    codes = [x["code"] for x in both]
    assert sorted(codes, key=rules.LIMITATION_ORDER.index) == codes and len(codes) == len(set(codes)) == 2
    assert next(x for x in both if x["code"] == "SOURCE_STALE")["evidence_ids"] == ["a", "b", "c"]
    # An absent selection stays UNKNOWN, never LIMITED by a fabricated claim.
    assert limit_claim("UNKNOWN", None, "UNKNOWN", [])[0] == "UNKNOWN"
    assert limit_claim("UNKNOWN", "MIXED", "PENDING_RECOMPUTE", [])[0] == "UNKNOWN"


def test_q9_5_job_and_currentness_aggregates() -> None:
    assert aggregate_job(["SETTLED", "NONE"]) == "NONE" and aggregate_state(["CURRENT", "UNKNOWN"]) == "UNKNOWN"
    assert aggregate_job(["FAILED", "PENDING", "SETTLED"]) == "FAILED"
    assert aggregate_job(["PENDING", "LEASED"]) == "LEASED" and aggregate_job(["SETTLED"] * 3) == "SETTLED"
    assert aggregate_state(["CURRENT", "STALE_SOURCE", "PENDING_RECOMPUTE"]) == "PENDING_RECOMPUTE"
    assert aggregate_state(["HISTORICAL", "STALE_SOURCE"]) == "STALE_SOURCE"
    assert aggregate_state(["HISTORICAL", "CURRENT"]) == "HISTORICAL"


def _z(at: datetime) -> str:
    return at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _stored(day: date, decision: str, constraints=(), observed=3600, sources=2, gaps=()) -> dict:
    noon = local_noon(day, ZONE)
    row = {"day": day.isoformat(), "from": _z(noon.start), "to": _z(noon.end), "opportunity_kwh": None,
           "constraints": list(constraints), "decision": decision, "evidence_ids": [f"e-{day.day}"]}
    return {**_hour(decision), "rows": [row], "basis": {"accepted_evidence_ids": []},
            "coverage": {"required_seconds": 3600, "observed_seconds": observed, "source_count": sources,
                         "gaps": list(gaps)}}


def _hours(results) -> list:
    out = []
    for day, result in results:
        head = None if result is None else _Head(1, uuid4(), LO, "sha256:" + "0" * 64, result, ())
        out.append(_Hour(day, local_noon(day, ZONE), head, "SETTLED" if head else "NONE",
                         "CURRENT" if head else "UNKNOWN", None))
    return out


def test_q9_6_renewable_envelope_missing_middle_day() -> None:
    gap = {"from": "2026-10-08T09:30:00.000000Z", "to": "2026-10-08T10:00:00.000000Z"}
    hours = _hours([(DAYS[0], _stored(DAYS[0], "ELIGIBLE", sources=3)),
                    (DAYS[1], None),
                    (DAYS[2], _stored(DAYS[2], "LIMITED", ["COVERAGE_GAP"], observed=1800, sources=1, gaps=[gap]))])
    env = renewable_envelope(hours)
    assert env["status"] == "UNKNOWN" and env["basis"] is None
    assert [r["day"] for r in env["rows"]] == ["2026-10-06", "2026-10-08"]  # no row for the missing day
    cov = env["coverage"]
    assert cov["required_seconds"] == 3 * 3600 and cov["observed_seconds"] == 3600 + 1800
    assert cov["source_count"] == 3  # the maximum in one assessed hour, not a distinct count across days
    middle = local_noon(DAYS[1], ZONE)
    assert {"from": _z(middle.start), "to": _z(middle.end)} in cov["gaps"] and gap in cov["gaps"]
    assert cov["gaps"] == sorted(cov["gaps"], key=lambda g: (g["from"], g["to"]))
    assert env["limitations"] == [{"code": "COVERAGE_GAP", "evidence_ids": ["e-8"]}]
    assert env["cards"]["assessed_days"] == 1
    # Rows are ordered by (day, from) whatever the stored order.
    assert [r["day"] for r in renewable_envelope(list(reversed(hours)))["rows"]] == ["2026-10-06", "2026-10-08"]


def test_q9_8_links() -> None:
    [one] = _hours([(DAYS[1], None)])
    assert links("MG-1", [one]) == {"dispatch": "/sites/MG-1/performance/dispatch?day=2026-10-07",
                                    "evidence": "/sites/MG-1/evidence", "financials": None, "actions": "/actions"}
    encoded = links("MG 1/x", [one])
    assert encoded["dispatch"] == "/sites/MG%201%2Fx/performance/dispatch?day=2026-10-07"
    assert encoded["evidence"] == "/sites/MG%201%2Fx/evidence"
    assert links("MG-1", _hours([(DAYS[0], None), (DAYS[1], None)]))["dispatch"] is None  # two UTC days
    late = _Hour(DAYS[1], rules.Window(datetime(2026, 10, 7, 23, tzinfo=timezone.utc),
                                       datetime(2026, 10, 8, 0, tzinfo=timezone.utc)), None, "NONE", "UNKNOWN", None)
    assert links("MG-1", [late])["dispatch"] == "/sites/MG-1/performance/dispatch?day=2026-10-07"
    cross = _Hour(DAYS[1], rules.Window(datetime(2026, 10, 7, 23, 30, tzinfo=timezone.utc),
                                        datetime(2026, 10, 8, 0, 30, tzinfo=timezone.utc)), None, "NONE", "UNKNOWN",
                  None)
    assert links("MG-1", [cross])["dispatch"] is None


def test_q9_9_non_minigrid_exact_shape_and_partial_echo() -> None:
    reader = _Reader()
    client = _client(reader, site_type="COLDCHAIN")
    body = client.get(URL, params={"from": "2026-10-07T12:00:00+03:00", "to": "bad", "known_at": Q["to"]}).json()
    assert body["window"] == {"from": "2026-10-07T09:00:00.000000Z", "to": None,
                              "known_at": "2026-10-07T10:00:00.000000Z", "bounds": "[from,to)"}
    assert body["site"] == {"code": "MG-1", "timezone": ZONE}
    assert body["currentness"] == {"state": "UNKNOWN", "job_state": "NONE", "windows": []}
    assert body["coverage"] is None and body["basis"] is None and body["rows"] == []
    assert set(body["cards"].values()) == {None}
    assert body["selected_source_provenance"] is None and body["pending_source_provenance"] is None
    assert body["source_provenance"]["classification"] == "UNKNOWN"
    assert body["source_provenance"]["evidence_ids"] == [] and body["source_provenance"]["source_ids"] == []
    assert body["links"] == {"dispatch": None, "evidence": "/sites/MG-1/evidence", "financials": None,
                             "actions": None}
    assert reader.calls == []
    # Unknown domain: 404 only after the Site scope checks; authentication comes first.
    solar = "/api/sites/MG-1/performance/mini/solar"
    assert _client(reader, access=lambda r, c: 401).get(solar).json()["detail"]["code"] == "UNAUTHENTICATED"
    assert _client(reader, access=lambda r, c: 403).get(solar).json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
    assert _client(reader).get("/api/sites/NOPE/performance/mini/solar").json()["detail"]["code"] == "SITE_NOT_FOUND"
    assert client.get(solar).json() == {"detail": {"code": "MINI_DOMAIN_NOT_FOUND",
                                                   "message": "This page was not found."}}


def test_q9_10_lineage_fails_closed() -> None:
    noon = local_noon(DAYS[1], ZONE)

    def row(domain="service", lo=noon.start, hi=noon.end, basis_ids=("0b", "0a"), linked=("0a", "0b")):
        return (1, uuid4(), LO, "sha", {"basis": {"accepted_evidence_ids": list(basis_ids)}}, domain, lo, hi,
                list(linked))

    check_lineage("service", noon, row())
    check_lineage("service", noon, row(basis_ids=(), linked=()))  # equal empty sets
    for bad in (row(domain="fuel"), row(lo=noon.start + timedelta(hours=1)), row(linked=("0a",)),
                row(linked=("0a", "0b", "0c")), row(basis_ids=("0a",))):
        with pytest.raises(MiniReadUnavailable) as error:
            check_lineage("service", noon, bad)
        assert "0a" not in str(error.value) and "0c" not in str(error.value)
    broken = MiniReadUnavailable("A selected mini-depth revision's lineage or basis is broken.")
    response = _client(_Reader(broken)).get(URL, params=Q)
    assert response.json() == {"detail": {"code": "MINI_DEPTH_STORE_UNAVAILABLE",
                                          "message": "Mini-grid evidence is unavailable right now. Try again."}}
