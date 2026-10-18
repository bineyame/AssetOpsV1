"""W2-03 pure cold rules (`cold-excursion/1`, `cold-start-response/1`) on the W2-02 replay vectors.

Inputs are the registered W2-02 producer's public series, pinned in `fixtures/w2/cold-w203-vectors.json`
(kept equal to the producer by `host/tests/test_w203_cold_vectors.py`). Each record becomes the
`ColdEvidence` the selection would read: the COLD-LAB-001 `cold-roles-1` binding gives role and asset,
receipt time is the publication time. Negative cases are derived from those vectors by one named change each.
The ordinary-intake replay through Postgres is `test_w203_cold_replay_postgres.py`.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid5

from assetops_backend.analytics.cold import (
    ColdEvidence,
    ColdPolicy,
    ColdStartPolicy,
    ColdWindow,
    SourceGate,
    assess_excursion,
    assess_start_response,
    basis_sha256,
    episode_key_sha256,
)

VECTORS = json.loads((Path(__file__).parent / "fixtures" / "w2" / "cold-w203-vectors.json").read_text("utf-8"))
NS = UUID("6c0d7a52-0000-4000-8000-000000000203")
TENANT, SITE = uuid5(NS, "tenant"), uuid5(NS, "site")
ASSET = {name: uuid5(NS, name) for name in (
    "room-1", "probe-1", "ambient-1", "compressor-1", "transfer-1", "generator-1", "bus-1", "grid-1")}
#: COLD-LAB-001 `cold-roles-1` channels: (device, signal) -> (role, asset).
ROLES = {
    ("chamber-probe", "temperature"): ("chamber_temperature", "probe-1"),
    ("ambient-probe", "temperature"): ("ambient_temperature", "ambient-1"),
    ("grid-meter", "state"): ("grid_state", "grid-1"),
    ("grid-meter", "event"): ("grid_power_event", "grid-1"),
    ("generator-controller", "state"): ("generator_state", "generator-1"),
    ("generator-controller", "start-event"): ("backup_start_event", "generator-1"),
    ("compressor-controller", "state"): ("compressor_state", "compressor-1"),
    ("compressor-meter", "power"): ("compressor_power", "compressor-1"),
    ("transfer-controller", "event"): ("transfer_result", "transfer-1"),
    ("backup-bus-meter", "state"): ("backup_bus_state", "bus-1"),
    ("door-sensor", "event"): ("door_event", "room-1"),
}
POLICY = ColdPolicy(room_asset_id=ASSET["room-1"], probe_asset_id=ASSET["probe-1"], policy_low=Decimal("2.0"),
                    policy_high=Decimal("4.0"), return_hysteresis=Decimal("0.2"), min_excursion_minutes=Decimal(15))
START = ColdStartPolicy(generator_asset_id=ASSET["generator-1"], start_timeout_minutes=Decimal(5),
                        transfer_bound=True, probe_asset_id=ASSET["probe-1"])
GATE = SourceGate("REGISTERED_SIMULATION", ("cold-lab-gateway",), True)


def at(hhmm: str) -> datetime:
    return datetime.fromisoformat(f"2026-10-06T{hhmm}:00+00:00")


def window(known: str = "20:05") -> ColdWindow:
    return ColdWindow(at("19:00"), at("20:05"), at(known))


def _time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def evidence(case: str) -> list[ColdEvidence]:
    out = []
    for row in VECTORS["cases"][case]:
        role, asset = ROLES[(row["device_id"], row["signal_id"])]
        value = row["value"]
        if value is not None and row["unit"] in ("degC", "kW"):
            value = Decimal(value)
        published = _time(row["published_at"])
        out.append(ColdEvidence(
            evidence_id=uuid5(NS, row["report_key"]), envelope_sha256=row["report_sha256"], family=row["family"],
            record_kind=row["record_kind"], role=role, asset_id=ASSET[asset], source_time=_time(row["source_time"]),
            received_at=published, decided_at=published, quality=row["quality"], value=value, unit=row["unit"],
            event_id=row["event_id"], correlation_id=row["correlation_id"], outcome=row["outcome"],
            source_id=f"{row['device_id']}/{row['signal_id']}", clock_attested=True))
    return out


def pick(rows, role: str, hhmm: str, kind: str | None = None) -> ColdEvidence:
    [found] = [e for e in rows if e.role == role and e.source_time == at(hhmm)
               and (kind is None or e.record_kind == kind)]
    return found


def swap(rows, old: ColdEvidence, new: ColdEvidence | None) -> list[ColdEvidence]:
    return [new if e is old else e for e in rows if not (e is old and new is None)]


def links(item) -> dict[UUID, tuple[str, str | None]]:
    return {link.evidence_id: (link.use, link.reason) for link in item.links}


def step(chain, name: str):
    [found] = [s for s in chain.steps if s.step == name]
    return found


def test_in_band_no_excursion() -> None:
    rows = evidence("normal")
    a = assess_excursion(rows, window(), POLICY, GATE)
    assert (a.state, a.claim_level) == ("NO_EXCURSION_OBSERVED", "BOUNDED")
    assert (a.known_points, a.expected_points, a.coverage) == (13, 13, Decimal(1))
    assert a.excursions == () and a.gaps == ()
    # Basis: same records in another order hash the same; a changed cutoff or gate does not.
    args = dict(analytic_id=a.analytic_id, model_version=a.model_version, tenant_id=TENANT, site_id=SITE,
                foundation_revision_ids=[uuid5(NS, "f")], binding_revision_ids=[uuid5(NS, "b")])
    first = basis_sha256(window=window(), source_gate=GATE, records=rows, **args)
    assert first == basis_sha256(window=window(), source_gate=GATE, records=list(reversed(rows)), **args)
    assert first != basis_sha256(window=window("20:10"), source_gate=GATE, records=rows, **args)
    assert first != basis_sha256(window=window(), source_gate=replace(GATE, classification="MIXED"),
                                 records=rows, **args)
    assert len(first) == 64


def test_two_high_points_and_open_bounds() -> None:
    rows = evidence("excursion")
    a = assess_excursion(rows, window(), POLICY, GATE)
    assert (a.state, a.claim_level, a.known_points) == ("OBSERVED_EXCURSION", "BOUNDED", 13)
    [x] = a.excursions
    assert x.direction == "HIGH" and x.anchor_evidence_id == pick(rows, "chamber_temperature", "19:15").evidence_id
    assert (x.start_earliest, x.start_latest) == (at("19:10"), at("19:15"))
    assert x.open and (x.end_earliest, x.end_latest) == (None, None)
    assert (x.duration_low, x.duration_high) == (Decimal(45), None)
    assert x.peak_observed == Decimal("4.8") and x.exposure_finding and x.claim_level == "BOUNDED"
    assert Decimal(0) < x.degree_minutes_low <= x.degree_minutes_high
    # backup-failed: the same exposure; the door cycle is context only.
    b_rows = evidence("backup-failed")
    [bx] = assess_excursion(b_rows, window(), POLICY, GATE).excursions
    assert (bx.start_latest, bx.duration_low, bx.duration_high, bx.exposure_finding) == (
        at("19:15"), Decimal(45), None, True)
    door = [e for e in b_rows if e.role == "door_event"]
    assert len(door) == 2 and links(bx)[door[0].evidence_id] == ("CONTEXT", "DOOR_EVENT")
    assert all(links(bx).get(d.evidence_id, ("CONTEXT",))[0] == "CONTEXT" for d in door)
    # late-reading: 12/13 at 20:05 (first highs 19:15 and 19:25), 13/13 at 20:10 on a new basis, same anchor.
    late = evidence("late-reading")
    early, after = (assess_excursion(late, window(k), POLICY, GATE) for k in ("20:05", "20:10"))
    assert (early.known_points, after.known_points) == (12, 13)
    [e1], [e2] = early.excursions, after.excursions
    assert e1.anchor_evidence_id == e2.anchor_evidence_id and e1.start_latest == at("19:15")
    supported = [e.source_time for e in late if links(e1).get(e.evidence_id) == ("SUPPORT", None)]
    assert at("19:25") in supported and at("19:20") not in supported
    assert (e1.duration_low, e2.duration_low) == (Decimal(45), Decimal(45))
    key = lambda x: episode_key_sha256(TENANT, SITE, "EXCURSION", ASSET["room-1"], x.anchor_evidence_id)
    assert key(e1) == key(e2) and len(key(e1)) == 64
    common = dict(analytic_id="cold-excursion", model_version="1", tenant_id=TENANT, site_id=SITE,
                  foundation_revision_ids=[], binding_revision_ids=[], source_gate=GATE)
    known_early = [e for e in late if e.received_at <= at("20:05")]
    assert basis_sha256(window=window("20:05"), records=known_early, **common) != basis_sha256(
        window=window("20:10"), records=late, **common)


def test_no_gap_bridge() -> None:
    rows = evidence("missing-probe")
    a = assess_excursion(rows, window(), POLICY, GATE)
    assert (a.known_points, a.expected_points, a.state, a.claim_level) == (7, 13, "UNKNOWN", "UNKNOWN")
    [gap] = a.gaps
    assert (gap.start, gap.end, gap.reason, gap.expected_points, gap.received_points) == (
        at("19:15"), at("19:45"), "MISSING_PROBE", 6, 0)
    assert all(not x.exposure_finding and x.claim_level == "UNKNOWN" for x in a.excursions)
    [x] = a.excursions
    assert x.start_earliest is None and x.start_latest == at("19:45")  # 19:10 -> 19:45 is not bridged
    # One fifteen-minute hole (19:35 -> 19:50) inside the excursion: the lower duration stops at the hole, and
    # the hole adds no degree-minute area.
    full = evidence("excursion")
    holed = [e for e in full if not (e.role == "chamber_temperature" and at("19:40") <= e.source_time <= at("19:45"))]
    h = assess_excursion(holed, window(), POLICY, GATE)
    assert h.known_points == 11 and h.claim_level == "BOUNDED"
    [hx] = h.excursions
    [fx] = assess_excursion(full, window(), POLICY, GATE).excursions
    assert hx.duration_low == Decimal(20) and hx.degree_minutes_high < fx.degree_minutes_high
    assert hx.exposure_finding


def test_start_success_and_failure() -> None:
    normal = evidence("normal")
    [c] = assess_start_response(normal, window(), START, GATE).chains
    assert (c.result, c.claim_level, c.missing_steps, c.failure_finding) == ("OBSERVED_SUCCESS", "OBSERVED", (), False)
    assert [(s.step, s.at) for s in c.steps][:5] == [
        ("GRID", at("19:05")), ("START_REQUEST", at("19:05")), ("START_RESULT", at("19:07")),
        ("GENERATOR", at("19:07")), ("TRANSFER", at("19:08"))]
    assert c.anchor_evidence_id == pick(normal, "backup_start_event", "19:05", "START_REQUEST").evidence_id
    for case in ("excursion", "backup-failed", "missing-probe"):
        rows = evidence(case)
        [f] = assess_start_response(rows, window(), START, GATE).chains
        assert (f.result, f.claim_level, f.failure_finding) == ("OBSERVED_FAILURE", "OBSERVED", True), case
        assert step(f, "START_RESULT").at == at("19:05") and step(f, "START_REQUEST").at == at("19:00")
        assert f.missing_steps == ("TRANSFER",)
    # Without the explicit result, the 5-minute timeout supports the failure only with complete generator
    # state coverage through the timeout.
    rows = evidence("excursion")
    no_result = swap(rows, pick(rows, "backup_start_event", "19:05", "START_RESULT"), None)
    [t] = assess_start_response(no_result, window(), START, GATE).chains
    assert (t.result, step(t, "START_RESULT").state) == ("OBSERVED_FAILURE", "MISSING")
    thin = swap(no_result, pick(no_result, "generator_state", "19:05"), None)
    [u] = assess_start_response(thin, window(), START, GATE).chains
    assert (u.result, u.claim_level, u.failure_finding) == ("UNKNOWN", "UNKNOWN", False)
    # A gate that does not permit a Finding keeps the observation but no Finding.
    [g] = assess_start_response(rows, window(), START, replace(GATE, permitted=False)).chains
    assert (g.result, g.failure_finding) == ("OBSERVED_FAILURE", False)


def test_missing_transfer_and_probe() -> None:
    rows = evidence("normal")
    no_transfer = swap(rows, pick(rows, "transfer_result", "19:08"), None)
    [c] = assess_start_response(no_transfer, window(), START, GATE).chains
    assert c.missing_steps == ("TRANSFER",) and c.result == "OBSERVED_SUCCESS"
    assert step(c, "TRANSFER").state == "MISSING" and step(c, "BUS").state == "OBSERVED"  # bus never stands in
    assert all(link.evidence_id != pick(rows, "transfer_result", "19:08").evidence_id for link in c.links)
    # The probe step goes missing when no usable probe reading follows the compressor state.
    no_probe = [e for e in rows if e.role != "chamber_temperature"]
    [p] = assess_start_response(no_probe, window(), START, GATE).chains
    assert "PROBE" in p.missing_steps and step(p, "PROBE").evidence_ids == ()
    m = assess_excursion(evidence("missing-probe"), window(), POLICY, GATE)
    assert m.state == "UNKNOWN" and not any(x.exposure_finding for x in m.excursions)


def test_contradictory_good_outcomes() -> None:
    rows = evidence("contradictory")
    a = assess_start_response(rows, window(), START, GATE)
    [c] = a.chains
    assert (a.state, c.result, c.claim_level, c.failure_finding) == (
        "CONTRADICTORY", "CONTRADICTORY", "CONTRADICTORY", False)
    results = [e for e in rows if e.record_kind == "START_RESULT"]
    assert {e.outcome for e in results} == {"SUCCEEDED", "FAILED"}
    assert step(c, "START_RESULT").state == "CONTRADICTORY"
    assert all(links(c)[e.evidence_id] == ("EXCLUDED", "CONTRADICTORY") for e in results)
    # Two GOOD probe values at one instant are a contradiction, never an excursion claim.
    temp = evidence("excursion")
    point = pick(temp, "chamber_temperature", "19:30")
    twin = replace(point, evidence_id=uuid5(NS, "twin"), value=Decimal("3.0"), envelope_sha256="0" * 64)
    t = assess_excursion(temp + [twin], window(), POLICY, GATE)
    assert (t.state, t.claim_level) == ("CONTRADICTORY", "CONTRADICTORY")
    assert not any(x.exposure_finding for x in t.excursions)
    assert any(g.reason == "CONTRADICTORY" and g.start == at("19:30") for g in t.gaps)


def test_suspect_clock_skew_unbound_excluded() -> None:
    rows = evidence("excursion")
    suspect = pick(rows, "chamber_temperature", "19:20")
    skewed = pick(rows, "chamber_temperature", "19:25")
    unbound_result = pick(rows, "backup_start_event", "19:05", "START_RESULT")
    changed = swap(rows, suspect, replace(suspect, quality="SUSPECT"))
    changed = swap(changed, skewed, replace(skewed, clock_attested=False))
    changed = swap(changed, unbound_result, replace(unbound_result, role=None, asset_id=None))
    a = assess_excursion(changed, window(), POLICY, GATE)
    assert a.known_points == 11
    assert links(a)[suspect.evidence_id] == ("CONTEXT", "SUSPECT")
    assert links(a)[skewed.evidence_id] == ("EXCLUDED", "CLOCK_UNATTESTED")
    assert {(g.start, g.reason) for g in a.gaps} == {(at("19:20"), "SUSPECT"), (at("19:25"), "CLOCK_UNATTESTED")}
    [x] = a.excursions
    # 19:15 -> 19:30 is beyond the ten-minute bridge, so 19:15 stays unconfirmed; the excursion is confirmed by
    # 19:30/19:35 with an unknown earliest start, and no excluded reading supports it.
    assert (x.start_earliest, x.start_latest) == (None, at("19:30"))
    assert links(x).get(suspect.evidence_id, ("CONTEXT",))[0] != "SUPPORT"
    assert links(x).get(skewed.evidence_id, ("EXCLUDED",))[0] != "SUPPORT"
    [c] = assess_start_response(changed, window(), START, GATE).chains
    assert links(c)[unbound_result.evidence_id] == ("EXCLUDED", "UNBOUND")
    assert unbound_result.evidence_id not in step(c, "START_RESULT").evidence_ids
    # Without its explicit result only the timeout with complete generator coverage can support the failure;
    # a SUSPECT generator state removes that coverage.
    assert step(c, "START_RESULT").state == "MISSING" and c.result == "OBSERVED_FAILURE"
    gen = pick(changed, "generator_state", "19:05")
    [u] = assess_start_response(swap(changed, gen, replace(gen, quality="SUSPECT")), window(), START, GATE).chains
    assert u.result == "UNKNOWN"
