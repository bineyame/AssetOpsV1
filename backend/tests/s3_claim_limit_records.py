"""`s3-claim-limit-records-v1`: the S3-02a capability / claim-limit public-ingestion fixture.

`build(runner)` takes an S4 `CaseRunner` (`test_s4_finding_store_postgres.py`: converted KOBO-001, the reviewed S3
demo configuration, reserve 20 % and a 0-minute minimum runtime from 2026-10-03) and adds only the cases the S3-02a
rule needs. Every reading is a sealed Batch V2 through the S2 ingestion service under the Site's registered gateway
principal and every assessment is the real S3 recompute worker; nothing is hand-inserted and no simulator truth is
read. It returns a manifest of exact public IDs that S3-02b's walkthrough uses.

Cases (each 08:00-08:30Z on its UTC day, 5-minute reports, generator STOPPED at 07:55 and 08:35, three feeders at
10 kW so load is 30 kW):

- `full-candidate` 2026-10-06: PV available 40 kW, PCS discharge 20 kW, SOC 80 % -> Candidate, complete coverage.
- `missing-pv` 2026-10-08: no PV-available report at all -> Indeterminate, PV MISSING over the interval.
- `poor-quality-conflict` 2026-10-11: PCS discharge UNAVAILABLE (NO_MEASUREMENT) at 08:10 and 08:15, and two
  contradictory PV-available reports at 08:25 -> Candidate portions plus POOR_QUALITY and CONFLICTED subspans.
- `late-revision` 2026-10-13: the 08:30 PV report arrives late; the first interval revision is withdrawn from
  currentness by a second revision of the same key (the first reads HISTORICAL).
- `stale-selection` 2026-10-15 (built last): assessed, then a later accepted SOC report leaves a recompute job
  outstanding -> STALE_PROJECTION, no current positive claim.

IDs differ per run; S3-02b reads them from the returned manifest (`tools/` copies the manifest beside the DB).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

FIXTURE_ID = "s3-claim-limit-records-v1"
STEP = timedelta(minutes=5)
FEEDERS = ("residential-meter", "clinic-meter", "mill-meter")
SIG = {"state": ("generator-controller", "status"), "pv": ("pv-inverter-controller", "available-power"),
       "dis": ("battery-pcs-controller", "discharge-capability"), "soc": ("battery-pcs-controller", "state-of-charge")}
DAYS = {"full-candidate": "2026-10-06", "missing-pv": "2026-10-08", "poor-quality-conflict": "2026-10-11",
        "late-revision": "2026-10-13", "stale-selection": "2026-10-15"}
EXPECT = {
    "full-candidate": {"currentness": "CURRENT", "ceiling": "CANDIDATE_AVOIDABLE", "support": "COMPLETE"},
    "missing-pv": {"currentness": "CURRENT", "ceiling": "INDETERMINATE", "support": "NONE"},
    "poor-quality-conflict": {"currentness": "CURRENT", "ceiling": "CANDIDATE_AVOIDABLE", "support": "LIMITED"},
    "late-revision": {"currentness": "CURRENT", "historical_currentness": "HISTORICAL"},
    "stale-selection": {"currentness": "STALE_PROJECTION", "ceiling": None},
}


def _at(day: str, hh: int, mm: int) -> datetime:
    return datetime.fromisoformat(f"{day}T00:00:00+00:00") + timedelta(hours=hh, minutes=mm)


def block(day: str, *, pv: bool = True, skip_pv: tuple[datetime, ...] = ()) -> list[tuple]:
    """(device, signal, time, value, quality) rows for one 08:00-08:30 ON interval."""
    rows = [(*SIG["state"], _at(day, 7, 55), "STOPPED", "GOOD")]
    t = _at(day, 8, 0)
    while t <= _at(day, 8, 30):
        rows.append((*SIG["state"], t, "RUNNING", "GOOD"))
        rows += [(f, None, t, "10", "GOOD") for f in FEEDERS]
        if pv and t not in skip_pv:
            rows.append((*SIG["pv"], t, "40", "GOOD"))
        rows.append((*SIG["dis"], t, "20", "GOOD"))
        rows.append((*SIG["soc"], t, "80", "GOOD"))
        t += STEP
    rows.append((*SIG["state"], _at(day, 8, 35), "STOPPED", "GOOD"))
    return rows


def _envelope(kit, device, signal, seq, when, value, quality, epoch):
    from assetops_contracts.source_envelope_v3 import SourceEnvelopeV3, canonical_envelope_v3_text, v3_message_id

    b = kit.binding(device, signal)
    z = when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    good = quality == "GOOD"
    return canonical_envelope_v3_text(SourceEnvelopeV3(
        message_id=v3_message_id(site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                 source_id=b["source_id"], sequence_epoch=epoch, sequence=seq),
        sequence_epoch=epoch, sequence=seq, site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
        source_id=b["source_id"], device_id=device, signal_id=b["signal_id"],
        binding_set_id=kit.doc["mapping"]["binding_set_id"], binding_version=kit.doc["mapping"]["version"],
        source_time=z, published_at=z, interval_start=None, interval_end=None, family="MEASUREMENT",
        measurement="STATE_AT_INSTANT", value=value if good else None, unit=b["source_unit"], quality=quality,
        unavailable_reason=None if good else "NO_MEASUREMENT"))


def deliver(runner, rows: list[tuple], decided: str, epoch: str = "epoch-1") -> None:
    """Sequence rows in source-time order per source (as a gateway numbers them) and submit one Batch V2 each."""
    envelopes = []
    for device, signal, when, value, quality in sorted(rows, key=lambda r: r[2]):
        source = runner.kit.binding(device, signal)["source_id"]
        runner.seq[(source, epoch)] = runner.seq.get((source, epoch), 0) + 1
        envelopes.append((device, _envelope(runner.kit, device, signal, runner.seq[(source, epoch)], when, value,
                                            quality, epoch)))
    runner.submit(envelopes, runner.tick(decided))


def _selected(url: str, runner, day: str) -> dict[str, Any]:
    from datetime import date

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService

    body = DispatchReadService(PostgresAssessmentStore(url)).window(runner.tenant, runner.site, date.fromisoformat(day))
    return {"status": body["status"],
            "run_id": None if body["selection"] is None else str(body["selection"]["run_id"]),
            "window_revision_id": None if body["window_assessment"] is None else str(body["window_assessment"]["id"]),
            "interval_revision_ids": [str(i["id"]) for i in body["intervals"]],
            "interval_claims": [i["claim_level"] for i in body["intervals"]]}


def build(runner, url: str) -> dict[str, Any]:
    """Run the five cases on `runner` (a fresh CaseRunner) against database `url`; return the ID manifest."""
    cases: dict[str, dict[str, Any]] = {}
    d = DAYS
    deliver(runner, block(d["full-candidate"]), "2026-10-30T08:00:00Z")
    deliver(runner, block(d["missing-pv"], pv=False), "2026-10-30T08:10:00Z")
    pq = d["poor-quality-conflict"]
    rows = [r for r in block(pq) if not (r[:2] == SIG["dis"] and r[2] in (_at(pq, 8, 10), _at(pq, 8, 15)))]
    rows += [(*SIG["dis"], _at(pq, 8, 10), None, "UNAVAILABLE"), (*SIG["dis"], _at(pq, 8, 15), None, "UNAVAILABLE"),
             (*SIG["pv"], _at(pq, 8, 25), "5", "GOOD")]
    deliver(runner, rows, "2026-10-30T08:20:00Z")
    late = d["late-revision"]
    deliver(runner, block(late, skip_pv=(_at(late, 8, 30),)), "2026-10-30T08:30:00Z")
    runner.step({"do": "assess"})
    first = _selected(url, runner, late)
    deliver(runner, [(*SIG["pv"], _at(late, 8, 30), "40", "GOOD")], "2026-10-30T09:00:00Z")
    runner.step({"do": "assess"})
    for name in ("full-candidate", "missing-pv", "poor-quality-conflict", "late-revision"):
        cases[name] = {"day": d[name], **_selected(url, runner, d[name]), "expect": EXPECT[name]}
    cases["late-revision"]["withdrawn"] = first
    stale = d["stale-selection"]
    deliver(runner, block(stale), "2026-10-30T09:30:00Z")
    runner.step({"do": "assess"})
    assessed = _selected(url, runner, stale)
    deliver(runner, [(*SIG["soc"], _at(stale, 8, 12), "79", "GOOD")], "2026-10-30T10:00:00Z")
    cases["stale-selection"] = {"day": stale, **_selected(url, runner, stale), "assessed": assessed,
                                "expect": EXPECT["stale-selection"]}
    return {"fixture_id": FIXTURE_ID, "site_code": "KOBO-001", "tenant_id": str(runner.tenant),
            "site_id": str(runner.site), "rule_id": "s3-claim-limit-1",
            "route": "/api/sites/KOBO-001/performance/dispatch/windows/{day}/claim-limit?revision={revision_id}",
            "cases": cases}
