"""S4-01 phase 1 producer: `s4-finding-cases-v1` through the normal S2/S3 path.

Executes the committed specification `backend/conversions/s4-finding-cases-v1.json`
(F01-F06, F08; F07 is test-scoped) against a real deployment shape:

- an isolated `git archive` of HEAD with its own `var/`, database
  `assetops_s4cases` on the Compose Postgres, its own TLS server port (8763);
  KOBO-001 imported, bindings converted, `demo_configuration --steps
  properties,bindings` (minigrid-roles-2);
- a registered gateway credential issued by `provision_gateway issue`; every
  F01-F08 reading is a LABELLED AUTHENTICATED FIXTURE Batch V2 (authored public
  content, sealed with the registered binding snapshot, posted with that
  credential to `POST /api/ingestion/batches` over TLS). Those readings are not
  gateway-sealed Lab output and not operator truth (S2/S3 fault-fixture
  precedent);
- one ordinary-path case, `F01-gateway` (Architect Q6): a registered KOBO-001
  Lab run (`kobo-mini-grid-prolonged` v2 on `mini-grid` v3, roles-2, published
  through `registered-kobo-publication` v3) on 2026-10-02 (template minimum
  runtime; the Lab refuses the 0-minute setup control), sealed by the durable
  registered gateway (epoch `s4-gateway-epoch-1`) and delivered over direct TLS,
  exactly as `tools/s3_dispatch_cases.py` does; then `process-jobs` and
  `match-findings`;
- the battery reserve control through the product API
  `POST /api/sites/KOBO-001/foundation/revisions`; the generator minimum-runtime
  control (no product route in this release) through `FoundationService` in the
  copied tree, labelled as a fixture control;
- `assess_dispatch process-jobs` (the S3 worker) and `assess_dispatch
  match-findings` (the S4 matcher); every expectation is checked against a
  reload through `assess_dispatch finding-rows`.

The spec's `decided` instants are ordering labels only: central acceptance and
publication use the server's real clock, in the same order.

Generated batch, evidence, run and Finding IDs are environment-bound and live
only in the work-dir run artifact (`<work>/s4-finding-cases-run.json`), never
in a committed snapshot. `verify` reloads them from Postgres in a fresh process
and replays the matcher, which must write nothing. Every process `run` starts
is stopped before it exits; it never touches `assetops`, the workspace `var/`
or any server already running.

    .venv/Scripts/python.exe tools/s4_finding_cases.py run      # produce, check, write the run artifact, verify
    .venv/Scripts/python.exe tools/s4_finding_cases.py verify   # reload from Postgres, compare, replay
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s2_demo_walkthrough as s2  # noqa: E402

s2.DEMO_DB = "assetops_s4cases"  # read by Demo at call time; no other database is touched
DEFAULT_WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "s4-finding-cases"
ARTIFACT_NAME = "s4-finding-cases-run.json"
SPEC_PATH = "backend/conversions/s4-finding-cases-v1.json"
DEMO_CONFIG = "backend/conversions/kobo-001-s3-dispatch-demo-config.json"
ASSESS = ("-m", "assetops_backend.analytics.assess_dispatch")
EPOCH_PREFIX = "s4-fixture-"
GATEWAY_EPOCH = "s4-gateway-epoch-1"
GATEWAY_DAY = "02"  # roles-2 day before the 10-03 setup controls: the Lab refuses a 0-minute generator
# minimum runtime (LIFECYCLE_TIMING_NOT_ALIGNED: mini-grid v3 needs a positive multiple of the 5-minute step),
# and the setup controls set it to 0 from 10-03. Run last, so no fixture case sees it.
MODEL = {"profile_id": "mini-grid", "profile_version": 3}
PUBLICATION = {"profile_id": "registered-kobo-publication", "profile_version": 3}
SCENARIO = ("kobo-mini-grid-prolonged", 2)
RUNTIME_CONTROL = r"""
import json, sys
from datetime import datetime
from assetops_backend.config import database_url
from assetops_backend.sites.composition import build_foundation_store
from assetops_backend.sites.foundation_service import FoundationService, utc_now
value, effective_from, note = int(sys.argv[1]), datetime.fromisoformat(sys.argv[2].replace("Z", "+00:00")), sys.argv[3]
service = FoundationService(build_foundation_store(database_url()), "demo", utc_now)
tenant = service.tenant()
site = service.site(tenant, "KOBO-001")
result = service.publish_component_properties(tenant, site, asset_code="generator", properties=[
    {"property_key": "minimum-runtime", "value": value, "unit": "min", "source": "TEMPLATE", "source_version": 2}],
    effective_from=effective_from, note=note)
