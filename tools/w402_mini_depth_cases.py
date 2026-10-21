"""W4-02 unit 3: authored mini-grid depth cases for MG-W402-001 through the registered gateway path.

`D-2026-10-20-w4-02-buildspec` closure 2 "Role sets and replay source", closure 4 B2/S5/N4 and closure 5. Reads
`backend/conversions/w4-mini-depth-cases-v1.json`, builds public Batch V2 content sealed with MG-W402-001's
registered `minigrid-roles-4` binding snapshot (v3 envelopes for the quantitative channels, v4 envelopes for the
three `authored-mini-depth-cases/1` tuples), posts it with the registered gateway credential to
`POST /api/ingestion/batches`, and writes the replay record: accepted evidence IDs per variant plus the binding and
profile identity. It never targets KOBO-001 and never reads Lab private truth.

Unit 4 step 5 (q3 ruling 12): after `run` and the mini worker (`python -m assetops_backend.mini_depth.worker
run-pending`), `record` adds every persisted `mini_depth_selection.seq` of the Site with its revision UUID, exact
accepted-ID set and provenance basis to the same replay file. No credential material is ever written.

    # once: python -m assetops_backend.sites.w402_demo --tenant demo
    # once: python -m assetops_backend.evidence.provision_gateway issue --tenant demo --site MG-W402-001 ...
    .venv/Scripts/python.exe tools/w402_mini_depth_cases.py run --api https://127.0.0.1:8443 \
        --credential-file <issued credential file> --out var/w402/replay.json
    .venv/Scripts/python.exe -m assetops_backend.mini_depth.worker run-pending --limit 100
    .venv/Scripts/python.exe tools/w402_mini_depth_cases.py record --replay var/w402/replay.json

`DATABASE_URL` names the database that holds MG-W402-001 (read only: snapshot and accepted IDs).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "backend" / "conversions" / "w4-mini-depth-cases-v1.json"
SITE_CODE = "MG-W402-001"
V4_TUPLES = {("mini-primary-bus-meter", "state"), ("mini-generator-controller", "start-event"),
             ("mini-backup-bus-meter", "state")}


def load_spec(path: Path = SPEC_PATH) -> dict[str, Any]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec["site_code"] != SITE_CODE:
        raise SystemExit(f"the authored mini-depth spec targets {spec['site_code']}, not {SITE_CODE}")
    return spec


def _instant(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _z(at: datetime) -> str:
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Planned:
    """One envelope before sequencing: its source time orders it within its source's batch."""

    device: str
    signal: str
    source_time: datetime
    kind: str  # MEAN | POINT | STATE | EVENT
    value: str | None = None
    unit: str | None = None
    interval_start: datetime | None = None
    record_kind: str | None = None
    outcome: str | None = None
    event_id: str | None = None
    correlation_id: str | None = None


def _means(device: str, signal: str, lo: datetime, minutes: Iterable[int], kw: str) -> list[Planned]:
    return [Planned(device, signal, lo + timedelta(minutes=m + 1), "MEAN", kw, "kW", lo + timedelta(minutes=m))
            for m in minutes]


def plan_variant(variant: dict[str, Any]) -> list[Planned]:
    """Every envelope one variant declares, in no particular order."""
    planned: list[Planned] = []
    chain = variant.get("backup_chain")
    for hour in variant["hours"]:
        lo = _instant(hour["from"])
        overrides = {}
        if chain is not None and chain["day"] == hour["day"]:
            for o in chain["mean_overrides_kw"]:
                for m in range(o["from_minute"], o["to_minute"]):
                    overrides[(o["device"], o["signal"], m)] = o["kw"]
        for mean in variant["means_kw"]:
            for m in range(mean.get("from_minute", 0), mean.get("to_minute", 60)):
                kw = overrides.get((mean["device"], mean["signal"], m), mean["kw"])
                planned += _means(mean["device"], mean["signal"], lo, (m,), kw)
        for c in variant.get("conflicting_means_kw", ()):
            planned += _means(c["device"], c["signal"], lo, range(c["from_minute"], c["to_minute"]), c["kw"])
        for p in variant["points"]:
            planned.append(Planned(p["device"], p["signal"], lo + timedelta(minutes=p["minute"]), "POINT",
                                   p["value"], p["unit"]))
    if chain is not None:
        for s in chain["states"]:
            planned.append(Planned(s["device"], s["signal"], _instant(s["at"]), "STATE", s["value"], "state"))
        for e in chain["events"]:
            planned.append(Planned(e["device"], e["signal"], _instant(e["at"]), "EVENT", record_kind=e["record_kind"],
                                   outcome=e["outcome"], event_id=e["event_id"],
                                   correlation_id=chain["correlation_id"]))
    return planned


def _binding(doc: dict[str, Any], device: str, signal: str) -> dict[str, Any]:
    for b in doc["bindings"]:
        if b["device_id"] == device and b["signal_id"] == signal:
            return b
    raise SystemExit(f"{SITE_CODE}'s binding snapshot has no channel {device}/{signal}")


