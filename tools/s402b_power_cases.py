"""S4-02b phase 2a producer: `s4-finding-cases-v1` plus the authored power-mean demonstration case.

Owner ruling `.agent/owner-S4-02b-money-demo-2026-10-14.md`. This runs `tools/s4_finding_cases.py` unchanged
(the S4 Finding cases F01-F08 and the ordinary F01-gateway Lab case) into its OWN database
`assetops_s402bcases` and work folder, then executes `backend/conversions/s4-power-demo-cases-v1.json`
(`P01-power`, 2026-10-23) through the same deployment shape: authored public generator-controller ac-power
INTERVAL_MEAN envelopes (back-to-back 5-minute means) and Candidate context rows, sealed with the registered
binding snapshot and posted with the registered gateway credential to `POST /api/ingestion/batches` over TLS;
then `process-jobs` and `match-findings`, checked against a reload. `assetops_s4cases` and its evidence are
never touched, so S4-01/S4-03 evidence stays valid.

The resulting database is the template for the S4-02b phase 2b owner walkthrough: copy it, publish the SYSTEM
price fixture steps (`python -m assetops_backend.publish_assumption fixture ... --step v1 --step v2 --step v3`),
then `python -m assetops_backend.recompute_consequences run --tenant demo --site KOBO-001` (S4-02c: bounded
by `--limit`, repeat until the summary line's backlog is 0); publish `--step v4` and run the
recompute again for the old/new consequence revisions. Its migration 0011 triggers enqueue a recompute for
every FindingRevision, so P01-power gives a positive amount and F01-gateway stays `POWER_COVERAGE_GAP`.

    .venv/Scripts/python.exe tools/s402b_power_cases.py run      # produce, check, write the run artifact, verify
    .venv/Scripts/python.exe tools/s402b_power_cases.py verify   # reload from Postgres, compare, replay
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import s4_finding_cases as s4  # noqa: E402

s2 = s4.s2
s2.DEMO_DB = "assetops_s402bcases"  # read by Demo at call time; assetops_s4cases is never touched
DEFAULT_WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "s402b-power-cases"
POWER_SPEC_PATH = "backend/conversions/s4-power-demo-cases-v1.json"


class PowerCases(s4.Cases):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        self.power_spec = json.loads((s2.REPO / POWER_SPEC_PATH).read_text(encoding="utf-8"))

    def power_envelopes(self, step: dict[str, Any], epoch: str) -> list[tuple[str, str]]:
        from assetops_contracts.source_envelope_v3 import SourceEnvelopeV3, canonical_envelope_v3_text, v3_message_id

        rules = self.power_spec["power_rules"]
        b = self.binding(rules["device"], rules["signal"])
        out = []
        for block in step["means"]:
            end = s4.instant(block["first_end"])
            while end <= s4.instant(block["last_end"]):
                key = (b["source_id"], epoch)
                self.seq[key] = self.seq.get(key, 0) + 1
                envelope = SourceEnvelopeV3(
                    message_id=v3_message_id(site_id=self.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                             source_id=b["source_id"], sequence_epoch=epoch, sequence=self.seq[key]),
                    sequence_epoch=epoch, sequence=self.seq[key], site_id=self.doc["site"]["site_id"],
                    gateway_id=b["gateway_id"], source_id=b["source_id"], device_id=rules["device"],
                    signal_id=b["signal_id"], binding_set_id=self.doc["mapping"]["binding_set_id"],
                    binding_version=self.doc["mapping"]["version"], source_time=s4.z(end), published_at=s4.z(end),
                    interval_start=s4.z(end - timedelta(minutes=rules["mean_minutes"])), interval_end=s4.z(end),
                    family="MEASUREMENT", measurement=rules["measurement"], value=block["kw"],
                    unit=b["source_unit"], quality=rules["quality"], unavailable_reason=None)
                out.append((rules["device"], canonical_envelope_v3_text(envelope)))
                end += timedelta(minutes=rules["mean_minutes"])
        return out

    def run_power_case(self, case: dict[str, Any]) -> None:
        record: dict[str, Any] = {"case_id": case["case_id"], "label": case["label"], "day": case["day"],
                                  "spec": self.power_spec["label"], "batch_ids": [], "matches": []}
        for spec_step in case["steps"]:
            do = spec_step["do"]
            if do == "deliver_power":
                epoch = s4.EPOCH_PREFIX + spec_step["epoch"]
                context = s4.block_rows(spec_step["context"], self.spec["reading_rules"])
                now, _ = self.seal([(r, None) for r in sorted(context, key=lambda x: x[2])], epoch + "-context")
                power = self.power_envelopes(spec_step, epoch)
                record["batch_ids"] += self.post(power + now)
                say(f"  {case['case_id']} deliver_power ({epoch}): {len(power)} power means, {len(now)} context "
                    f"readings")
            elif do in ("assess", "match"):
                before = len(self.cases)
                self.run_case({"case_id": case["case_id"], "label": case["label"], "day": case["day"],
                               "steps": [spec_step]})
                sub = self.cases.pop(before)
                record["matches"] += sub["matches"]
        ids = [r[0] for r in self.pg("SELECT e.id::text FROM accepted_evidence e JOIN ingestion_batch b ON "
                                     "b.id = e.batch_id WHERE b.external_batch_id = ANY(%s)", record["batch_ids"])]
        record["evidence_count"], record["evidence_id_sha256"] = len(ids), s4.digest(ids)
        self.case_evidence[record["case_id"]] = ids
        self.cases.append(record)

    def run(self) -> None:
        self.setup()
        try:
            self.prepare()
            n = 3
            for n, case in enumerate(self.spec["cases"], start=4):
                step(f"{n}. {case['case_id']} {case['label']} ({case['day']})")
                self.run_case(case)
            step(f"{n + 1}. F01-gateway: ordinary registered gateway path (Lab run, durable gateway, TLS)")
            self.gateway_case()
            for k, case in enumerate(self.power_spec["cases"], start=n + 2):
                step(f"{k}. {case['case_id']} {case['label']} ({case['day']}, {self.power_spec['label']})")
                self.run_power_case(case)
            step("Run artifact")
            self.write_artifact()
        finally:
            step("Stopping every process this script started")
            self.stop_all()
            say("  stopped: tls-server, lab-api, gateway")


def say(text: str) -> None:
    s4.say(text)


def step(text: str) -> None:
    s4.step(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s402b_power_cases.py")
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--work", default=str(DEFAULT_WORK))
    parser.add_argument("--artifact", default=None, help=f"default: <work>/{s4.ARTIFACT_NAME}")
    parser.add_argument("--tls-port", type=int, default=8904)
    parser.add_argument("--http-port", type=int, default=8905)  # Lab/product API for F01-gateway
    parser.add_argument("--cadence-seconds", type=int, default=60)
    parser.add_argument("--db", default=s2.DEMO_DB, help="own database (dropped and recreated by run)")
    args = parser.parse_args(argv)
    if args.db in ("assetops", "assetops_s4cases") or not args.db.startswith("assetops_s402b"):
        raise SystemExit(f"Refusing database {args.db!r}: use an assetops_s402b* database of its own.")
    s2.DEMO_DB = args.db
    if args.command == "run":
        started = time.time()
        cases = PowerCases(args)
        cases.run()
        say(f"Produced in {time.time() - started:.0f} s ({len(cases.failures)} check failures). "
            "Verifying after reload in a fresh process:")
        done = subprocess.run([str(s2.PY), __file__, "verify", "--work", args.work,
                               "--tls-port", str(args.tls_port), "--http-port", str(args.http_port), "--db", args.db,
                               *(["--artifact", args.artifact] if args.artifact else [])])
        return 1 if cases.failures else done.returncode
    return PowerCases(args).verify()


if __name__ == "__main__":
    raise SystemExit(main())
