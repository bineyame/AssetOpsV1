"""DEMO-A U3 / DEMO-SPARSE U3: the Kobo (KOBO-001) story days of the combined demo dataset, run by
`tools/demo_combined.py` as a child.

    python tools/demo_combined_kobo.py build <database-url> <work>

It is the public replay of `backend/conversions/d-verification-window-v3.json` (WALK1-4: the s602b REPLAY body of
v2, `tools/s602b_verification_walkthrough.py`, on mini-grid v6 + publication v5): two registered Lab runs published by a real gateway
process, accepted by ordinary S2 batch ingestion, assessed (S3) and matched (S4); then recommendation -> accept ->
apply -> freeze plan -> later selection -> evaluation through the real Action API. The only change is the calendar:
a deep copy of the v2 manifest with every instant replaced from `<work>/story.json` (baseline received, assessed,
accepted, applied and frozen on story day S, the later run on S+1). Diesel price v1 is published at Kobo install
+ 1 h through the test-only recorded-time seam (DEMO-A0, Addendum 1 R1), so the trial is priced with a price known
before it. Then the prepared work records (two generator visits, two plans) through the work service.

DEMO-SPARSE: the Site is imported at `kobo.import_at` and converted at `kobo.install_at` (S-29d), the labelled demo
configurations take effect at commissioning (`configure_at`, Q1 ruling), and every Kobo entry of `<work>/days.json`
runs in build order: a day kind is one registered Lab run (`run_day`), the trial pair is the chain above at its place,
and a `missing` day writes nothing.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import demo_story_days as sd
from demo_combined import at, iso

CONVERSIONS = Path(__file__).resolve().parents[1] / "backend" / "conversions"
#: WALK1-4 (D-W1-7, D-W1-9): every Kobo day, the trial pair included, replays the v3 manifest - v2's scenario, seeds,
#: windows and policy on mini-grid v6 + registered-kobo-publication v5. v2 stays byte-unchanged for the host tests.
MANIFEST_V3 = json.loads((CONVERSIONS / "d-verification-window-v3.json").read_text(encoding="utf-8"))
#: WALK1-4: the minigrid-roles-4 demo configuration (charge-request binding, D-W1-3 declared margins).
ROLES4 = json.loads((CONVERSIONS / "kobo-001-minigrid-roles-4-demo-config.json").read_text(encoding="utf-8"))
FIXTURE_PRICES = Path(__file__).resolve().parents[1] / "backend" / "conversions" / "demo-diesel-price-publications.json"
#: WALK1-3 §4.1 (D-W1-2): the declared price per kWh for productive users, published at the diesel price's instant.
FIXTURE_PRODUCTIVE_PRICE = (Path(__file__).resolve().parents[1] / "backend" / "conversions"
                            / "demo-productive-price-publications.json")


def resolved_manifest(base: dict, story: dict) -> dict:
    """The v2 manifest on the story calendar: same scenario, seeds, profiles, reserve values and windows' length."""
    k = story["kobo"]
    M = copy.deepcopy(base)
    for name in ("baseline", "later"):
        for key in ("start", "end", "foundation_known_at", "received_at", "sequence_epoch"):
            M["runs"][name][key] = k["runs"][name][key]
    M["scenario"] = dict(k["runs"]["baseline"]["scenario"])
    M["action"].update({"finding_anchor_day": story["S_date"], "accept_at": k["action"]["accept_at"],
                        "apply_at": k["action"]["apply_at"], "effective_from": k["action"]["effective_from"]})
    M["plan"]["freeze_at"] = k["plan"]["freeze_at"]
    M["windows"]["baseline_start"] = k["windows"]["baseline_start"].replace("Z", "+00:00")
    M["windows"]["later_start"] = k["windows"]["later_start"].replace("Z", "+00:00")
    M["evaluate_at"] = k["evaluate_at"]
    return M


#: Q1 ruling (`.agent/DEMO-SPARSE-preflight.md`): the two labelled demo configurations take effect at Kobo
#: commissioning instead of their build dates; values byte-identical, only `effective_from` moves.
CONFIG_OFFSETS = {"properties": timedelta(minutes=10), "roles2": timedelta(minutes=10),
                  "roles3": timedelta(minutes=20), "known": timedelta(minutes=30),
                  # WALK1-3 §4.2: the additive supply-use change, after the +20 roles-3 revision so it carries forward (a change
                  # only splits the revision in force at its instant); no pinned configuration file changes
                  "uses": timedelta(minutes=25),
                  # WALK1-4: roles-4 (charge request) and the two declared margins, after the supply uses so every
                  # earlier property carries forward, before the commissioning record instant (+30)
                  "roles4": timedelta(minutes=27)}