def v3_message_id_for(doc: dict[str, Any], b: dict[str, Any], epoch: str, seq: int) -> str:
    from assetops_contracts.source_envelope_v3 import v3_message_id

    return v3_message_id(site_id=doc["site"]["site_id"], gateway_id=b["gateway_id"], source_id=b["source_id"],
                         sequence_epoch=epoch, sequence=seq)


def seal_for(doc: dict[str, Any], snapshot_sha256: str, b: dict[str, Any], texts: list[str]) -> str:
    """One Batch V2 body for binding row `b`'s source, sealed with the registered snapshot."""
    from assetops_contracts.ingestion_batch_v2 import seal_batch_v2

    _, body = seal_batch_v2(
        site_id=doc["site"]["site_id"], gateway_id=b["gateway_id"], source_id=b["source_id"],
        source_mode=doc["gateway"]["mode"], foundation_version=doc["foundation"]["version"],
        foundation_valid_from=doc["foundation"]["valid_from"], binding_set_id=doc["mapping"]["binding_set_id"],
        binding_version=doc["mapping"]["version"], snapshot_sha256=snapshot_sha256, envelope_texts=texts)
    return body


def _envelope(doc: dict[str, Any], b: dict[str, Any], epoch: str, seq: int, p: Planned) -> str:
    from assetops_contracts.source_envelope import canonical_json

    site = doc["site"]["site_id"]
    message = {"message_id": v3_message_id_for(doc, b, epoch, seq), "sequence_epoch": epoch, "sequence": seq}
    v4 = (p.device, p.signal) in V4_TUPLES
    if p.kind == "EVENT":
        payload: dict[str, Any] = {
            "family": "EVENT", "record_kind": p.record_kind, "event_id": p.event_id,
            "correlation_id": p.correlation_id, "component_id": "generator", "actor": "CONTROLLER",
            "outcome": p.outcome, "unit": None, "value": None, "quality": "GOOD", "session_id": None,
            "connector_id": None}
    else:
        payload = {"family": "MEASUREMENT", "measurement": "INTERVAL_MEAN" if p.kind == "MEAN" else "STATE_AT_INSTANT",
                   "value": p.value, "unit": p.unit, "quality": "GOOD", "unavailable_reason": None}
        if v4:
            payload.update(session_id=None, connector_id=None)
    document = {
        "schema": {"id": "assetops.source-envelope", "version": 4 if v4 else 3},
        "message": message,
        "source": {"site_id": site, "gateway_id": b["gateway_id"], "source_id": b["source_id"],
                   "device_id": p.device, "signal_id": p.signal},
        "mapping": {"binding_set_id": doc["mapping"]["binding_set_id"], "version": doc["mapping"]["version"]},
        "timing": {"source_time": _z(p.source_time), "published_at": _z(p.source_time),
                   "interval_start": None if p.interval_start is None else _z(p.interval_start),
                   "interval_end": None if p.interval_start is None else _z(p.source_time)},
        "payload": payload,
    }
    return canonical_json(document)


@dataclass(frozen=True)
class Batch:
    source_id: str
    device: str
    body: str
    count: int


def build_batches(spec: dict[str, Any], doc: dict[str, Any], snapshot_sha256: str, variant_name: str,
                  *, chunk: int = 200) -> list[Batch]:
    """Sealed Batch V2 bodies for one variant: one source per batch, sequences in source-time order."""
    variant = next(v for v in spec["variants"] if v["variant"] == variant_name)
    epoch = variant["sequence_epoch"]
    by_source: dict[str, list[tuple[Planned, dict[str, Any]]]] = {}
    for p in plan_variant(variant):
        b = _binding(doc, p.device, p.signal)
        by_source.setdefault(b["source_id"], []).append((p, b))
    batches: list[Batch] = []
    for source_id in sorted(by_source):
        rows = sorted(by_source[source_id], key=lambda pb: (pb[0].source_time, pb[0].device, pb[0].signal,
                                                            pb[0].value or "", pb[0].event_id or ""))
        texts = [_envelope(doc, b, epoch, seq, p) for seq, (p, b) in enumerate(rows, start=1)]
        for i in range(0, len(texts), chunk):
            part = texts[i:i + chunk]
            batches.append(Batch(source_id, rows[0][0].device, seal_for(doc, snapshot_sha256, rows[0][1], part),
                                 len(part)))
    return batches


def snapshot_of(connection, site_code: str = SITE_CODE) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """The Site's one current binding snapshot (parsed, sha256) and its identity, read from the database."""
    from sqlalchemy import text

    row = connection.execute(text(
        "SELECT r.id, r.role_set, r.snapshot_canonical FROM signal_binding_set_revision r "
        "JOIN site s ON s.tenant_id = r.tenant_id AND s.id = r.site_id "
        "WHERE s.site_code = :code AND r.superseded_at IS NULL ORDER BY r.version DESC LIMIT 1"),
        {"code": site_code}).one()
    body = bytes(row.snapshot_canonical)
    sha = hashlib.sha256(body).hexdigest()
    return json.loads(body), sha, {"binding_set_revision_id": str(row.id), "role_set": row.role_set,
                                   "snapshot_sha256": sha}


