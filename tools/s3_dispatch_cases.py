"""S3-01 phase 1 producer: the replayable `s3-dispatch-cases-v1` public fixture.

Every public report travels the normal path - a registered KOBO-001 Lab run on
`mini-grid` v3 published through `registered-kobo-publication` v3, the durable
registered gateway, a sealed Batch V2 over direct TLS and central acceptance
into Postgres - except the one labelled contradiction FAULT FIXTURE (decision
default Q1 in `.agent/S3-01-questions-1.md`), which is a separate authenticated
Batch V2 under its own labelled epoch and never gateway output.

Isolated like `tools/s2_demo_walkthrough.py` (whose `Demo` it reuses): a
`git archive` of HEAD with its own `var/`, database `assetops_s3cases` on the
Compose Postgres, new ports (HTTP 8710, TLS 8743), its own gateway pipe, work
directory `%LOCALAPPDATA%/AssetOps/s3-dispatch-cases`. Every process it starts
is stopped before it exits. It never touches `assetops`, the workspace `var/`
or any server already running.

    .venv/Scripts/python.exe tools/s3_dispatch_cases.py run      # produce + write the manifest
    .venv/Scripts/python.exe tools/s3_dispatch_cases.py verify   # reload from Postgres, compare IDs

The manifest holds only public identities (Site/gateway/source IDs, Foundation
and binding versions, epochs, batch and evidence IDs, expected claim
ceilings). Lab run IDs and the Lab's private world (trajectories, decisions)
are named only under `private_oracle`, by location, and are never public
evidence. Precondition checks read accepted public values only; they are not
the dispatch analytic.
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
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s2_demo_walkthrough as s2  # noqa: E402

s2.DEMO_DB = "assetops_s3cases"  # read by Demo at call time; the S2 database is never touched
DEFAULT_WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "s3-dispatch-cases"
MANIFEST_NAME = "s3-dispatch-cases-v1.json"
DEMO_CONFIG = "backend/conversions/kobo-001-s3-dispatch-demo-config.json"
EPOCH_1, EPOCH_2 = "s3-cases-epoch-1", "s3-cases-epoch-2"
OOO_EPOCH = "s3-out-of-order-fixture-epoch"  # phase 2: labelled fault fixture (Architect Q5/F3)
ASSESS = ("-m", "assetops_backend.analytics.assess_dispatch")
FIXTURE_EPOCH = "s3-contradiction-fixture-epoch"
MODEL = {"profile_id": "mini-grid", "profile_version": 3}
PUBLICATION = {"profile_id": "registered-kobo-publication", "profile_version": 3}
SCENARIOS = {
    "prolonged": ("kobo-mini-grid-prolonged", 2),
    "stop-60": ("kobo-mini-grid-stop-60", 2),
    "degraded": ("kobo-s3-dispatch-degraded-reporting", 1),
    "necessary-run": ("kobo-s3-dispatch-necessary-run", 1),  # phase 3 (review F5)
}
CAPABILITY_ROLES = ("pv_available_power", "pcs_discharge_capability")
HEADROOM = Decimal("1.1")
say, step = s2.say, s2.step


def window(day: str) -> tuple[str, str]:
    return f"2026-10-{day}T03:00:00Z", f"2026-10-{day}T11:00:00Z"


def plus(instant: str, minutes: int) -> str:
    moved = datetime.fromisoformat(instant.replace("Z", "+00:00")) + timedelta(minutes=minutes)
    return moved.strftime("%Y-%m-%dT%H:%M:%SZ")


def id_digest(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


class Cases(s2.Demo):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        self.manifest_path = Path(args.manifest).resolve() if args.manifest else self.work / MANIFEST_NAME
        self.cases: list[dict[str, Any]] = []
        self.private_runs: dict[str, list[str]] = {}
        self.periods: list[dict[str, Any]] = []
        self.period_history: list[dict[str, Any]] = []

    def gateway_address(self) -> str:
        if sys.platform == "win32":
            return r"\\.\pipe\assetops-s3-cases-gateway"
        return str(self.gw / "gw.sock")

    def write_gateway_config(self, snap: dict[str, Any], credential: Path) -> None:
        super().write_gateway_config(snap, credential)
        path = self.gw / "gateway.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        config["provisioning"]["sequence_epoch"] = EPOCH_1
        path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # ------------------------------------------------------------ helpers
    def pg(self, sql: str, *params: Any) -> list[tuple]:
        import psycopg

        with psycopg.connect(self.db_url.replace("postgresql+psycopg://", "postgresql://")) as conn:
            return conn.execute(sql, params).fetchall()

    def demo_config(self, steps: str) -> dict[str, Any]:
        out = self.py("-m", "assetops_backend.sites.demo_configuration", "--fixture", DEMO_CONFIG,
                      "--tenant", "demo", "--steps", steps).stdout.strip().splitlines()
        say("  " + out[0][:200])
        result = json.loads(out[-1])
        for period in result["periods"]:
            say(f"  from {period['at']}: Foundation v{period['foundation_version']}, binding set "
                f"v{period['binding_version']} {period['role_set']}, snapshot {period['snapshot_sha256'][:16]}..")
        self.periods = result["periods"]
        self.period_history.append({"steps": steps, "periods": result["periods"]})
        return result

    def basis(self, start: str) -> dict[str, Any]:
        """The period whose instant is the latest at or before `start`."""
        return [p for p in self.periods if p["at"] <= start][-1]

    def run_case(self, label: str, day: str, scenario: str, seed: int = 20261001) -> list[str]:
        """One registered run executed, released and delivered; returns its new external batch IDs."""
        start, end = window(day)
        basis = self.basis(start)
        scenario_id, scenario_version = SCENARIOS[scenario]
        body = {
            "site_id": s2.SITE, "foundation_version": basis["foundation_version"], "scenario_id": scenario_id,
            "scenario_version": scenario_version, "interval": {"start_time": start, "end_time": end},
            "timestep_minutes": 5, "seed": seed, "model_profile": MODEL, "publication_profile": PUBLICATION,
            "run_inputs": [],
        }
        run = self.lab("POST", "/runs", body, expect=201)["run"]
        run_id = run["run_id"]
        if run.get("execution_status") != "READY":
            raise SystemExit(f"{label}: run {run_id} is {run.get('execution_status')}: "
                             f"{json.dumps(run.get('blocking_reasons'))[:600]}")
        self.private_runs.setdefault(label, []).append(run_id)
        before = set(self.sealed_inventory())
        self.lab("POST", f"/runs/{run_id}/execution/start")
        self.lab("POST", f"/runs/{run_id}/execution/run-to-end")
        self.lab("POST", f"/runs/{run_id}/publication/advance", {"instant": plus(end, 15)}, expect=None)
        released = self.lab("POST", f"/runs/{run_id}/commit", expect=None)
        self.deliver_all(label)
        added = sorted(set(self.sealed_inventory()) - before)
        say(f"  {label}: {scenario_id} v{scenario_version} {start}..{end} on Foundation "
            f"v{basis['foundation_version']} / {basis['role_set']} v{basis['binding_version']}; "
            f"commit {json.dumps(released)[:120]}; {len(added)} sealed batches delivered")
        return added

    def accepted(self, external_batch_ids: list[str]) -> list[dict[str, Any]]:
        rows = self.pg(
            "SELECT e.id::text, b.external_batch_id, e.sequence_epoch, e.sequence, e.role, e.device_id, "
            "e.signal_id, e.asset_id::text, e.source_time, e.published_at, e.interval_end, e.quality, "
            "e.normalized_value_text, e.binding_set_revision_id::text, e.foundation_revision_id::text, "
            "e.source_id::text, e.gateway_id::text, e.envelope_sha256 "
            "FROM accepted_evidence e JOIN ingestion_batch b ON b.id = e.batch_id "
            "WHERE b.external_batch_id = ANY(%s) ORDER BY e.source_time, e.sequence", list(external_batch_ids))
        keys = ("evidence_id", "batch_id", "epoch", "sequence", "role", "device_id", "signal_id", "asset_id",
                "source_time", "published_at", "interval_end", "quality", "value", "binding_set_revision_id",
                "foundation_revision_id", "source_id", "gateway_id", "envelope_sha256")
        return [dict(zip(keys, r)) for r in rows]

    def reserve(self, at: str) -> Decimal:
        """The selected Foundation revision's battery reserve control at `at` (public configuration)."""
        rows = self.pg("SELECT content FROM foundation_revision WHERE superseded_at IS NULL AND valid_from <= %s "
                       "AND (valid_to IS NULL OR valid_to > %s)", at, at)
        snap, status = [r[0] for r in rows], len(rows)
        found: list[Any] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("property_key") == "reserve-state-of-charge":
                    found.append(node.get("value"))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(snap)
        if status != 1 or len(set(map(str, found))) != 1:
            raise SystemExit(f"reserve not readable at {at}: {status} {found}")
        return Decimal(str(found[0]))

    @staticmethod
    def instants(rows: list[dict[str, Any]]) -> dict[datetime, dict[str, Any]]:
        """Accepted GOOD public values by 15-minute instant: states at their source time, interval
        readings at their interval end; feeder demand summed only when all three meters are present."""
        grid: dict[datetime, dict[str, Any]] = {}
        for row in rows:
            if row["quality"] != "GOOD" or row["value"] is None:
                continue
            at = row["interval_end"] or row["source_time"]
            slot = grid.setdefault(at, {"demand": {}})
            if row["role"] == "feeder_demand":
                slot["demand"][row["asset_id"]] = Decimal(row["value"])
            elif row["role"] == "generator_state":
                slot["generator_state"] = row["value"]
            else:
                slot[row["role"]] = Decimal(row["value"])
        for slot in grid.values():
            slot["load"] = sum(slot["demand"].values()) if len(slot["demand"]) == 3 else None
        return grid

    def classify_public(self, rows: list[dict[str, Any]], reserve: Decimal) -> dict[str, list[str]]:
        """Which dispatch-2 rows 3/4/5a/5b the accepted public values satisfy while the generator is RUNNING."""
        out: dict[str, list[str]] = {"row3_near_reserve": [], "row4_capability_shortfall": [],
                                     "row5a_pv_alone": [], "row5b_pv_plus_discharge": []}
        for at, s in sorted(self.instants(rows).items()):
            if s.get("generator_state") != "RUNNING" or s["load"] is None:
                continue
            load, soc = s["load"], s.get("battery_soc")
            pv, dis = s.get("pv_available_power"), s.get("pcs_discharge_capability")
            text = at.strftime("%Y-%m-%dT%H:%M:%SZ")
            if soc is not None and pv is not None and soc <= reserve + 10 and load > pv:
                out["row3_near_reserve"].append(text)
            if pv is not None and dis is not None and load > pv + dis:
                out["row4_capability_shortfall"].append(text)
            if pv is not None and dis is not None and pv >= load * HEADROOM:
                out["row5a_pv_alone"].append(text)
            if None not in (pv, dis, soc) and soc > reserve + 10 and pv + dis >= load * HEADROOM:
                out["row5b_pv_plus_discharge"].append(text)
        return out

    def record(self, case_id: str, label: str, day: str | None, batches: list[str], rows: list[dict[str, Any]],
               expected: str, precondition: dict[str, Any], epochs: list[str] | None = None,
               fault_fixture: bool = False) -> None:
        ids = [r["evidence_id"] for r in rows]
        first = rows[0] if rows else {}
        case = {
            "case_id": case_id, "label": label,
            "window": None if day is None else dict(zip(("start", "end"), window(day))),
            "fault_fixture": fault_fixture,
            "epochs": epochs or sorted({r["epoch"] for r in rows}),
            "batch_ids": sorted(batches),
            "evidence_ids": sorted(ids), "evidence_count": len(ids), "evidence_id_sha256": id_digest(ids),
            "roles": sorted({r["role"] for r in rows}),
            "quality": {q: sum(1 for r in rows if r["quality"] == q) for q in sorted({r["quality"] for r in rows})},
            "foundation_revision_ids": sorted({r["foundation_revision_id"] for r in rows}),
            "binding_set_revision_ids": sorted({r["binding_set_revision_id"] for r in rows}),
            "gateway_id": first.get("gateway_id"), "source_ids": sorted({r["source_id"] for r in rows}),
            "expected_claim_ceiling": expected,
            "precondition": precondition,
        }
        self.cases.append(case)
        say(f"  CASE {case_id}: {len(ids)} accepted readings, epochs {case['epochs']}, roles {len(case['roles'])}, "
            f"precondition met={precondition.get('met')}; expected ceiling: {expected}")

    # ------------------------------------------------------------ the flow
    def flow(self) -> None:
        step("2. Lab/product API, provisioned gateway (epoch s3-cases-epoch-1), TLS upload server")
        self.start_lab()
        snap = self.snapshot()
        self.gateway_external_id = snap["gateway"]["gateway_external_id"]
        sources = [s["source_external_id"] for s in snap["sources"]]
        self.credential = self.issue(sources)
        self.write_gateway_config(snap, self.credential)
        self.start_tls()
        self.start_gateway()
        self.identity = {"tenant_id": snap["tenant_id"], "site_id": snap["site"]["site_id"], "site_code": s2.SITE,
                         "gateway_id": snap["gateway"]["gateway_id"],
                         "gateway_external_id": self.gateway_external_id,
                         "sources": sorted((s["source_external_id"], s["source_id"]) for s in snap["sources"])}

        step("3. SIMULATED DEMO CONFIGURATION, step 1 only: generator values from 2026-10-01 (no capability channel yet)")
        self.demo_config("properties")

        step("4. Candidate blocked BEFORE: a roles-1 run (2026-10-01); capability channels are unbound")
        batches = self.run_case("before-roles-1", "01", "prolonged")
        rows = self.accepted(batches)
        reserve = self.reserve(window("01")[0])
        present = sorted({r["role"] for r in rows} & set(CAPABILITY_ROLES))
        rows_hit = self.classify_public(rows, reserve)
        running = sum(1 for s in self.instants(rows).values() if s.get("generator_state") == "RUNNING")
        self.record("candidate-blocked-before", "Generator runs on a minigrid-roles-1 basis", "01", batches, rows,
                    "Indeterminate: missing roles pv_available_power, pcs_discharge_capability (never Candidate)",
                    {"met": running > 0 and not present and not rows_hit["row5a_pv_alone"]
                     and not rows_hit["row5b_pv_plus_discharge"],
                     "capability_roles_accepted": present, "role_set": self.basis(window("01")[0])["role_set"],
                     "candidate_rows_satisfiable": rows_hit["row5a_pv_alone"] + rows_hit["row5b_pv_plus_discharge"],
                     "running_instants": running})

        step("5. SIMULATED DEMO CONFIGURATION, step 2: minigrid-roles-2 with both capability channels from 2026-10-02")
        self.demo_config("properties,bindings")

        step("6. Necessary and two-capability Candidate (2026-10-02, roles-2)")
        batches = self.run_case("main-roles-2", "02", "prolonged")
        rows = self.accepted(batches)
        reserve = self.reserve(window("02")[0])
        hit = self.classify_public(rows, reserve)
        necessary = hit["row3_near_reserve"] + hit["row4_capability_shortfall"]
        candidate = hit["row5b_pv_plus_discharge"] + hit["row5a_pv_alone"]
        say(f"  reserve {reserve} %; public rows satisfied while RUNNING: "
            + ", ".join(f"{k} {len(v)}" for k, v in hit.items()))
        self.record("physical-necessary", "Generator needed: near reserve and/or capability shortfall", "02", batches,
                    rows, "Necessary (BATTERY_NEAR_RESERVE / CAPABILITY_SHORTFALL) at the named instants",
                    {"met": bool(necessary), "reserve_soc": str(reserve), "row3_instants": hit["row3_near_reserve"],
                     "row4_instants": hit["row4_capability_shortfall"]})
        self.record("two-capability-candidate", "Generator running while PV available + PCS discharge capability "
                    "cover load x 1.1 and SOC > reserve + 10", "02", batches, rows,
                    "Candidate avoidable, bounded to the named segments (never the whole interval)",
                    {"met": bool(candidate), "row5b_instants": hit["row5b_pv_plus_discharge"],
                     "row5a_instants": hit["row5a_pv_alone"],
                     "capability_roles_accepted": sorted({r["role"] for r in rows} & set(CAPABILITY_ROLES))})

        step("7. Missing/poor-quality and late/out-of-order reporting (2026-10-03, degraded-reporting scenario)")
        batches = self.run_case("degraded-roles-2", "03", "degraded")
        rows = self.accepted(batches)
        cap = sorted(r["source_time"] for r in rows if r["role"] == "pcs_discharge_capability")
        pv = sorted(r["source_time"] for r in rows if r["role"] == "pv_available_power")
        gap = [t.strftime("%H:%M") for t in pv if t not in set(cap)]
        not_good = {q: n for q, n in {q: sum(1 for r in rows if r["quality"] == q)
                                      for q in {r["quality"] for r in rows}}.items() if q != "GOOD"}
        self.record("missing-poor-quality", "PCS discharge-capability reporting gap (one hour) plus any "
                    "UNAVAILABLE readings; no SUSPECT value is fabricated (Q2 default)", "03", batches, rows,
                    "Indeterminate across the gap: missing pcs_discharge_capability (never Candidate)",
                    {"met": len(gap) >= 4, "discharge_capability_missing_at": gap, "non_good_quality": not_good})
        soc = [r for r in rows if r["role"] == "battery_soc"]
        late = []
        for r in soc:
            lag = (r["published_at"] - r["source_time"]).total_seconds()
            # sequences are per (source, epoch): compare only within the SOC reading's own source
            overtaken = [o for o in rows if o["source_id"] == r["source_id"] and o["epoch"] == r["epoch"]
                         and o["source_time"] > r["source_time"] and o["sequence"] < r["sequence"]]
            if lag >= 600:
                late.append({"evidence_id": r["evidence_id"], "source_time": r["source_time"].isoformat(),
                             "published_at": r["published_at"].isoformat(), "sequence": r["sequence"],
                             "same_source_later_readings_sequenced_before_it": len(overtaken)})
        self.record("late-publication", "One battery SOC publication held ten minutes (late at source publication only; "
                    "not out-of-order, not centrally late - see late-central-acceptance). The ordinary "
                    "path keeps source order within a source, so no reading is sequenced after a later one "
                    "(Q5 ruling)", "03", batches, rows,
                    "Placed at its source time; delivered with its window, so it cannot by itself prove reassessment",
                    {"met": bool(late), "late_readings": late,
                     "out_of_order_within_source": any(x["same_source_later_readings_sequenced_before_it"]
                                                       for x in late)})

        step("8. Overlapping runs on ONE epoch (2026-10-04): ambiguous by construction (Q3 default)")
        first = self.run_case("overlap-a", "04", "prolonged")
        second = self.run_case("overlap-b", "04", "stop-60", seed=20261004)
        rows = self.accepted(first + second)
        by_key: dict[tuple, set] = {}
        for r in rows:
            by_key.setdefault((r["role"], r["asset_id"], r["source_time"]), set()).add(r["value"])
        clashes = sum(1 for values in by_key.values() if len(values) > 1)
        doubled = sum(1 for k in by_key if sum(1 for r in rows if (r["role"], r["asset_id"], r["source_time"]) == k) > 1)
        self.record("overlap-same-epoch", "Two registered runs over one window on one gateway epoch", "04",
                    first + second, rows,
                    "Limited/Indeterminate: ambiguous cohort named (one epoch, two reports per channel-time); "
                    "never summed, never separated by sequence range or receipt order",
                    {"met": len({r["epoch"] for r in rows}) == 1 and doubled > 0, "doubled_channel_times": doubled,
                     "differing_values": clashes})

        step("9. Overlap separable by epoch (2026-10-05): epoch-1 run, reprovision to epoch-2, second run")
        first = self.run_case("separable-epoch-1", "05", "prolonged")
        self.stop("gateway")
        out = self.py("-m", "assetops_gateway", "reprovision-epoch", "--config", str(self.gw / "gateway.json"),
                      "--epoch", EPOCH_2, cwd=self.gw)
        say(f"  gateway reprovisioned to {EPOCH_2} (exit {out.returncode})")
        self.start_gateway()
        second = self.run_case("separable-epoch-2", "05", "stop-60", seed=20261005)
        rows = self.accepted(first + second)
        epochs = {b: sorted({r["epoch"] for r in rows if r["batch_id"] == b}) for b in first + second}
        separable = all(e == [EPOCH_1] for b, e in epochs.items() if b in first) and all(
            e == [EPOCH_2] for b, e in epochs.items() if b in second)
        self.record("overlap-separable-epoch", "Two runs over one window on two gateway epochs", "05",
                    first + second, rows,
                    "Each epoch is its own cohort; an assessment selects one and names the other (no blending)",
                    {"met": separable, "epoch_by_batch": {EPOCH_1: len(first), EPOCH_2: len(second)}})

        step("9b. PHASE 3: generator needed for its whole run (2026-10-09, necessary-run scenario, ordinary)")
        batches = self.run_case("necessary-run", "09", "necessary-run", seed=20261009)
        rows = self.accepted(batches)
        reserve = self.reserve(window("09")[0])
        hit = self.classify_public(rows, reserve)
        running = sorted({at.strftime("%Y-%m-%dT%H:%M:%SZ") for at, s in self.instants(rows).items()
                          if s.get("generator_state") == "RUNNING"})
        necessary = set(hit["row3_near_reserve"]) | set(hit["row4_capability_shortfall"])
        say(f"  reserve {reserve} %; {len(running)} RUNNING instants, {len(necessary & set(running))} satisfy "
            f"row 3 or row 4; candidate rows {len(hit['row5a_pv_alone']) + len(hit['row5b_pv_plus_discharge'])}")
        self.record("necessary-interval", "Generator needed for its whole run: load above PV available + PCS "
                    "discharge capability at every RUNNING report (ordinary registered gateway evidence)", "09",
                    batches, rows, "Interval claim NECESSARY (all segments Necessary: CAPABILITY_SHORTFALL, "
                    "BATTERY_NEAR_RESERVE/AT_RESERVE while SOC <= reserve + 10)",
                    {"met": bool(running) and set(running) <= set(hit["row4_capability_shortfall"])
                     and not hit["row5a_pv_alone"] and not hit["row5b_pv_plus_discharge"],
                     "reserve_soc": str(reserve), "running_instants": len(running),
                     "row3_instants": hit["row3_near_reserve"], "row4_instants": hit["row4_capability_shortfall"]})

        step("10. FAULT FIXTURE (labelled, not gateway output): contradictory same-role readings (Q1 default)")
        self.contradiction()

        step("11. PHASE 2 FAULT FIXTURE (labelled): later source time accepted first, earlier second (2026-10-07)")
        self.out_of_order()

        step("12. PHASE 2: the dispatch assessment worker (current model) consumes the S2 recompute jobs; every case window assessed")
        self.assess_cases()

        step("13. PHASE 2: late CENTRAL acceptance (2026-10-08): cutoff A, held batches accepted, cutoff B")
        self.late_central()

    def contradiction(self) -> None:
        from assetops_contracts.ingestion_batch_v2 import seal_batch_v2
        from assetops_contracts.source_envelope import canonical_json
        from assetops_contracts.source_envelope_v3 import v3_message_id

        template, batch = self.soc_template()
        source_time = "2026-10-06T05:00:00Z"
        base = Decimal(template["payload"]["value"])
        envelope_texts = []
        for sequence, value in ((1, base), (2, base + Decimal("7.5"))):
            envelope = json.loads(json.dumps(template))
            src = envelope["source"]
            envelope["message"] = {"message_id": v3_message_id(
                site_id=src["site_id"], gateway_id=src["gateway_id"], source_id=src["source_id"],
                sequence_epoch=FIXTURE_EPOCH, sequence=sequence),
                "sequence_epoch": FIXTURE_EPOCH, "sequence": sequence}
            envelope["timing"]["source_time"] = source_time
            envelope["timing"]["published_at"] = plus(source_time, 1)
            envelope["payload"]["value"] = f"{value.normalize():f}"  # canonical decimal: no trailing zero
            envelope_texts.append(canonical_json(envelope))
        batch_id, body = seal_batch_v2(
            site_id=batch["site_id"], gateway_id=batch["gateway_id"], source_id=batch["source_id"],
            source_mode=batch["source_mode"], foundation_version=batch["configuration"]["foundation_version"],
            foundation_valid_from=batch["configuration"]["foundation_valid_from"],
            binding_set_id=batch["mapping"]["binding_set_id"], binding_version=batch["mapping"]["version"],
            snapshot_sha256=batch["mapping"]["snapshot_sha256"], envelope_texts=envelope_texts)
        external = json.loads(body)["batch_id"]
        status, receipt = self.call("POST", "/api/ingestion/batches", raw=body.encode("utf-8"), base=self.https,
                                    headers=self.bearer(self.credential))
        say(f"  fault-fixture batch {external}: {status} counts={(receipt or {}).get('counts')}")
        rows = self.accepted([external])
        values = sorted({r["value"] for r in rows})
        self.record("contradiction-fault-fixture", "LABELLED FAULT FIXTURE: two different battery SOC values at one "
                    "source time in one cohort (authenticated Batch V2, not gateway-sealed)", None, [external], rows,
                    "Indeterminate: contradictory same-role samples (equal rank); never blended into source truth",
                    {"met": status == 200 and len(rows) == 2 and len(values) == 2, "source_time": source_time,
                     "values": values}, fault_fixture=True)

    # ------------------------------------------------------------ phase 2
    def soc_template(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """The fault fixtures' template: the two-capability-candidate case's state-of-charge envelope with a
        value at the minimum (source_time, sequence) across all its batches - never batch walk order, since
        batch IDs digest the per-run gateway ID and snapshot, so their sort order changes run to run."""
        main = next(c for c in self.cases if c["case_id"] == "two-capability-candidate")
        texts = dict(self.gw_db("SELECT batch_id, payload_text FROM upload_batch"))
        found = []
        for batch_id in main["batch_ids"]:
            parsed = json.loads(texts[batch_id])
            for envelope_text in parsed["envelopes"]:
                envelope = json.loads(envelope_text)
                if envelope["source"]["signal_id"] == "state-of-charge" and envelope["payload"].get("value"):
                    found.append(((envelope["timing"]["source_time"], envelope["message"]["sequence"]),
                                  envelope, parsed))
        if not found:
            raise SystemExit("no accepted state-of-charge envelope to copy for the fault fixture")
        key, envelope, parsed = min(found, key=lambda f: f[0])
        say(f"  template SOC envelope: source_time {key[0]}, sequence {key[1]}, value {envelope['payload']['value']}")
        return envelope, parsed

    def post_fixture(self, template: dict[str, Any], batch: dict[str, Any], epoch: str,
                     items: list[tuple[int, str, str]]) -> tuple[str, int]:
        """One labelled FAULT FIXTURE Batch V2 (authenticated, NOT gateway-sealed)."""
        from assetops_contracts.ingestion_batch_v2 import seal_batch_v2
        from assetops_contracts.source_envelope import canonical_json
        from assetops_contracts.source_envelope_v3 import v3_message_id

        texts = []
        for sequence, source_time, value in items:
            envelope = json.loads(json.dumps(template))
            src = envelope["source"]
            envelope["message"] = {"message_id": v3_message_id(
                site_id=src["site_id"], gateway_id=src["gateway_id"], source_id=src["source_id"],
                sequence_epoch=epoch, sequence=sequence), "sequence_epoch": epoch, "sequence": sequence}
            envelope["timing"]["source_time"] = source_time
            envelope["timing"]["published_at"] = plus(source_time, 1)
            envelope["payload"]["value"] = value
            texts.append(canonical_json(envelope))
        _, body = seal_batch_v2(
            site_id=batch["site_id"], gateway_id=batch["gateway_id"], source_id=batch["source_id"],
            source_mode=batch["source_mode"], foundation_version=batch["configuration"]["foundation_version"],
            foundation_valid_from=batch["configuration"]["foundation_valid_from"],
            binding_set_id=batch["mapping"]["binding_set_id"], binding_version=batch["mapping"]["version"],
            snapshot_sha256=batch["mapping"]["snapshot_sha256"], envelope_texts=texts)
        status, _ = self.call("POST", "/api/ingestion/batches", raw=body.encode("utf-8"), base=self.https,
                              headers=self.bearer(self.credential))
        return json.loads(body)["batch_id"], status

    def decided(self, evidence_ids: list[str]) -> dict[str, str]:
        rows = self.pg("SELECT e.id::text, d.decided_at FROM accepted_evidence e JOIN ingestion_disposition d "
                       "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal WHERE e.id::text = ANY(%s)",
                       list(evidence_ids))
        return {i: t.isoformat() for i, t in rows}

    def out_of_order(self) -> None:
        template, batch = self.soc_template()
        base = Decimal(template["payload"]["value"])
        later, status_1 = self.post_fixture(template, batch, OOO_EPOCH, [(1, "2026-10-07T05:15:00Z", f"{base:f}")])
        earlier, status_2 = self.post_fixture(template, batch, OOO_EPOCH,
                                              [(2, "2026-10-07T05:00:00Z", f"{base + 1:f}")])
        rows = self.accepted([later, earlier])
        at = self.decided([r["evidence_id"] for r in rows])
        ordered = sorted(rows, key=lambda r: at[r["evidence_id"]])
        inverted = (len(rows) == 2 and ordered[0]["source_time"] > ordered[1]["source_time"]
                    and ordered[0]["sequence"] < ordered[1]["sequence"])
        say(f"  out-of-order fixture batches {later} ({status_1}) then {earlier} ({status_2}); inverted={inverted}")
        self.record("out-of-order-fault-fixture", "LABELLED FAULT FIXTURE: a battery SOC at 05:15 centrally accepted "
                    "BEFORE the same source's SOC at 05:00 (authenticated Batch V2, not gateway-sealed)", "07",
                    [later, earlier], rows,
                    "Limited: SEQUENCE_ORDER_INVERTED over 05:00-05:15 names both IDs; never re-sorted by receipt",
                    {"met": status_1 == 200 and status_2 == 200 and inverted,
                     "acceptance_order": [{"evidence_id": r["evidence_id"], "batch_id": r["batch_id"],
                                           "sequence": r["sequence"], "source_time": r["source_time"].isoformat(),
                                           "decided_at": at[r["evidence_id"]]} for r in ordered]},
                    fault_fixture=True)

    def worker(self, *argv: str) -> Any:
        return json.loads(self.py(*ASSESS, *argv).stdout.strip().splitlines()[-1])

    def window_read(self, start: str, explicit: bool = False) -> dict[str, Any]:
        """The latest run of a window and its selected revisions (direct read; phase 3 builds the API)."""
        selection = "EXPLICIT" if explicit else "DEFAULT"
        rows = self.pg(
            "SELECT r.id::text, r.cohort_status, r.input_sha256, r.knowledge_cutoff, r.job_id::text, "
            "a.assessment_key, a.revision_no, a.id::text, a.claim_level, a.result FROM analytic_run r "
            "JOIN analytic_run_assessment l ON l.run_id = r.id JOIN assessment_revision a ON a.id = "
            "l.assessment_revision_id WHERE r.id = (SELECT id FROM analytic_run WHERE window_start = %s "
            "AND selection = %s ORDER BY completed_at DESC, id LIMIT 1) ORDER BY a.assessment_key",
            start, selection)
        if not rows:
            return {"run_id": None}
        window_row = next(r for r in rows if ":window:" in r[5])
        intervals = [r for r in rows if ":interval:" in r[5]]
        segments = [s for r in intervals for s in r[9]["segments"]]
        return {"run_id": rows[0][0], "cohort_status": rows[0][1], "input_sha256": rows[0][2],
                "knowledge_cutoff": rows[0][3].isoformat(), "job_id": rows[0][4],
                "window": {"revision_id": window_row[7], "revision_no": window_row[6], "claim_level": window_row[8],
                           "limitations": window_row[9]["limitations"]},
                "intervals": [{"key": r[5], "revision_id": r[7], "revision_no": r[6], "claim_level": r[8],
                               "candidate_minutes": r[9]["portions_minutes"]["candidate"]} for r in intervals],
                "segment_classes": sorted({s["classification"] for s in segments}),
                "indeterminate_segments": [(s["start"], s["end"]) for s in segments
                                           if s["classification"] == "INDETERMINATE"]}

    def assess_cases(self) -> None:
        outcomes = self.worker("process-jobs")
        say(f"  worker: {len(outcomes)} job(s): " + ", ".join(sorted({o['status'] for o in outcomes})))
        for case in self.cases:
            start = (case["window"] or {"start": window("06")[0]})["start"]
            read = self.window_read(start[:10] + "T00:00:00+00:00")
            case["assessment"] = read
            case["assessment_check"] = self.check(case["case_id"], read)
            say(f"  {case['case_id']}: window {read.get('window', {}).get('claim_level')}, intervals "
                f"{[i['claim_level'] for i in read.get('intervals', [])]}, check={case['assessment_check']}")
        sep = next(c for c in self.cases if c["case_id"] == "overlap-separable-epoch")
        gateway = self.identity["gateway_id"]
        sep["explicit_choices"] = {}
        for epoch in (EPOCH_1, EPOCH_2):
            sources = [r[0] for r in self.pg(
                "SELECT DISTINCT source_id::text FROM accepted_evidence WHERE sequence_epoch = %s "
                "AND source_time >= %s AND source_time < %s ORDER BY 1", epoch, *window("05"))]
            chosen = [f"{gateway}:{s}:{epoch}" for s in sources]
            out = self.worker("assess", "--tenant-id", self.identity["tenant_id"], "--site-id",
                              self.identity["site_id"], "--start", window("05")[0], "--end", window("05")[1],
                              "--cohort", *chosen)
            claims = sorted(c[0] for c in self.pg(
                "SELECT a.claim_level FROM analytic_run_assessment l JOIN assessment_revision a ON "
                "a.id = l.assessment_revision_id WHERE l.run_id::text = %s AND l.scope = 'INTERVAL'", out["run_id"]))
            status = self.pg("SELECT cohort_status FROM analytic_run WHERE id::text = %s", out["run_id"])[0][0]
            sep["explicit_choices"][epoch] = {"run_id": out["run_id"], "cohort": chosen, "cohort_status": status,
                                              "interval_claims": claims}
            say(f"  explicit cohort {epoch}: run {out['run_id']} {status}, intervals {claims}")

    @staticmethod
    def check(case_id: str, read: dict[str, Any]) -> dict[str, Any]:
        """Phase-2 expectations on the persisted dispatch-3.x result (claim ceilings, not mock values)."""
        claims = [i["claim_level"] for i in read.get("intervals", [])]
        limits = " ".join(read.get("window", {}).get("limitations", []))
        segs = read.get("segment_classes", [])
        expect = {
            "candidate-blocked-before": bool(claims) and "CANDIDATE_AVOIDABLE" not in claims
                                        and "MISSING_ROLE" in limits,
            "physical-necessary": "NECESSARY" in segs,
            # review F5: the INTERVAL claim, not merely a Necessary segment
            "necessary-interval": "NECESSARY" in claims and not set(claims) - {"NECESSARY"},
            "two-capability-candidate": "CANDIDATE_AVOIDABLE" in claims,
            "missing-poor-quality": any(s <= "2026-10-03T06:45" and e >= "2026-10-03T06:00"
                                        for s, e in read.get("indeterminate_segments", [])),
            "late-publication": read.get("run_id") is not None,
            "overlap-same-epoch": (read.get("window", {}).get("claim_level") == "INDETERMINATE"
                                   and not set(claims) - {"INDETERMINATE"}
                                   and "SEQUENCE_ORDER_INVERTED" in limits),
            "overlap-separable-epoch": read.get("cohort_status") == "AMBIGUOUS" and not claims,
            "contradiction-fault-fixture": "REPORTS_OVERLAP" in limits and not claims,
            "out-of-order-fault-fixture": "SEQUENCE_ORDER_INVERTED" in limits,
        }
        return {"met": bool(expect.get(case_id, True))}

    def late_central(self) -> None:
        start, end = window("08")
        basis = self.basis(start)
        scenario_id, scenario_version = SCENARIOS["prolonged"]
        body = {"site_id": s2.SITE, "foundation_version": basis["foundation_version"], "scenario_id": scenario_id,
                "scenario_version": scenario_version, "interval": {"start_time": start, "end_time": end},
                "timestep_minutes": 5, "seed": 20261008, "model_profile": MODEL, "publication_profile": PUBLICATION,
                "run_inputs": []}
        run = self.lab("POST", "/runs", body, expect=201)["run"]
        if run.get("execution_status") != "READY":
            raise SystemExit(f"late-central: run is {run.get('execution_status')}")
        self.private_runs.setdefault("late-central", []).append(run["run_id"])
        before = set(self.sealed_inventory())
        self.lab("POST", f"/runs/{run['run_id']}/execution/start")
        self.lab("POST", f"/runs/{run['run_id']}/execution/run-to-end")
        self.lab("POST", f"/runs/{run['run_id']}/publication/advance", {"instant": plus(end, 15)}, expect=None)
        self.lab("POST", f"/runs/{run['run_id']}/commit", expect=None)
        sealed = sorted(set(self.sealed_inventory()) - before)
        held = 2
        first = self.deliver(len(sealed) - held)["batches"]
        delivered_a = sorted(r[0] for r in self.pg(
            "SELECT external_batch_id FROM ingestion_batch WHERE external_batch_id = ANY(%s)", sealed))
        say(f"  delivered {first['acked']} of {len(sealed)} sealed batches; {len(sealed) - len(delivered_a)} held")
        rows_a = self.accepted(delivered_a)
        self.worker("process-jobs")
        read_a = self.window_read(start[:10] + "T00:00:00+00:00")
        say(f"  cutoff A {read_a['knowledge_cutoff']}: run {read_a['run_id']}, window rev "
            f"{read_a['window']['revision_no']}, intervals {[i['claim_level'] for i in read_a['intervals']]}")
        self.deliver_all("late-central-held")
        late_batches = sorted(set(sealed) - set(delivered_a))
        late_rows = self.accepted(late_batches)
        jobs = self.pg("SELECT id::text, created_at, window_start, window_end FROM recompute_job "
                       "WHERE status = 'PENDING' ORDER BY created_at")
        self.worker("process-jobs")
        read_b = self.window_read(start[:10] + "T00:00:00+00:00")
        say(f"  cutoff B {read_b['knowledge_cutoff']}: run {read_b['run_id']}, window rev "
            f"{read_b['window']['revision_no']}, intervals {[i['claim_level'] for i in read_b['intervals']]}")
        late_ids = sorted(r["evidence_id"] for r in late_rows)
        late_at = self.decided(late_ids)
        old_kept = self.pg("SELECT count(*) FROM assessment_revision WHERE id::text = %s",
                           read_a["window"]["revision_id"])[0][0] == 1
        met = (bool(late_rows) and bool(jobs) and read_a["run_id"] != read_b["run_id"] and old_kept
               and read_b["window"]["revision_no"] > read_a["window"]["revision_no"]
               and min(late_at.values()) > read_a["knowledge_cutoff"])
        self.record("late-central-acceptance", "Ordinary registered run whose last sealed batches are HELD at the "
                    "gateway until after a first central assessment (gateway order kept; Architect F3)", "08",
                    sealed, rows_a + late_rows,
                    "A new recompute job and new revision(s) at cutoff B; the cutoff-A revision stays addressable",
                    {"met": met, "cutoff_a": read_a["knowledge_cutoff"], "cutoff_b": read_b["knowledge_cutoff"],
                     "held_batch_ids": late_batches, "late_evidence_ids": late_ids,
                     "late_decided_at": sorted(set(late_at.values())),
                     "pending_jobs_after_late": [{"job_id": j[0], "created_at": j[1].isoformat(),
                                                  "window": [j[2].isoformat(), j[3].isoformat()]} for j in jobs],
                     "run_a": read_a, "run_b": read_b})

    def verify_phase2(self, manifest: dict[str, Any]) -> list[str]:
        """Reload the persisted runs and revisions named in the manifest; the old late-case revision must
        still exist unchanged and the cutoff-A run must still select it."""
        failures = []
        for case in manifest["cases"]:
            a = case.get("assessment") or {}
            if not case.get("assessment_check", {"met": True})["met"]:
                failures.append(case["case_id"] + " (assessment)")
            if a.get("run_id"):
                found = self.pg("SELECT input_sha256 FROM analytic_run WHERE id::text = %s", a["run_id"])
                if not found or found[0][0] != a["input_sha256"]:
                    failures.append(case["case_id"] + " (run reload)")
        late = next((c for c in manifest["cases"] if c["case_id"] == "late-central-acceptance"), None)
        if late:
            run_a = late["precondition"]["run_a"]
            linked = {r[0] for r in self.pg("SELECT assessment_revision_id::text FROM analytic_run_assessment "
                                            "WHERE run_id::text = %s", run_a["run_id"])}
            if run_a["window"]["revision_id"] not in linked:
                failures.append("late-central-acceptance (old revision not addressable)")
            say(f"  verify late-central-acceptance: cutoff A run {run_a['run_id']} still selects window revision "
                f"{run_a['window']['revision_no']} = {run_a['window']['revision_id'] in linked}")
        return failures

    # ------------------------------------------------------------ manifest
    def write_manifest(self) -> dict[str, Any]:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=s2.REPO, capture_output=True,
                                text=True).stdout.strip()
        config_bytes = (s2.REPO / DEMO_CONFIG).read_bytes()
        manifest = {
            "schema": {"id": "s3-dispatch-cases", "version": 1},
            "label": "s3-dispatch-cases-v1",
            "status": "SIMULATED public fixture (S3-01 phases 1-3, I-sim-dispatch-cases; phase 2 adds the persisted dispatch-3 result per case; phase 3 adds the ordinary necessary-interval case). Not field evidence. Fault-fixture labels are manifest annotations, not central attestation.",
            "replayability": "Evidence, batch, run and revision IDs are per run: each run recreates the database, "
                              "registers a new gateway and new Foundation/binding revisions, and batch IDs digest "
                              "those. The fixture is replayable by procedure + seeds + verify (same cases, counts, "
                              "values and claim checks), not byte-for-byte. Fault-fixture templates are chosen by "
                              "minimum (source_time, sequence), so their values are stable across runs.",
            "produced_from_commit": commit,
            "database": s2.DEMO_DB,
            "site": self.identity,
            "publication": {"model_profile": MODEL, "publication_profile": PUBLICATION,
                            "gateway_epochs": [EPOCH_1, EPOCH_2], "fault_fixture_epoch": FIXTURE_EPOCH,
                            "out_of_order_fixture_epoch": OOO_EPOCH},
            "demo_configuration": {"fixture": DEMO_CONFIG,
                                   "fixture_sha256": hashlib.sha256(config_bytes).hexdigest(),
                                   "periods": self.periods,
                                   # the roles-1 case froze the first step's basis; the second step
                                   # split and re-aligned that period (bitemporal, never rewritten)
                                   "as_published": self.period_history},
            "cases": self.cases,
            "all_evidence_id_sha256": id_digest([i for c in self.cases for i in c["evidence_ids"]]),
            "private_oracle": {
                "statement": "Lab-private world state and run identities. Not public evidence; never an input to "
                             "the dispatch analytic; kept apart from the public identities above.",
                "lab_store": str(self.tree / "var"),
                "lab_runs_by_case": self.private_runs,
            },
        }
        self.manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        say(f"  manifest: {self.manifest_path} ({len(self.cases)} cases, "
            f"{sum(c['evidence_count'] for c in self.cases)} accepted readings)")
        return manifest

    def verify(self) -> int:
        """Reload every case's accepted IDs from Postgres and compare them with the manifest."""
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        failures = []
        for case in manifest["cases"]:
            ids = [r["evidence_id"] for r in self.accepted(case["batch_ids"])]
            same = sorted(ids) == case["evidence_ids"] and id_digest(ids) == case["evidence_id_sha256"]
            say(f"  verify {case['case_id']}: {len(ids)} reloaded, match={same}, "
                f"precondition met={case['precondition'].get('met')}")
            if not same:
                failures.append(case["case_id"])
            if not case["precondition"].get("met"):
                failures.append(case["case_id"] + " (precondition)")
        all_ids = [i for c in manifest["cases"] for i in c["evidence_ids"]]
        say(f"  all evidence digest match={id_digest(all_ids) == manifest['all_evidence_id_sha256']}")
        failures += self.verify_phase2(manifest)
        say("VERIFY " + ("PASSED" if not failures else f"FAILED: {failures}"))
        return 0 if not failures else 1

    def run(self) -> None:
        self.setup()
        try:
            self.flow()
            step("14. Manifest")
            self.write_manifest()
        finally:
            step("Stopping every process this script started")
            self.stop_all()
            say("  stopped: tls-server, lab-api, gateway")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s3_dispatch_cases.py")
    parser.add_argument("command", choices=("run", "verify"))
    parser.add_argument("--work", default=str(DEFAULT_WORK))
    parser.add_argument("--manifest", default=None, help="default: <work>/s3-dispatch-cases-v1.json")
    parser.add_argument("--tls-port", type=int, default=8743)
    parser.add_argument("--http-port", type=int, default=8710)
    parser.add_argument("--cadence-seconds", type=int, default=60)
    args = parser.parse_args(argv)
    cases = Cases(args)
    if args.command == "run":
        started = time.time()
        cases.run()
        say(f"Produced in {time.time() - started:.0f} s. Verifying after reload:")
        return Cases(args).verify()
    return cases.verify()


if __name__ == "__main__":
    raise SystemExit(main())