#: WALK1-3 §4.2: what each Kobo feeder supplies, declared in the Site configuration (never guessed from names).
SUPPLY_USES = {"load-mill": "PRODUCTIVE", "load-res": "HOUSEHOLD", "load-clinic": "ESSENTIAL_SERVICE"}


def configure_at(store, result, install_at: datetime) -> dict:
    """`pub.configure` on the story calendar: S3 demo configuration (generator values + roles-2) at install + 10 min,
    the S6 verification configuration (roles-3) at install + 20 min, both recorded at install + 30 min."""
    import test_s6_verification_publication as pub
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.demo_configuration import apply_demo_configuration

    s3, ver = copy.deepcopy(pub.S3_DEMO), copy.deepcopy(pub.VERIFICATION)
    s3["component_properties"]["effective_from"] = iso(install_at + CONFIG_OFFSETS["properties"])
    s3["bindings"]["effective_from"] = iso(install_at + CONFIG_OFFSETS["roles2"])
    ver["component_properties"]["effective_from"] = iso(install_at + CONFIG_OFFSETS["properties"])
    ver["bindings"]["effective_from"] = iso(install_at + CONFIG_OFFSETS["roles3"])
    for doc, base in ((s3, pub.S3_DEMO), (ver, pub.VERIFICATION)):
        assert doc["status"] == base["status"] and doc["status"].startswith("SIMULATED DEMO CONFIGURATION")
    clock = pub.registered.Clock(install_at + CONFIG_OFFSETS["known"])
    foundation, bindings = pub.registered.FoundationService(store, "demo", clock), BindingService(store, clock)
    apply_demo_configuration(store, foundation, bindings, result.tenant, result.site, s3)
    applied = apply_demo_configuration(store, foundation, bindings, result.tenant, result.site, ver)
    assert applied.periods[-1]["role_set"] == "minigrid-roles-3"
    declare_supply_uses(foundation, result, install_at)
    declare_no_load_rate(foundation, result, install_at)
    roles4 = configure_roles4(store, foundation, bindings, result, install_at)
    return {"labels": [s3["label"], ver["label"]],
            "properties_effective_from": s3["component_properties"]["effective_from"],
            "roles2_effective_from": s3["bindings"]["effective_from"],
            "roles3_effective_from": ver["bindings"]["effective_from"],
            "supply_uses_effective_from": iso(install_at + CONFIG_OFFSETS["uses"]),
            "roles4_effective_from": roles4, "roles4_label": ROLES4["label"],
            "recorded_at": iso(install_at + CONFIG_OFFSETS["known"])}


def configure_roles4(store, foundation, bindings, result, install_at: datetime) -> str:
    """WALK1-4: at install + 27 min, the declared solar uncertainty (pv-inverter) through the labelled roles-4 demo
    configuration, the declared retained margin (ac-bus) as one additive Foundation change at the same instant, and
    the roles-4 binding set (every roles-3 binding plus the battery charge request). D-W1-3 declared values."""
    from assetops_backend.sites.demo_configuration import apply_demo_configuration

    at_ = iso(install_at + CONFIG_OFFSETS["roles4"])
    doc = copy.deepcopy(ROLES4)
    bus = doc.pop("ac_bus_properties")
    doc["component_properties"]["effective_from"] = at_
    doc["bindings"]["effective_from"] = at_
    assert doc["status"].startswith("SIMULATED DEMO CONFIGURATION")
    foundation.publish_component_properties(
        result.tenant, result.site, asset_code=bus["asset_code"], effective_from=install_at + CONFIG_OFFSETS["roles4"],
        note=bus["note"], properties=bus["properties"])
    applied = apply_demo_configuration(store, foundation, bindings, result.tenant, result.site, doc)
    assert applied.periods[-1]["role_set"] == "minigrid-roles-4", applied.periods
    return at_


def declare_supply_uses(foundation, result, install_at: datetime) -> None:
    """WALK1-3 §4.2: one additive Foundation change per feeder at install + 25 min, recorded with the rest of the
    commissioning configuration (install + 30 min). Only `supply-use` is added; every other property is kept."""
    for code, use in SUPPLY_USES.items():
        foundation.publish_component_properties(
            result.tenant, result.site, asset_code=code, effective_from=install_at + CONFIG_OFFSETS["uses"],
            note="Demonstration supply use declared at commissioning",
            properties=[{"property_key": "supply-use", "value": use, "unit": "state", "source": "SITE",
                         "source_version": 1}])