def accepted_ids(connection, site_id: str, message_ids: Iterable[str]) -> list[str]:
    from sqlalchemy import text

    ids = connection.execute(text(
        "SELECT d.accepted_evidence_id FROM ingestion_disposition d WHERE d.site_id = :s "
        "AND d.message_id = ANY(:m) AND d.decision = 'ACCEPTED' ORDER BY d.accepted_evidence_id"),
        {"s": site_id, "m": list(message_ids)}).scalars().all()
    return [str(i) for i in ids]


def message_ids(batches: Iterable[Batch]) -> list[str]:
    from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text

    return [json.loads(t)["message"]["message_id"] for b in batches
            for t in parse_canonical_batch_v2_text(b.body).envelopes]


def replay_record(spec: dict[str, Any], identity: dict[str, Any], doc: dict[str, Any],
                  accepted: dict[str, list[str]]) -> dict[str, Any]:
    """N4: accepted evidence IDs and binding/profile identity only."""
    return {
        "fixture": {"id": spec["schema"]["id"], "version": spec["schema"]["version"]},
        "site_code": SITE_CODE, "site_id": doc["site"]["site_id"], "gateway_id": doc["gateway"]["gateway_id"],
        "binding": identity, "v4_mapping_profile": spec["v4_mapping_profile"],
        "accepted_evidence_ids": accepted,
        "accepted_counts": {k: len(v) for k, v in accepted.items()},
    }


def selection_record(selections: Iterable[Any], site_timezone: str) -> list[dict[str, Any]]:
    """q3 ruling 12: each persisted selection (`mini_depth.store.SelectionRecord`) as replay JSON, in seq order."""
    from zoneinfo import ZoneInfo

    zone = ZoneInfo(site_timezone)
    return [{
        "seq": s.seq, "domain": s.domain, "local_day": s.window_start.astimezone(zone).date().isoformat(),
        "window_start": _z(s.window_start), "window_end": _z(s.window_end), "revision_id": str(s.revision_id),
        "job_id": None if s.job_id is None else str(s.job_id), "model_version": s.model_version,
        "knowledge_cutoff": s.knowledge_cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input_sha256": s.input_sha256, "source_freshness": s.source_freshness,
        "foundation_revision_ids": sorted(str(i) for i in s.foundation_revision_ids),
        "binding_set_revision_ids": sorted(str(i) for i in s.binding_set_revision_ids),
        "accepted_evidence_ids": sorted(str(i) for i in s.evidence_ids),
    } for s in sorted(selections, key=lambda s: s.seq)]


def _post(api: str, credential: str, body: str, *, insecure: bool) -> dict[str, Any]:
    request = urllib.request.Request(api.rstrip("/") + "/api/ingestion/batches", data=body.encode("utf-8"),
                                     method="POST", headers={"Authorization": f"Bearer {credential}",
                                                             "Content-Type": "application/json"})
    context = ssl._create_unverified_context() if insecure else None  # noqa: S323 - local demo host only
    with urllib.request.urlopen(request, context=context) as response:  # noqa: S310 - operator-supplied URL
        return json.loads(response.read())


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - operator entry point
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--api", required=True)
    run.add_argument("--credential-file", required=True)
    run.add_argument("--out", required=True)
    run.add_argument("--insecure", action="store_true", help="accept the local demo host's self-signed TLS")
    record = sub.add_parser("record")
    record.add_argument("--replay", required=True)
    args = parser.parse_args(argv)
    sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "contracts")]
    from sqlalchemy import create_engine

    spec = load_spec()
    engine = create_engine(os.environ["DATABASE_URL"])
    if args.command == "record":
        from assetops_backend.mini_depth.store import PostgresMiniDepthStore

        mini = PostgresMiniDepthStore(engine)
        tenant_id, site_id, zone = mini.site_scope(SITE_CODE)
        path = Path(args.replay)
        replay = json.loads(path.read_text(encoding="utf-8"))
        if zone is None:
            raise SystemExit(f"{SITE_CODE} has no Site timezone; local days cannot be recorded")
        replay["selections"] = selection_record(mini.site_selections(tenant_id, site_id), zone)
        path.write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"selections": len(replay["selections"])}))
        return 0
    with engine.connect() as c:
        doc, sha, identity = snapshot_of(c)
    credential = Path(args.credential_file).read_text(encoding="utf-8").strip()
    accepted: dict[str, list[str]] = {}
    for variant in spec["variants"]:
        batches = build_batches(spec, doc, sha, variant["variant"])
        for b in batches:
            _post(args.api, credential, b.body, insecure=args.insecure)
        with engine.connect() as c:
            accepted[variant["variant"]] = accepted_ids(c, doc["site"]["site_id"], message_ids(batches))
    record = replay_record(spec, identity, doc, accepted)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record["accepted_counts"]))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