print(json.dumps({"revision_id": str(result.changed.id)}))
"""
say, step = s2.say, s2.step


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def z(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def digest(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def block_rows(block: dict[str, Any], rules: dict[str, Any]) -> list[tuple]:
    """The spec's reading rules (identical to `test_s4_finding_store_postgres.block_rows`)."""
    stride = timedelta(minutes=rules["step_minutes"])
    sig = rules["signals"]
    only = set(block.get("only") or ("state", "load", "pv", "dis", "soc"))
    rows: list[tuple] = []
    start, end = instant(block["from"]), instant(block["to"])
    if block.get("stop_before"):
        rows.append((*sig["state"], start - stride, "STOPPED"))
    t = start
    while t <= end:
        if "state" in only:
            rows.append((*sig["state"], t, "RUNNING"))
        if "load" in only:
            rows += [(f, None, t, rules["feeder_kw"]) for f in rules["feeders"]]
        for key in ("pv", "dis", "soc"):
            if key in only and key in block:
                rows.append((*sig[key], t, block[key]))
        t += stride
    if block.get("stop_after"):
        rows.append((*sig["state"], end + stride, "STOPPED"))
    return rows


class Cases(s2.Demo):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        self.artifact_path = Path(args.artifact).resolve() if args.artifact else self.work / ARTIFACT_NAME
        self.spec = json.loads((s2.REPO / SPEC_PATH).read_text(encoding="utf-8"))
        self.seq: dict[tuple[str, str], int] = {}
        self.held: dict[str, list[tuple[str, str]]] = {}
        self.cases: list[dict[str, Any]] = []
        self.controls: list[dict[str, Any]] = []
        self.failures: list[str] = []

    def gateway_address(self) -> str:  # started only for F01-gateway; distinct from every other producer
        return r"\\.\pipe\assetops-s4-cases-gateway" if sys.platform == "win32" else str(self.gw / "gw.sock")

    def write_gateway_config(self, snap: dict[str, Any], credential: Path) -> None:
        super().write_gateway_config(snap, credential)
        path = self.gw / "gateway.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["provisioning"]["sequence_epoch"] = GATEWAY_EPOCH
        path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # ------------------------------------------------------------ helpers
    def pg(self, sql: str, *params: Any) -> list[tuple]:
        import psycopg

        with psycopg.connect(self.db_url.replace("postgresql+psycopg://", "postgresql://")) as conn:
            return conn.execute(sql, params).fetchall()

    def cli(self, *argv: str) -> Any:
        return json.loads(self.py(*ASSESS, *argv).stdout.strip().splitlines()[-1])

    def site_args(self) -> list[str]:
        return ["--tenant-id", self.identity["tenant_id"], "--site-id", self.identity["site_id"]]

    def binding(self, device: str, signal: str | None = None) -> dict[str, Any]:
        return next(b for b in self.doc["bindings"] if b["device_id"] == device and signal in (None, b["signal_id"]))

    # ------------------------------------------------------------ setup
    def prepare(self) -> None:
        step("2. TLS product server, registered gateway credential, demo configuration (roles-2)")
        self.start_tls()
        [(gateway_external_id,)] = self.pg("SELECT g.gateway_external_id FROM gateway g JOIN site s ON s.id = "
                                           "g.site_id WHERE s.site_code = %s", s2.SITE)
        self.gateway_external_id = gateway_external_id
        sources = [r[0] for r in self.pg("SELECT o.source_external_id FROM source o JOIN site s ON s.id = "
                                         "o.site_id WHERE s.site_code = %s ORDER BY 1", s2.SITE)]
        self.credential = self.issue(sources)
        out = self.py("-m", "assetops_backend.sites.demo_configuration", "--fixture", DEMO_CONFIG,
                      "--tenant", "demo", "--steps", "properties,bindings").stdout.strip().splitlines()
        say("  " + out[0][:200])
        self.periods = json.loads(out[-1])["periods"]
        # The pinned snapshot every fixture batch is sealed against: the latest registered binding set
        # (minigrid-roles-2), exactly as the Postgres test's CaseRunner pins it.
        [(set_id, body)] = self.pg(
            "SELECT r.id::text, r.snapshot_canonical FROM signal_binding_set_revision r JOIN site s ON s.id = "
            "r.site_id WHERE s.site_code = %s ORDER BY r.valid_from DESC, r.recorded_at DESC LIMIT 1", s2.SITE)
        body = bytes(body)
        self.doc, self.snapshot_sha = json.loads(body), hashlib.sha256(body).hexdigest()
        self.identity = {"tenant_id": self.doc["tenant_id"], "site_id": self.doc["site"]["site_id"],
                         "site_code": s2.SITE, "gateway_id": self.doc["gateway"]["gateway_id"],
                         "gateway_external_id": gateway_external_id, "binding_set_revision_id": set_id,
                         "binding_version": self.doc["mapping"]["version"], "snapshot_sha256": self.snapshot_sha}
        say(f"  sealing basis: binding set v{self.doc['mapping']['version']} ({set_id}), Foundation "
            f"v{self.doc['foundation']['version']}, snapshot {self.snapshot_sha[:16]}..")
        step("3. Setup controls (labelled fixture controls)")
        for control in self.spec["setup"]:
            self.control(control, "setup")

    # ------------------------------------------------------------ steps
    def post(self, envelopes: list[tuple[str, str]]) -> list[str]:
        from assetops_contracts.ingestion_batch_v2 import seal_batch_v2

        by_device: dict[str, list[str]] = {}
        for device, text in envelopes:
            by_device.setdefault(device, []).append(text)
        batch_ids = []
        for device, texts in by_device.items():
            b = self.binding(device)
            batch_id, body = seal_batch_v2(
                site_id=self.doc["site"]["site_id"], gateway_id=b["gateway_id"], source_id=b["source_id"],
                source_mode=self.doc["gateway"]["mode"], foundation_version=self.doc["foundation"]["version"],
                foundation_valid_from=self.doc["foundation"]["valid_from"],
                binding_set_id=self.doc["mapping"]["binding_set_id"], binding_version=self.doc["mapping"]["version"],
                snapshot_sha256=self.snapshot_sha, envelope_texts=texts)
            status, receipt = self.call("POST", "/api/ingestion/batches", raw=body.encode("utf-8"), base=self.https,
                                        headers=self.bearer(self.credential))
            if status != 200 or (receipt or {}).get("status") != "COMPLETED":
                raise SystemExit(f"fixture batch {batch_id} ({device}) refused: {status} {receipt}")
            batch_ids.append(json.loads(body)["batch_id"])
        return batch_ids

    def seal(self, rows: list[tuple[tuple, str | None]], epoch: str) -> tuple[list, list]:
        """Sequence every row in source-time order (a gateway numbers readings as it takes them); a held row
        keeps its earlier sequence but is delivered by a later release step (late central acceptance)."""
        from assetops_contracts.source_envelope_v3 import SourceEnvelopeV3, canonical_envelope_v3_text, v3_message_id

        now, later = [], []
        for (device, signal, when, value), held in rows:
            b = self.binding(device, signal)
            key = (b["source_id"], epoch)
            self.seq[key] = self.seq.get(key, 0) + 1
            envelope = SourceEnvelopeV3(
                message_id=v3_message_id(site_id=self.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                         source_id=b["source_id"], sequence_epoch=epoch, sequence=self.seq[key]),
                sequence_epoch=epoch, sequence=self.seq[key], site_id=self.doc["site"]["site_id"],
                gateway_id=b["gateway_id"], source_id=b["source_id"], device_id=device, signal_id=b["signal_id"],
                binding_set_id=self.doc["mapping"]["binding_set_id"], binding_version=self.doc["mapping"]["version"],
                source_time=z(when), published_at=z(when), interval_start=None, interval_end=None,
                family="MEASUREMENT", measurement="STATE_AT_INSTANT", value=value, unit=b["source_unit"],
                quality="GOOD", unavailable_reason=None)
            item = (device, canonical_envelope_v3_text(envelope))
            (later.append((held, item)) if held else now.append(item))
        return now, later

    def control(self, control: dict[str, Any], case_id: str) -> None:
        note = f"{self.spec['label']}: labelled fixture control"
        if control["do"] == "reserve":
            status, out = self.call("POST", f"/api/sites/{s2.SITE}/foundation/revisions", base=self.https, body={
                "asset_code": "battery", "property_key": "reserve-state-of-charge", "value": control["value"],
                "unit": "%", "valid_from": control["effective_from"], "note": note})
            if status != 201:
                raise SystemExit(f"reserve control refused: {status} {out}")
            revision = out["revision"].get("revision_id") or out["revision"].get("id")
        else:
            revision = json.loads(self.py("-c", RUNTIME_CONTROL, str(control["value"]), control["effective_from"],
                                          note).stdout.strip().splitlines()[-1])["revision_id"]
        self.controls.append({"case": case_id, "do": control["do"], "value": control["value"],
                              "effective_from": control["effective_from"], "foundation_revision_id": revision})
        say(f"  {case_id}: {control['do']} = {control['value']} from {control['effective_from']} "
            f"(Foundation revision {revision})")

    def rows(self) -> dict[str, Any]:
        return self.cli("finding-rows", *self.site_args())

    def check(self, outcome: dict[str, Any], expect: list[dict], case_id: str, collateral: bool) -> list[str]:
        """The Postgres test's expectation check, against a reload through `finding-rows`."""
        rows = self.rows()
        problems: list[str] = []
        by_anchor = {instant(f["anchor_start"]): f for f in rows["findings"]}
        by_id = {f["id"]: f for f in rows["findings"]}
        new = [r for r in rows["revisions"] if r["id"] in outcome["revision_ids"]]
        if collateral:
            named = {instant(e["anchor"]) for e in expect if e["anchor"] != "SPLIT_PART"}
            for r in [r for r in new if instant(by_id[r["finding_id"]]["anchor_start"]) not in named]:
                [prior] = [p for p in rows["revisions"] if p["finding_id"] == r["finding_id"]
                           and p["revision_no"] == r["revision_no"] - 1]
                if not (r["transition"] == "BASIS_REFRESHED" and r["lifecycle"] == prior["lifecycle"]
                        and r["support_sha256"] == prior["support_sha256"]
                        and (r["episode_start"], r["episode_end"], str(r["candidate_minutes"]))
                        == (prior["episode_start"], prior["episode_end"], str(prior["candidate_minutes"]))
                        and r["assessment_revision_id"] != prior["assessment_revision_id"]):
                    problems.append(f"collateral revision {r['id']} is not a provenance-only BASIS_REFRESHED")
                new.remove(r)
        if len(new) != len(expect):
            return problems + [f"{len(new)} new revisions, expected {len(expect)}: "
                               f"{[(r['transition'], r['episode_start']) for r in new]}"]
        for e in expect:
            if e["anchor"] == "SPLIT_PART":
                finding = next((by_id[r["finding_id"]] for r in new if by_id[r["finding_id"]]["split_from_finding_id"]),
                               None)
            else:
                finding = by_anchor.get(instant(e["anchor"]))
            if finding is None:
                problems.append(f"no Finding anchored at {e['anchor']}")
                continue
            revs = [r for r in new if r["finding_id"] == finding["id"]]
            if len(revs) != 1:
                problems.append(f"{e['anchor']}: {len(revs)} new revisions")
                continue
            rev = revs[0]
            want = {"transition": e["transition"], **{k: e[k] for k in ("lifecycle", "revision_no") if k in e}}
            for key, value in want.items():
                if rev[key] != value:
                    problems.append(f"{e['anchor']}: {key} {rev[key]} != {value}")
            if (finding["id"] in outcome["finding_ids"]) != bool(e.get("new")):
                problems.append(f"{e['anchor']}: new={finding['id'] in outcome['finding_ids']}")
            if "episode" in e and [instant(rev["episode_start"]), instant(rev["episode_end"])] != [
                    instant(x) for x in e["episode"]]:
                problems.append(f"{e['anchor']}: episode {rev['episode_start']}..{rev['episode_end']}")
            if "necessary_minutes_gt" in e and not (float(rev["necessary_minutes"]) > e["necessary_minutes_gt"]
                                                    and float(rev["candidate_minutes"]) > 0):
                problems.append(f"{e['anchor']}: minutes {rev['necessary_minutes']}/{rev['candidate_minutes']}")
            if "interval_citations" in e:
                cites = [a for a in rows["assessments"] if a["finding_revision_id"] == rev["id"]
                         and a["scope"] == "INTERVAL"]
                if len(cites) != e["interval_citations"]:
                    problems.append(f"{e['anchor']}: {len(cites)} interval citations")
            for key, column in (("recurs_after", "recurs_after_finding_id"), ("split_from", "split_from_finding_id")):
                if key in e:
                    want_id = None if e[key] is None else by_anchor[instant(e[key])]["id"]
                    if finding[column] != want_id:
                        problems.append(f"{e['anchor']}: {column} {finding[column]} != {want_id}")
            if "merged_into" in e:
                merges = [m for m in rows["merges"] if m["superseded_finding_id"] == finding["id"]]
                if [m["canonical_finding_id"] for m in merges] != [by_anchor[instant(e["merged_into"])]["id"]]:
                    problems.append(f"{e['anchor']}: merge {merges}")
            if rev["lifecycle"] == "SUPPORTED" and not [x for x in rows["evidence"]
                                                         if x["finding_revision_id"] == rev["id"]]:
                problems.append(f"{e['anchor']}: a SUPPORTED revision cites no accepted evidence")
        return problems

    def run_case(self, case: dict[str, Any]) -> None:
        record: dict[str, Any] = {"case_id": case["case_id"], "label": case["label"], "day": case["day"],
                                  "batch_ids": [], "matches": []}
        rules = self.spec["reading_rules"]
        for spec_step in case["steps"]:
            do = spec_step["do"]
            if do == "deliver":
                epoch = EPOCH_PREFIX + spec_step.get("epoch", "epoch-1")
                rows = [(r, None) for b in spec_step["blocks"] for r in block_rows(b, rules)]
                rows += [(r, name) for name, blocks in spec_step.get("held", {}).items() for b in blocks
                         for r in block_rows(b, rules)]
                now, later = self.seal(sorted(rows, key=lambda x: x[0][2]), epoch)
                for name, item in later:
                    self.held.setdefault(name, []).append(item)
                batches = self.post(now)
                record["batch_ids"] += batches
                say(f"  {case['case_id']} deliver ({epoch}): {len(now)} readings in {len(batches)} batches; "
                    f"held {sorted({n for n, _ in later})}")
            elif do == "release":
                batches = self.post(self.held.pop(spec_step["name"]))
                record["batch_ids"] += batches
                say(f"  {case['case_id']} release {spec_step['name']}: {len(batches)} batches ({spec_step['label']})")
            elif do == "assess":
                outcomes = self.cli("process-jobs")
                bad = [o for o in outcomes if o["status"] != "DONE"]
                say(f"  {case['case_id']} assess: {len(outcomes)} job(s), "
                    f"{sum(len(o['runs']) for o in outcomes)} run(s)" + (f", NOT DONE {bad}" if bad else ""))
                if bad:
                    self.failures.append(f"{case['case_id']} assess: {bad}")
            elif do in ("reserve", "runtime"):
                self.control(spec_step, case["case_id"])
            elif do == "match":
                outcome = self.cli("match-findings", *self.site_args())
                problems = self.check(outcome, spec_step["expect"], case["case_id"], bool(spec_step.get("collateral")))
                record["matches"].append({"planned": outcome["planned"], "finding_ids": outcome["finding_ids"],
                                          "revision_ids": outcome["revision_ids"], "expected": len(spec_step["expect"]),
                                          "collateral": bool(spec_step.get("collateral")), "problems": problems})
                say(f"  {case['case_id']} match: planned {outcome['planned']}, new Findings "
                    f"{len(outcome['finding_ids'])}, new revisions {len(outcome['revision_ids'])}, "
                    f"expected {len(spec_step['expect'])}" + ("" if not spec_step.get("collateral") else " + collateral")
                    + (" OK" if not problems else f" FAILED {problems}"))
                self.failures += [f"{case['case_id']}: {p}" for p in problems]
        ids = [r[0] for r in self.pg("SELECT e.id::text FROM accepted_evidence e JOIN ingestion_batch b ON "
                                     "b.id = e.batch_id WHERE b.external_batch_id = ANY(%s)", record["batch_ids"])]
        record["evidence_count"], record["evidence_id_sha256"] = len(ids), digest(ids)
        self.cases.append(record)

    # ------------------------------------------------------------ ordinary gateway path (Architect Q6)
    def gateway_case(self) -> None:
        """One registered Lab run sealed by the durable gateway and delivered over TLS (S3 `run_case` pattern)."""
        self.start_lab()
        snap = self.snapshot()
        self.write_gateway_config(snap, self.credential)
        self.start_gateway()
        start, end = f"2026-10-{GATEWAY_DAY}T03:00:00Z", f"2026-10-{GATEWAY_DAY}T11:00:00Z"
        status, at = self.call("GET", f"/api/sites/{s2.SITE}/foundation/snapshot?at={start}")
        if status != 200:
            raise SystemExit(f"Foundation snapshot at {start}: {status} {at}")
        foundation_version = at["foundation"]["version"]
        body = {"site_id": s2.SITE, "foundation_version": foundation_version, "scenario_id": SCENARIO[0],
                "scenario_version": SCENARIO[1], "interval": {"start_time": start, "end_time": end},
                "timestep_minutes": 5, "seed": self.spec["seed"], "model_profile": MODEL,
                "publication_profile": PUBLICATION, "run_inputs": []}
        run = self.lab("POST", "/runs", body, expect=201)["run"]
        if run.get("execution_status") != "READY":
            raise SystemExit(f"F01-gateway: run {run['run_id']} is {run.get('execution_status')}: "
                             f"{json.dumps(run.get('blocking_reasons'))[:600]}")
        before = set(self.sealed_inventory())
        self.lab("POST", f"/runs/{run['run_id']}/execution/start")
        self.lab("POST", f"/runs/{run['run_id']}/execution/run-to-end")
        published_to = z(instant(end) + timedelta(minutes=15))
        self.lab("POST", f"/runs/{run['run_id']}/publication/advance", {"instant": published_to}, expect=None)
        self.lab("POST", f"/runs/{run['run_id']}/commit", expect=None)
        self.deliver_all("F01-gateway")
        batches = sorted(set(self.sealed_inventory()) - before)
        accepted = self.pg("SELECT e.sequence_epoch, e.gateway_id::text, COUNT(*) FROM accepted_evidence e "
                           "JOIN ingestion_batch b ON b.id = e.batch_id WHERE b.external_batch_id = ANY(%s) "
                           "GROUP BY 1, 2", batches)
        say(f"  F01-gateway: {SCENARIO[0]} v{SCENARIO[1]} {start}..{end} on Foundation v{foundation_version}; "
            f"{len(batches)} sealed batches delivered; accepted (epoch, gateway, readings) {accepted}")
        record: dict[str, Any] = {
            "case_id": "F01-gateway", "label": "ordinary registered gateway path: Lab run sealed by the durable "
            "gateway, delivered over direct TLS (Architect Q6)", "day": start[:10], "batch_ids": batches,
            "sequence_epochs": sorted({r[0] for r in accepted}), "gateway_ids": sorted({r[1] for r in accepted}),
            "foundation_version": foundation_version, "matches": []}
        problems = []
        if [r[0] for r in accepted] != [GATEWAY_EPOCH] or [r[1] for r in accepted] != [self.identity["gateway_id"]]:
            problems.append(f"accepted evidence is not sealed by the registered gateway under {GATEWAY_EPOCH}")
        outcomes = self.cli("process-jobs")
        if [o for o in outcomes if o["status"] != "DONE"]:
            problems.append(f"assess: {outcomes}")
        outcome = self.cli("match-findings", *self.site_args())
        rows = self.rows()
        opened = [f for f in rows["findings"] if f["anchor_start"][:10] == start[:10]]
        revs = [r for r in rows["revisions"] if r["finding_id"] in {f["id"] for f in opened}]
        if not opened or any(r["transition"] != "OPENED" or r["lifecycle"] != "SUPPORTED" for r in revs):
            problems.append(f"expected OPENED SUPPORTED Finding(s) on {start[:10]}: "
                            f"{[(r['transition'], r['lifecycle']) for r in revs]}")
        record["matches"].append({"planned": outcome["planned"], "finding_ids": outcome["finding_ids"],
                                  "revision_ids": outcome["revision_ids"], "opened_on_day": [
                                      {"finding_id": f["id"], "anchor_start": f["anchor_start"]} for f in opened],
                                  "problems": problems})
        say(f"  F01-gateway match: planned {outcome['planned']}, new Findings {len(outcome['finding_ids'])}, "
            f"Findings anchored {start[:10]}: {[(f['anchor_start'], f['recurs_after_finding_id']) for f in opened]}"
            + (" OK" if not problems else f" FAILED {problems}"))
        self.failures += [f"F01-gateway: {p}" for p in problems]
        ids = [r[0] for r in self.pg("SELECT e.id::text FROM accepted_evidence e JOIN ingestion_batch b ON "
                                     "b.id = e.batch_id WHERE b.external_batch_id = ANY(%s)", batches)]
        record["evidence_count"], record["evidence_id_sha256"] = len(ids), digest(ids)
        self.cases.append(record)

    # ------------------------------------------------------------ artifact
    @staticmethod
    def finding_listing(rows: dict[str, Any]) -> list[dict[str, Any]]:
        out = []
        for f in rows["findings"]:
            revs = [r for r in rows["revisions"] if r["finding_id"] == f["id"]]
            out.append({"finding_id": f["id"], "finding_key": f["finding_key"], "anchor_start": f["anchor_start"],
                        "recurs_after_finding_id": f["recurs_after_finding_id"],
                        "split_from_finding_id": f["split_from_finding_id"],
                        "revisions": [{"revision_id": r["id"], "revision_no": r["revision_no"],
                                       "transition": r["transition"], "lifecycle": r["lifecycle"],
                                       "assessment_revision_id": r["assessment_revision_id"],
                                       "run_id": r.get("run_id"), "basis_sha256": r["basis_sha256"],
                                       "episode": [r["episode_start"], r["episode_end"]]} for r in revs]})
        return out

    def write_artifact(self) -> None:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=s2.REPO, capture_output=True,
                                text=True).stdout.strip()
        rows = self.rows()
        artifact = {
            "schema": {"id": "s4-finding-cases-run", "version": 1},
            "label": self.spec["label"],
            "status": "ENVIRONMENT-BOUND RUN ARTIFACT of the labelled authenticated fixture specification "
                      f"{SPEC_PATH}. Batch, evidence, run and Finding IDs are per run (each run recreates the "
                      "database); never commit this file as a current snapshot. Not field evidence.",
            "produced_from_commit": commit,
            "spec_sha256": hashlib.sha256((s2.REPO / SPEC_PATH).read_bytes()).hexdigest(),
            "database": s2.DEMO_DB,
            "site": self.identity,
            "demo_configuration_periods": self.periods,
            "controls": self.controls,
            "cases": self.cases,
            "findings": self.finding_listing(rows),
            "counts": {k: len(v) for k, v in rows.items()},
            "failures": self.failures,
        }
        self.artifact_path.write_text(json.dumps(artifact, indent=2, default=str), encoding="utf-8")
        say(f"  run artifact: {self.artifact_path} ({len(rows['findings'])} Findings, "
            f"{len(rows['revisions'])} revisions; failures {len(self.failures)})")

    def verify(self) -> int:
        """Fresh process: reload every Finding row and accepted evidence ID, compare, replay the matcher."""
        artifact = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        self.identity = artifact["site"]
        failures = list(artifact["failures"])
        for case in artifact["cases"]:
            ids = [r[0] for r in self.pg("SELECT e.id::text FROM accepted_evidence e JOIN ingestion_batch b ON "
                                         "b.id = e.batch_id WHERE b.external_batch_id = ANY(%s)", case["batch_ids"])]
            same = len(ids) == case["evidence_count"] and digest(ids) == case["evidence_id_sha256"]
            say(f"  verify {case['case_id']}: {len(ids)} accepted readings reloaded, match={same}")
            if not same:
                failures.append(f"{case['case_id']} evidence")
        reloaded = self.finding_listing(self.rows())
        same = json.loads(json.dumps(reloaded, default=str)) == artifact["findings"]
        say(f"  verify Findings: {len(reloaded)} Findings, "
            f"{sum(len(f['revisions']) for f in reloaded)} revisions reloaded, match={same}")
        if not same:
            failures.append("Finding rows")
        replay = self.cli("match-findings", *self.site_args())
        say(f"  replay match-findings: planned {replay['planned']}, new revisions {len(replay['revision_ids'])}")
        if replay["planned"] or replay["revision_ids"] or replay["finding_ids"]:
            failures.append("replay wrote")
        say("VERIFY " + ("PASSED" if not failures else f"FAILED: {failures}"))
        return 0 if not failures else 1

    def run(self) -> None:
        self.setup()
        try:
            self.prepare()
            for n, case in enumerate(self.spec["cases"], start=4):
                step(f"{n}. {case['case_id']} {case['label']} ({case['day']})")
                self.run_case(case)
            step(f"{n + 1}. F01-gateway: ordinary registered gateway path (Lab run, durable gateway, TLS)")
            self.gateway_case()
            step(f"{n + 2}. Run artifact")
            self.write_artifact()
        finally:
            step("Stopping every process this script started")
            self.stop_all()
            say("  stopped: tls-server, lab-api, gateway")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s4_finding_cases.py")
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--work", default=str(DEFAULT_WORK))
    parser.add_argument("--artifact", default=None, help=f"default: <work>/{ARTIFACT_NAME}")
    parser.add_argument("--tls-port", type=int, default=8763)
    parser.add_argument("--http-port", type=int, default=8730)  # Lab/product API for F01-gateway
    parser.add_argument("--cadence-seconds", type=int, default=60)
    args = parser.parse_args(argv)
    if args.command == "run":
        started = time.time()
        cases = Cases(args)
        cases.run()
        say(f"Produced in {time.time() - started:.0f} s ({len(cases.failures)} check failures). "
            "Verifying after reload in a fresh process:")
        done = subprocess.run([str(s2.PY), __file__, "verify", "--work", args.work,
                               *(["--artifact", args.artifact] if args.artifact else [])])
        return 1 if cases.failures else done.returncode
    return Cases(args).verify()


if __name__ == "__main__":
    raise SystemExit(main())