#: FUEL-1 §4.3 / A3-R §3.1 (owner 2026-11-07: "Generic 3.3 L/h, labelled"): the declared generator no-load fuel
#: rate and its basis. 3.3 is the owner's value, never changed to reach a figure.
NO_LOAD = [{"property_key": "generator-no-load-fuel-rate", "value": 3.3, "unit": "L/h", "source": "SITE",
            "source_version": 1},
           {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state",
            "source": "SITE", "source_version": 1}]
NO_LOAD_NOTE = ("Generic no-load fuel rate for a 40 kW diesel set (common design-software default, about 0.08 L/h "
                "per kW of rating); not this generator's datasheet. Owner decision 2026-11-07.")


def declare_no_load_rate(foundation, result, install_at: datetime) -> None:
    """FUEL-1 A3-R §3.1: one additive Foundation change on the generator at install + 25 min (with the supply uses),
    so every later revision carries the rate and its basis; every other generator property is kept."""
    foundation.publish_component_properties(
        result.tenant, result.site, asset_code="generator", effective_from=install_at + CONFIG_OFFSETS["uses"],
        note=NO_LOAD_NOTE, properties=copy.deepcopy(NO_LOAD))


def publish_price(url: str, recorded_at: datetime) -> None:
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.publish_assumption import main as publish
    import pg_harness

    store = PostgresAssumptionStore(url, test_recorded_clock_override=lambda: recorded_at)
    try:
        for name, fixture in (("diesel price", FIXTURE_PRICES), ("productive-use price", FIXTURE_PRODUCTIVE_PRICE)):
            code = publish(["fixture", "--site", "KOBO-001", "--file", str(fixture), "--step", "v1"], store=store)
            if code != 0:
                raise SystemExit(f"{name} v1 publication failed ({code})")
    finally:
        pg_harness.dispose(store)


def write_work(url: str, store, result, story: dict) -> dict:
    from test_w401_work_service_postgres import PRINCIPAL, event, plan, record, request
    from assetops_backend.work.composition import build_work_service

    k = story["kobo"]
    tenant, site = result.tenant.id, result.site.id
    assets = store.registrations(tenant, site).assets
    by_type = {}
    for a in assets:
        by_type.setdefault(a.asset_type, []).append(a)
    work = build_work_service(url)
    out = {"visits": [], "plans": []}
    try:
        for v in k["visits"]:
            asset = by_type[v["asset_type"]][0]
            when = at(v["at"])
            # POLISH §3 "Request narratives": the request's own title as a sentence, not the test default.
            s, case = work.create_case(tenant, site, request(
                f"demo3-kobo-{v['key']}", title=v["title"], narrative=f"{v['title']}.", occurred_at=iso(when),
                asset_id=str(asset.id), finding_links=[]), PRINCIPAL)
            assert s == 201, (v["key"], s, case)
            s, rec = work.post_record(tenant, site, case["id"], record(
                f"demo3-kobo-{v['key']}-rec", activity=v["title"], occurred_at=iso(when + timedelta(minutes=20)),
                outcome_note=v["note"]), PRINCIPAL)
            assert s == 201, (v["key"], s, rec)
            s, a = work.post_event(tenant, site, case["id"], event(
                "ASSIGN", {"assignee": "Site technician"}, f"demo3-kobo-{v['key']}-assign",
                occurred_at=iso(when + timedelta(minutes=21))), PRINCIPAL)
            assert s == 201, (v["key"], s, a)
            s, c = work.post_event(tenant, site, case["id"], event(
                "COMPLETE", {"maintenance_record_id": rec["id"]}, f"demo3-kobo-{v['key']}-complete",
                occurred_at=iso(when + timedelta(minutes=22))), PRINCIPAL)
            assert s == 201 and c["state"] == "COMPLETED", (v["key"], s, c)
            out["visits"].append({"key": v["key"], "id": case["id"], "code": case.get("code"), "record_id": rec["id"],
                                  "asset": asset.asset_code, "occurred_at": iso(when)})
        for p in k["plans"]:
            asset = by_type[p["asset_type"]][0]
            s, pl = work.post_plan(tenant, site, plan(
                f"demo3-kobo-{p['key']}", asset_id=str(asset.id), title=p["title"], trigger_kind=p["trigger_kind"],
                next_due_at=p["due_at"], next_due_hours=p["due_hours"], occurred_at=p["at"]), PRINCIPAL)
            assert s == 201, (p["key"], s, pl)
            out["plans"].append({"key": p["key"], "id": str(pl.get("canonical_plan_id") or pl.get("id")),
                                 "title": p["title"], "asset": asset.asset_code, "due_at": p["due_at"]})
    finally:
        work._store.dispose()
    return out


def day_manifest(base: dict, day: "sd.DayRun") -> dict:
    """The v2 manifest for one story day: that day's scenario and instants; seed and profiles unchanged."""
    M = copy.deepcopy(base)
    M["scenario"] = dict(day.scenario)
    M["runs"] = {"day": {"start": iso(day.start), "end": iso(day.end), "seed": base["runs"]["baseline"]["seed"],
                         "sequence_epoch": day.epoch, "foundation_known_at": iso(day.known_at),
                         "received_at": iso(day.received_at)}}
    return M


def findings_on(engine, site_id, day: str) -> list[str]:
    from sqlalchemy import text

    lo = at(day + "T00:00:00Z")
    with engine.connect() as c:
        rows = c.execute(text("SELECT DISTINCT finding_id FROM finding_revision WHERE site_id = :s AND "
                              "episode_start < :hi AND episode_end > :lo ORDER BY finding_id"),
                         {"s": site_id, "lo": lo, "hi": lo + timedelta(days=1)}).fetchall()
    return [str(r[0]) for r in rows]


def publish_first_half(tmp_path: Path, run, epoch: str, received_at: datetime, *, gateway_dir: Path | None = None,
                       keep=None, outage_continues: bool = False, withheld_run: str | None = None) -> dict:
    """`rp._publish_and_accept` for the `degraded` kind's U1 fallback (a gateway outage): the run publishes through
    a real gateway, but only the first half of its sealed batches reaches S2 before the gateway stops. The rest is
    never delivered (append-only: nothing is withdrawn).

    DD1a1-R5: on the Site-day's one gateway state (`gateway_dir`), the undelivered half stays in that gateway's
    outbox, so a complement run after the outage cannot deliver its own batches without the withheld ones. Such a
    complement (`outage_continues`) is run and staged on the same stream but delivers nothing: the outage lasts the
    rest of the day (DD1a1-R6).

    DD1a1-R6 fix: the gateway's background uploader runs a delivery pass the moment it starts, which drained the
    withheld half through a later complement's gateway. A post-outage complement's gateway is therefore started with
    no `upload` block (no network: the gateway is down), so nothing it holds can leave it. `withheld_run` (the story
    run of the outage) is read back from the same outbox afterwards, to show its undelivered half is still held."""
    import secrets
    from uuid import UUID

    import test_s6_verification_publication as pub
    import test_s6_verification_replay as rp
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.evidence.publication import register_run
    from assetops_backend.runs.source_publication import run_attestation
    from assetops_contracts.ingestion_receipt_v2 import canonical_receipt_v2_text
    from assetops_gateway.credential_protection import restrict_to_current_user
    from fake_central import CERT, FakeCentral
    from gateway_publication import RegisteredGatewayPublisher

    doc = json.loads(run.registered_basis.snapshot_canonical)
    principal = GatewayPrincipal(tenant_id=UUID(doc["tenant_id"]), site_id=UUID(doc["site"]["site_id"]),
                                 gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"])
    received = pub.registered.Clock(received_at)
    ingestion = BatchIngestionService(PostgresEvidenceLedger(rp.URL, test_decision_clock_override=received), received)
    statuses: list[str] = []

    def respond(path, headers, body):
        if path.split("?")[0] != "/api/ingestion/batches":
            return 201, b"{}"
        answer = ingestion.submit(principal, body)
        statuses.append(answer.receipt.status)
        return answer.status, canonical_receipt_v2_text(answer.receipt).encode("utf-8")

    token = f"aog1.{secrets.token_hex(16)}.{secrets.token_urlsafe(32)}"
    state = gateway_dir or tmp_path / "gateway"
    state.mkdir(parents=True, exist_ok=gateway_dir is not None)
    (state / "upload.credential").write_text(token, encoding="ascii")
    restrict_to_current_user(state / "upload.credential")
    central = FakeCentral(respond)
    upload = {"server_url": central.url, "upload_credential_file": "upload.credential", "ca_file": str(CERT),
              "interval_seconds": 3600}
    if outage_continues:
        from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config

        write_config(state, provisioning_from_snapshot(run.registered_basis.snapshot_canonical, epoch=epoch))
        process = GatewayProcess(state / "gateway.json")  # no `upload`: no uploader, no background pass
        assert process.ready, process.first_line
    else:
        process = rp._gateway(tmp_path, run, epoch, upload, state_dir=gateway_dir)
    try:
        port = pub._host(tmp_path / "h", process.link, keep)
        port.start(run)
        assert port.run_to_end(run).status == "COMPLETED"
        stage = port.registered_stage(run)
        assert stage.status == "STAGED", stage.status
        register_run(PostgresEvidenceLedger(rp.URL), run_attestation(run, stage))
        port.release_registered(run)
        half = 0 if outage_continues else len(stage.batches) // 2
        publisher, sent = RegisteredGatewayPublisher(process.link), 0
        while sent < half:
            attempted = publisher.deliver(min(50, half - sent))["batches"]["attempted"]
            if not attempted:
                break
            sent += attempted
        outbox = publisher.delivery(str(getattr(run, "run_id", "")))  # DD1a1-R6: what the gateway still holds
        withheld = publisher.delivery(withheld_run) if withheld_run else None
    finally:
        process.kill()
        central.close()
    if outage_continues:
        assert statuses == [], statuses  # DD1a1-R6: nothing reached S2 after the outage
    else:
        assert statuses and set(statuses) == {"COMPLETED"}, statuses
    return {"batches": len(stage.batches), "delivered_batches": sent, "envelopes": len(stage.envelopes),
            "delivery": ("staged, not delivered (the gateway stays down for the rest of the local day)"
                         if outage_continues else "first half of the sealed batches (gateway outage)"),
            "outbox_after": outbox, "withheld_after": withheld}


def trial_day_index(url: str, runner, S: datetime) -> dict:
    """U3 unit check: the one-day Site Finding index over [S, S+1) (the S4 read, CURRENT without IDX-GAPS) through
    the real router. The Performance gate is held open here only: the product gate opens after `finish()`."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.analytics.finding_index import FindingIndexService
    from assetops_backend.finding_index_api import build_finding_index_router

    dispatch = DispatchReadService(PostgresAssessmentStore(url))
    index = FindingIndexService(PostgresFindingStore(url), dispatch)
    scope = {"KOBO-001": ("KOBO-001", runner.tenant, runner.site)}
    app = FastAPI()
    app.include_router(build_finding_index_router(index, scope.get,
                                                  gate=lambda c, t, s: (True, "demo child check: gate held open")))
    with TestClient(app) as client:
        r = client.get("/api/sites/KOBO-001/finding-index", params={
            "domain": "mini-grid-dispatch", "from": iso(S), "to": iso(S + timedelta(days=1))})
    assert r.status_code == 200, r.text
    return r.json()


#: DD0c-R Q1: the demo child seals each run once (L1 batching); a parity check may flip it off.
SEAL_ONCE = True


def _seal_once() -> None:
    import test_s6_verification_publication as pub

    pub.SEAL_ONCE = SEAL_ONCE


#: DD1a1-R5: the epochs (Site-days) whose `degraded` story run has had its gateway outage in this build, each
#: mapped to that story run's id (DD1a1-R6: its withheld half is read back after each later complement).
_OUTAGE: dict[str, str] = {}


def gateway_dir(tmp: Path, epoch: str) -> Path:
    """The one gateway state of a Site-day stream (DD1a1-R5)."""
    return tmp / f"gw-{epoch}"


def run_day(store, runner, tmp: Path, day: "sd.DayRun", base: dict) -> dict:
    """One registered Lab run on its story day: draft -> real gateway -> S2 acceptance at `received_at`; when the
    kind assesses at build, S3 assess + S4 match at `received_at + 5 min` (a `tick` day waits for the schedule)."""
    import test_s6_verification_replay as rp

    _seal_once()
    M = day_manifest(base, day)
    spec = M["runs"]["day"]
    run, _ = rp._draft(store, spec, M)
    # DD1a1-R5: every run of a Site-day reopens that day's one gateway state, so the epoch's sequence continues; a
    # complement sends only the instants its `keep` allows (story runs send everything, unchanged).
    stream = {"gateway_dir": gateway_dir(tmp, day.epoch), "keep": day.keep_observation() or day.keep()}
    if day.kind == "degraded":
        deliver = publish_first_half
        _OUTAGE[day.epoch] = str(getattr(run, "run_id", None) or getattr(run, "id", ""))
    elif day.epoch in _OUTAGE:
        deliver = publish_first_half
        stream["outage_continues"] = True
        stream["withheld_run"] = _OUTAGE[day.epoch]
    else:
        deliver = rp._publish_and_accept
    # DD-1a1: a full day holds several runs (story + steady complement), so the work folder names the start too
    published = deliver(tmp / f"{day.day}-{day.kind}-{day.start:%H%M}", run, spec["sequence_epoch"],
                        rp._at(spec["received_at"]), **stream)
    if day.assess == "build":
        runner.now = max(runner.now, day.received_at + timedelta(minutes=5))
        runner.step({"do": "assess"}); runner.step({"do": "match"})
    return {"run_id": str(getattr(run, "run_id", None) or getattr(run, "id", "")), "published": published}


def build(url: str, work: Path, story: dict) -> dict:
    import pg_harness
    import test_s1_bindings_postgres as pgb
    import test_s6_verification_replay as rp
    from sqlalchemy import create_engine, text
    from test_s6_verification_plan_postgres import verifying
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    _OUTAGE.clear()  # DD1a1-R6: a later build in this process does not inherit an outage
    days = [d for d in sd.from_payload(json.loads((work / "days.json").read_text(encoding="utf-8"))["days"])
            if d.site == "kobo"]
    k = story["kobo"]
    install_at = at(k["install_at"])
    M = resolved_manifest(MANIFEST_V3, story)
    tmp = Path(tempfile.mkdtemp(prefix="kobo-replay-", dir=str(work)))
    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    result = pgb.imported(store, when=at(k["import_at"]))
    pgb.convert(store, pgb.BindingService(store, pgb.Clock(install_at)), result.tenant, result.site, pgb.FIXTURE)
    configuration = configure_at(store, result, install_at)
    with engine.begin() as c:
        c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
        c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
    publish_price(url, at(k["price_recorded_at"]))
    first = next(d.received_at for d in days if d.has_run)
    runner = rp.LabRunner(store, engine, result, first + timedelta(minutes=5))
    harness: list = []  # the S6 harness, opened by the trial chain once the trial-day Finding exists
    published, records, ids = {}, [], {}
    try:
        done: set[int] = set()

        def play(n: int, day) -> None:
            entry = {"day": day.day, "offset": day.offset, "kind": day.kind, "as": day.as_kind,
                     "scenario": day.scenario, "run_id": None, "assess": day.assess,
                     "received_at": iso(day.received_at) if day.received_at else None}
            done.add(n)
            if day.has_run:
                entry.update(run_day(store, runner, tmp, day, MANIFEST_V3))
            records.append(entry)
            print("kobo day", day.day, day.kind, entry.get("run_id"), flush=True)

        for n, day in enumerate(days):
            if n in done or day.kind == "trial-after":
                continue  # admitted inside the trial chain, or run by the trial-before entry's chain
            if day.kind == "trial-before":
                later = [d for d in days[n + 1:] if d.kind.startswith("trial-")]
                assert later and later[0].kind == "trial-after", "the trial-after must follow the trial-before"

                def admit(until: datetime, n: int = n) -> None:
                    """DD1a1-R9: every later complement received by `until` is admitted at its `received_at`,
                    between the chain steps, so the evaluation reads data as it stood at its own time."""
                    for m, d in enumerate(days):
                        if m > n and m not in done and not d.kind.startswith("trial-") and d.has_run and d.received_at <= until:
                            play(m, d)

                ids = _trial_chain(store, runner, harness, verifying, tmp, M, published, day.epoch, admit)
                entry = {"day": day.day, "offset": day.offset, "kind": day.kind, "as": day.as_kind,
                         "scenario": day.scenario, "run_id": None, "assess": day.assess,
                         "received_at": iso(day.received_at) if day.received_at else None}
                for d, name in ((day, "baseline"), (later[0], "later")):
                    records.append({**entry, "day": d.day, "offset": d.offset, "kind": d.kind,
                                    "received_at": iso(d.received_at),
                                    "run_id": (ids["runs"][name] or [None])[0]})
                print("kobo trial", day.day, ids["action_code"], flush=True)
                continue
            play(n, day)
        for r in records:
            r["findings"] = findings_on(engine, result.site.id, r["day"])
            r["status_after_build"] = ("NO_RUN" if r["received_at"] is None else
                                       "ASSESSED" if r["assess"] == "build" else "AWAITING_TICK")
        body = trial_day_index(url, runner, at(story["S"]))
        listed = [str(r.get("finding_id")) for r in body.get("rows") or []]
        assert body["status"] == "CURRENT" and ids.get("finding") in listed, (body["status"],
                                                                             body.get("status_reasons"), listed)
        ids["trial_day_index"] = {"status": body["status"], "total_count": body.get("total_count"),
                                  "finding_ids": listed}
        work_rows = write_work(url, store, result, story)
    finally:
        for h in harness:
            h.close()
        pg_harness.dispose(runner.findings)
        pg_harness.dispose(store)
        engine.dispose()
    ids.update({"install_at": k["install_at"], "import_at": k["import_at"],
                "price_recorded_at": k["price_recorded_at"], "configuration": configuration,
                "trial": k["trial"], "window_hour": k["trial"]["window_hour"],
                "published": published, "work": work_rows, "days": records})
    (work / "kobo.json").write_text(json.dumps(ids, indent=2, default=str), encoding="utf-8")
    cc = ids["cost_check"] or {}
    print("kobo:", len([r for r in records if r["run_id"]]), "runs; VERIFIED", ids["action_code"], "cost_check",
          cc.get("state"), cc.get("reason"))
    return ids


def _trial_chain(store, runner, harness: list, verifying, tmp: Path, M: dict, published: dict, epoch: str,
                 admit=lambda until: None) -> dict:
    """The DEMO-A chain (s602b REPLAY body) at the trial pair's place: baseline run, accept, apply, freeze, later
    run, evaluation through the real Action API. DD1a1-R9: `admit(until)` admits the Site's complements received
    by `until` before the freeze, the later run and the evaluation (ACT-K1's steps and instants are unchanged)."""
    import test_s6_verification_replay as rp

    _seal_once()
    act, win = M["action"], M["windows"]
    spec = {**M["runs"]["baseline"], "sequence_epoch": epoch}  # DD1a1-R8: the stream's epoch and gateway state
    base_run, _ = rp._draft(store, spec, M)
    published["baseline"] = rp._publish_and_accept(tmp / "baseline", base_run, spec["sequence_epoch"],
                                                   rp._at(spec["received_at"]),
                                                   gateway_dir=gateway_dir(tmp, spec["sequence_epoch"]))
    runner.now = max(runner.now, rp._at(spec["received_at"]) + timedelta(minutes=5))
    runner.step({"do": "assess"}); runner.step({"do": "match"})
    # The harness's SYSTEM demonstration grant lists the Site's Findings when it opens (fixture_grants snapshot),
    # so it opens after the trial-day Finding is matched, as in the DEMO-A chain.
    h = verifying(runner)
    harness.append(h)
    h.clock.at = rp._at(act["accept_at"])
    finding = h.findings()[act["finding_anchor_day"]]
    rec = h.recommendation(finding).json()
    made = h.accept(finding, rec["proposal"], idempotency_key="demo3-accept-0001")
    assert made.status_code == 201, made.text
    action_id = made.json()["action"]["action_id"]
    h.clock.at = rp._at(act["apply_at"])
    current = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()["application_basis"][
        "current_foundation_revision_id"]
    applied = h.client.post(f"/api/sites/KOBO-001/actions/{action_id}/apply", json={
        "expected_foundation_revision_id": current, "value": act["reserve_new"],
        "effective_from": act["effective_from"], "idempotency_key": "demo3-apply-0001"})
    assert applied.status_code == 201, applied.text
    runner.now = max(runner.now, h.clock.at); runner.step({"do": "assess"}); runner.step({"do": "match"})
    admit(rp._at(M["plan"]["freeze_at"]))
    h.clock.at = max(rp._at(M["plan"]["freeze_at"]), runner.now + timedelta(minutes=1))
    base = f"/api/sites/KOBO-001/actions/{action_id}/verification"
    frozen = h.client.post(f"{base}/plans", json={"baseline_start": win["baseline_start"],
                                                  "later_start": win["later_start"],
                                                  "idempotency_key": "demo3-freeze-0001"})
    assert frozen.status_code == 201, frozen.text
    plan = frozen.json()["plan"]
    spec = {**M["runs"]["later"], "sequence_epoch": epoch}
    admit(rp._at(spec["received_at"]) - timedelta(microseconds=1))
    later_run, _ = rp._draft(store, spec, M)
    published["later"] = rp._publish_and_accept(tmp / "later", later_run, spec["sequence_epoch"],
                                                rp._at(spec["received_at"]),
                                                gateway_dir=gateway_dir(tmp, spec["sequence_epoch"]))
    runner.now = max(runner.now, rp._at(spec["received_at"]) + timedelta(minutes=5))
    runner.step({"do": "assess"}); runner.step({"do": "match"})
    admit(rp._at(M["evaluate_at"]))
    h.clock.at = max(rp._at(M["evaluate_at"]), runner.now + timedelta(minutes=1))
    bound = h.client.post(f"{base}/plans/{plan['plan_id']}/later-selection",
                          json={"idempotency_key": "demo3-bind-0001"})
    assert bound.status_code == 201, bound.text
    made = h.client.post(f"{base}/evaluations", json={"idempotency_key": "demo3-eval-0001"})
    assert made.status_code == 201, made.text
    outcome = made.json()["outcome"]
    assert outcome["outcome"] == "VERIFIED", outcome["reasons"]
    action = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
    events = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}/events").json()["events"]
    sources = outcome["basis"]["source_resolutions"]
    ids = {
        "manifest": {"base": "backend/conversions/d-verification-window-v3.json",
                     "story": "backend/conversions/demo-combined-story-v1.json",
                     "days": "backend/conversions/demo-story-days-v4.json", "scenario": M["scenario"],
                     "model_profile": M["model_profile"], "resolved": {k: M[k] for k in ("runs", "action", "plan",
                                                                                          "windows", "evaluate_at")}},
        "finding": str(finding), "finding_revision": rec["revision_id"],
        "action": action_id, "action_code": action["action"]["action_code"],
        "change": action["change"]["change_id"], "plan": plan["plan_id"],
        "outcome": outcome["outcome_id"], "outcome_recorded_at": outcome["recorded_at"],
        "outcome_reasons": outcome["reasons"],
        "cost_check": (action.get("verification") or {}).get("cost_check"),
        "events": [{"id": e["id"], "kind": e["kind"], "recorded_at": e["recorded_at"]} for e in events],
        "runs": {name: [r.get("run_id") for r in sources[name]["runs"]] for name in ("baseline", "later")},
    }
    return ids


def add_day(url: str, work: Path, planned: dict) -> dict:
    """`demo_combined.py add-day` for KOBO-001: one registered Lab run on a day the calendar does not hold yet,
    delivered on real time (`received_at` = the DB now the parent read). Assessed in process only for `--assess-now`
    (`assess == "build"`); otherwise the running `serve` loop's next tick assesses it."""
    import types

    import pg_harness
    import test_s6_verification_publication as pub
    import test_s6_verification_replay as rp
    from sqlalchemy import create_engine
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    # DD1a2-R Q8.3: a full-day kind arrives as its runs in source-time order; the story run names the day
    runs = sd.from_payload(planned if isinstance(planned, list) else [planned])
    day = next(r for r in runs if not r.complement_of)
    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    foundation = pub.registered.FoundationService(store, "demo", pub.registered.Clock(day.received_at))
    tenant = foundation.tenant()
    result = types.SimpleNamespace(tenant=tenant, site=foundation.site(tenant, "KOBO-001"))
    runner = rp.LabRunner(store, engine, result, day.received_at)
    tmp = Path(tempfile.mkdtemp(prefix="kobo-add-day-", dir=str(work)))
    try:
        out = {}
        for r in runs:
            done = run_day(store, runner, tmp, r, MANIFEST_V3)
            out = done if r is day else out
        out["findings"] = findings_on(engine, result.site.id, day.day) if day.assess == "build" else []
    finally:
        pg_harness.dispose(runner.findings)
        pg_harness.dispose(store)
        engine.dispose()
    print(json.dumps({"added": day.day, "kind": day.kind, **{k: out[k] for k in ("run_id", "findings")}}))
    return out


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "add-day":
        add_day(sys.argv[2], Path(sys.argv[3]), json.loads(sys.argv[4]))
        raise SystemExit(0)
    if len(sys.argv) != 4 or sys.argv[1] != "build":
        raise SystemExit("usage: demo_combined_kobo.py build|add-day <database-url> <work> [<day-json>]")
    work_dir = Path(sys.argv[3])
    build(sys.argv[2], work_dir, json.loads((work_dir / "story.json").read_text(encoding="utf-8")))
