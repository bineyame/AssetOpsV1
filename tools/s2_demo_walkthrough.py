"""S2-02 owner walkthrough: registered gateway -> direct TLS -> Postgres, end to end.

Repeatable and isolated. It never touches the developer database (`assetops`),
the workspace `var/` tree or any server already running. Everything it makes
lives under one work directory (default `%LOCALAPPDATA%/AssetOps/s2-demo`):

    tree/          a `git archive` of HEAD; its own `var/` (the backend resolves
                   every store from its module location, so a copied tree is the
                   only way to keep Lab runs, Stages and comparison reports apart)
    tls/           a NEWLY generated self-signed certificate/key (openssl); the
                   checked-in test fixture under gateway/tests is never used
    gateway/       the gateway's SQLite ledger, local IPC credential and config
    credentials/   the protected (owner-only DACL) upload credential files
    logs/          one log per started process

Database: `assetops_s2demo` on the Compose Postgres (127.0.0.1:55432), dropped
and recreated by `run`. Ports (override with flags): TLS upload server 8643,
Lab/product HTTP API 8610. Commands, from the repository root:

    .venv/Scripts/python.exe tools/s2_demo_walkthrough.py run      # full demo, then stop everything
    .venv/Scripts/python.exe tools/s2_demo_walkthrough.py serve    # reopen the result for the browser

`serve` starts the TLS server, the gateway and the Lab/product API over the
existing work directory and prints the frontend command; Ctrl+C stops them.
Every process this script starts is stopped before it exits.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import ssl
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PY = REPO / ".venv" / "Scripts" / "python.exe"
if not PY.exists():  # POSIX venv layout
    PY = REPO / ".venv" / "bin" / "python"
DEFAULT_WORK = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AssetOps" / "s2-demo"
PG_ADMIN = "postgresql://assetops:{pw}@127.0.0.1:{port}/assetops"
DEMO_DB = "assetops_s2demo"
SITE = "KOBO-001"
START, END = "2026-09-30T03:00:00Z", "2026-09-30T15:00:00Z"


def say(text: str = "") -> None:
    print(text, flush=True)


def step(title: str) -> None:
    say()
    say(f"=== {title} ===")


class Demo:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.work: Path = Path(args.work).resolve()
        self.tree = self.work / "tree"
        self.tls = self.work / "tls"
        self.gw = self.work / "gateway"
        self.creds = self.work / "credentials"
        self.logs = self.work / "logs"
        pw = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
        port = os.environ.get("ASSETOPS_PG_PORT", "55432")
        self.admin_url = PG_ADMIN.format(pw=pw, port=port)
        self.db_url = f"postgresql+psycopg://assetops:{pw}@127.0.0.1:{port}/{DEMO_DB}"
        self.http = f"http://127.0.0.1:{args.http_port}"
        self.https = f"https://127.0.0.1:{args.tls_port}"
        self.procs: dict[str, subprocess.Popen] = {}
        self.result: dict[str, Any] = {"database": DEMO_DB, "http": self.http, "https": self.https}
        self.link = None

    # ------------------------------------------------------------------ env
    def env(self, **extra: str) -> dict[str, str]:
        env = dict(os.environ)
        roots = [self.tree / p for p in ("backend", "gateway", "simulator", "contracts", "host")]
        env["PYTHONPATH"] = os.pathsep.join(str(r) for r in roots)
        env["DATABASE_URL"] = self.db_url
        env["PYTHONUNBUFFERED"] = "1"
        env.pop("ASSETOPS_TEST_DATABASE_URL", None)
        env.update(extra)
        return env

    def py(self, *argv: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
        done = subprocess.run([str(PY), *argv], cwd=str(cwd or self.tree), env=self.env(),
                              capture_output=True, text=True, timeout=600)
        if check and done.returncode != 0:
            raise SystemExit(f"FAILED: python {' '.join(argv)}\n{done.stdout}\n{done.stderr}")
        return done

    # ---------------------------------------------------------------- setup
    def setup(self) -> None:
        step("1. Isolated work directory, database and TLS material")
        self.work.mkdir(parents=True, exist_ok=True)
        if self.tree.exists():
            shutil.rmtree(self.tree)
        for d in (self.gw, self.creds, self.tls, self.logs):
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True)
        archive = subprocess.run(["git", "archive", "--format=tar", "HEAD", "backend", "gateway", "host",
                                  "simulator", "contracts", "config", "contract-fixtures"],
                                 cwd=REPO, capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(self.tree, filter="data")
        (self.tree / "var" / "sites").mkdir(parents=True)
        shutil.copy2(REPO / "var" / "sites" / "kobo-001.yaml", self.tree / "var" / "sites" / "kobo-001.yaml")
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                                text=True).stdout.strip()
        say(f"Work directory: {self.work} (code from git HEAD {commit}; own var/)")
        probe = self.py("-c", "import assetops_backend,assetops_gateway;print(assetops_backend.__file__);"
                        "print(assetops_gateway.__file__)").stdout.split()
        if not all(str(self.tree).lower() in p.lower() for p in probe):
            raise SystemExit(f"Isolation failed: packages resolve outside the copied tree: {probe}")

        import psycopg

        with psycopg.connect(self.admin_url, autocommit=True) as conn:
            conn.execute(f"DROP DATABASE IF EXISTS {DEMO_DB} WITH (FORCE)")
            conn.execute(f"CREATE DATABASE {DEMO_DB}")
        say(f"Database: {DEMO_DB} (dropped and recreated; the developer database is not touched)")
        self.py("-m", "alembic", "upgrade", "head", cwd=self.tree / "backend")
        out = self.py("-m", "assetops_backend.sites.import_kobo", "--source", "var/sites/kobo-001.yaml",
                      "--tenant", "demo").stdout
        say("Imported KOBO-001: " + out.strip().splitlines()[-1][:160])
        out = self.py("-m", "assetops_backend.sites.convert_kobo_bindings", "--fixture",
                      "backend/conversions/kobo-001-bindings.json", "--tenant", "demo").stdout
        say("Published bindings: " + out.strip().splitlines()[-1][:160])

        key, cert = self.tls / "server.key", self.tls / "server.crt"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "30",
                        "-keyout", str(key), "-out", str(cert), "-subj", "/CN=127.0.0.1",
                        "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost"],
                       check=True, capture_output=True)
        self.protect(key)
        fp = subprocess.run(["openssl", "x509", "-in", str(cert), "-noout", "-fingerprint", "-sha256"],
                            capture_output=True, text=True).stdout.strip()
        say(f"New TLS certificate {cert} ({fp}); key restricted to the current user")

    def protect(self, path: Path) -> None:
        self.py("-c", "import sys;from pathlib import Path;"
                "from assetops_gateway.credential_protection import restrict_to_current_user as r;"
                "r(Path(sys.argv[1]))", str(path))


    # ------------------------------------------------------------ processes
    def start(self, name: str, argv: list[str], cwd: Path, ready: str, env: dict[str, str] | None = None,
              timeout: float = 90) -> None:
        log = (self.logs / f"{name}.log").open("a", encoding="utf-8")
        log.write(f"\n--- start {time.strftime('%H:%M:%S')} {' '.join(argv)}\n")
        log.flush()
        proc = subprocess.Popen([str(PY), *argv], cwd=str(cwd), env=env or self.env(), stdout=log,
                                stderr=subprocess.STDOUT)
        self.procs[name] = proc
        deadline = time.time() + timeout
        while time.time() < deadline:
            if proc.poll() is not None:
                raise SystemExit(f"{name} exited early; see {self.logs / (name + '.log')}")
            if ready in (self.logs / f"{name}.log").read_text(encoding="utf-8", errors="replace").split(
                    "--- start")[-1]:
                return
            time.sleep(0.3)
        raise SystemExit(f"{name} did not become ready in {timeout}s; see {self.logs / (name + '.log')}")

    def stop(self, name: str) -> None:
        proc = self.procs.pop(name, None)
        if proc is None:
            return
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=20)
        if name == "gateway":
            self.link = None

    def stop_all(self) -> None:
        for name in list(self.procs):
            self.stop(name)

    def start_tls(self) -> None:
        self.start("tls-server", ["-m", "assetops_backend.serve_tls", "--cert", str(self.tls / "server.crt"),
                                  "--key", str(self.tls / "server.key"), "--port", str(self.args.tls_port)],
                   self.tree, "Application startup complete")

    def start_lab(self) -> None:
        env = self.env(ASSETOPS_GATEWAY_ADDRESS=self.gateway_address(),
                       ASSETOPS_GATEWAY_CREDENTIAL=str(self.gw / "gateway.credential"))
        self.start("lab-api", ["-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                               str(self.args.http_port)], self.tree / "host", "Application startup complete",
                   env=env)

    def gateway_address(self) -> str:
        if sys.platform == "win32":
            return r"\\.\pipe\assetops-s2-demo-gateway"
        return str(self.gw / "gw.sock")

    def start_gateway(self) -> None:
        self.start("gateway", ["-m", "assetops_gateway", "serve", "--config", str(self.gw / "gateway.json")],
                   self.gw, "READY")
        from assetops_gateway.ipc import GatewayLink  # the copied tree's code is identical to HEAD's

        self.link = GatewayLink(self.gateway_address(), self.gw / "gateway.credential")

    # ----------------------------------------------------------------- http
    def call(self, method: str, path: str, body: Any = None, *, base: str | None = None,
             headers: dict[str, str] | None = None, raw: bytes | None = None) -> tuple[int, Any]:
        url = (base or self.http) + path
        data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
        request = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            request.add_header(k, v)
        context = ssl.create_default_context(cafile=str(self.tls / "server.crt")) if url.startswith(
            "https") else None
        try:
            with urllib.request.urlopen(request, timeout=120, context=context) as response:
                text = response.read().decode()
                status = response.status
        except urllib.error.HTTPError as error:
            text, status = error.read().decode(), error.code
        try:
            return status, json.loads(text) if text else None
        except ValueError:
            return status, text

    # ------------------------------------------------------------ the demo
    def snapshot(self) -> dict[str, Any]:
        status, snap = self.call("GET", f"/api/sites/{SITE}/foundation/snapshot?at={START}")
        assert status == 200, snap
        return snap

    def issue(self, sources: list[str]) -> Path:
        argv = ["-m", "assetops_backend.evidence.provision_gateway", "issue", "--tenant", "demo", "--site", SITE,
                "--gateway", self.gateway_external_id, "--credential-out", str(self.creds / "upload.credential"),
                "--cadence-seconds", str(self.args.cadence_seconds)]
        for source in sources:
            argv += ["--enable-source", source]
        out = self.py(*argv).stdout
        say("  " + out.strip().splitlines()[0][:200])
        path = Path(next(l for l in out.splitlines() if l.startswith("Credential file: "))[17:].strip())
        say(f"  Credential file: {path.name} (in {path.parent})")
        return path

    def write_gateway_config(self, snap: dict[str, Any], credential: Path) -> None:
        config = {
            "database": "gateway.sqlite3",
            "credential_file": "gateway.credential",
            "address": self.gateway_address(),
            "provisioning": {
                "tenant_id": snap["tenant_id"], "site_id": snap["site"]["site_id"],
                "gateway_id": snap["gateway"]["gateway_id"], "source_mode": "SIMULATED",
                "permitted_source_ids": sorted(s["source_id"] for s in snap["sources"]),
                "sequence_epoch": "s2-demo-epoch-1",
            },
            "diagnostics": {"emission_cadence_seconds": self.args.cadence_seconds},
            "upload": {"server_url": self.https, "upload_credential_file": str(credential),
                       "ca_file": str(self.tls / "server.crt"), "timeout_seconds": 10,
                       "batches_per_pass": 25, "interval_seconds": 3600},
        }
        (self.gw / "gateway.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    def gw_db(self, sql: str, *params: Any) -> list[tuple]:
        import sqlite3

        db = sqlite3.connect(f"file:{(self.gw / 'gateway.sqlite3').as_posix()}?mode=ro", uri=True, timeout=10)
        try:
            return db.execute(sql, params).fetchall()
        finally:
            db.close()

    def batch_states(self) -> str:
        rows = self.gw_db("SELECT state, COUNT(*) FROM upload_batch GROUP BY state ORDER BY state")
        return ", ".join(f"{s} {n}" for s, n in rows) or "none"

    def sealed_inventory(self) -> dict[str, list[dict[str, Any]]]:
        """Every sealed batch at the gateway and its envelopes (parsed), by batch ID."""
        rows = self.gw_db("SELECT i.batch_id, o.envelope_text FROM batch_item i "
                          "JOIN envelope_outbox o ON o.message_id = i.message_id ORDER BY i.batch_id, i.ordinal")
        found: dict[str, list[dict[str, Any]]] = {}
        for batch_id, text in rows:
            found.setdefault(batch_id, []).append(json.loads(text))
        return found

    def deliver(self, max_batches: int = 25) -> dict[str, Any]:
        return self.link.call("deliver", {"max_batches": max_batches})

    def deliver_all(self, label: str) -> None:
        passes = 0
        while True:
            result = self.deliver(25)["batches"]
            passes += 1
            say(f"  pass {passes:>2}: attempted {result['attempted']:>2} acked {result['acked']:>2} "
                f"in_progress {result['in_progress']} refused {result['refused']} retrying {result['retrying']}"
                f" | gateway batches: {self.batch_states()}")
            if result["attempted"] == 0:
                return
            if result["stopped"]:
                say(f"  pass stopped: {result['stopped']}")
                return

    def lab(self, method: str, path: str, body: Any = None, expect: int | None = 200) -> Any:
        status, payload = self.call(method, "/api/simulator-lab" + path, body)
        if expect is not None and status != expect:
            raise SystemExit(f"{method} {path} -> {status}: {json.dumps(payload)[:600]}")
        return payload

    def new_run(self, label: str) -> str:
        body = {
            "site_id": SITE, "foundation_version": 2, "scenario_id": "kobo-daytime-post-run-publication",
            "scenario_version": 1, "interval": {"start_time": START, "end_time": END}, "timestep_minutes": 15,
            "seed": 20260929, "model_profile": {"profile_id": "daytime-mini-grid", "profile_version": 1},
            "publication_profile": {"profile_id": "registered-kobo-publication", "profile_version": 2},
            "run_inputs": [],
        }
        run = self.lab("POST", "/runs", body, expect=201)["run"]
        say(f"  {label}: run {run['run_id']} ({run.get('execution_status')})")
        return run["run_id"]

    def commit_summary(self, run_id: str) -> dict[str, Any]:
        payload = self.lab("GET", f"/runs/{run_id}/commit")
        release = payload.get("registered_release") or {}
        delivery = release.get("delivery") or {}
        schedule = release.get("publication_schedule") or {}
        say(f"  GET commit: commit={payload.get('commit')} fully_released={payload.get('fully_released')} "
            f"batches_by_state={delivery.get('batches_by_state')} gap={release.get('publication_gap')} "
            f"schedule={schedule.get('state') or schedule.get('ordinary_publication')}")
        blockers = release.get("release_blockers") or []
        if blockers:
            say(f"  release blockers: {json.dumps(blockers)[:400]}")
        return payload

    def health(self, label: str | None) -> dict[str, Any]:
        status, payload = self.call("GET", f"/api/sites/{SITE}/gateway-health")
        gateways = (payload or {}).get("gateways") or [{}]
        gateway = gateways[0]
        if label is not None:
            say(f"  gateway-health ({label}): {status} status={gateway.get('status')} "
                f"last_server_contact={gateway.get('last_server_contact')} "
                f"declared_cadence_seconds={gateway.get('declared_cadence_seconds')} "
                f"basis={gateway.get('status_basis')}")
        return gateway

    def pg_counts(self) -> dict[str, int]:
        import psycopg

        url = self.db_url.replace("postgresql+psycopg://", "postgresql://")
        with psycopg.connect(url) as conn:
            return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    for t in ("ingestion_batch", "accepted_evidence", "ingestion_disposition", "batch_refusal")}

    def valued_batch(self) -> tuple[str, str]:
        """An ACKED batch holding a reading with a numeric value."""
        for batch_id, text in self.gw_db("SELECT batch_id, payload_text FROM upload_batch WHERE state='ACKED' "
                                         "ORDER BY created_at"):
            if any(json.loads(e)["payload"].get("value") is not None for e in json.loads(text)["envelopes"]):
                return batch_id, text
        raise SystemExit("no ACKED batch holds a numeric reading")

    @staticmethod
    def reseal_with_changed_value(text: str) -> str:
        """The same batch ID and message IDs, one value changed, sealed as valid canonical Batch V2."""
        from assetops_contracts.ingestion_batch_v2 import seal_batch_v2
        from assetops_contracts.source_envelope import canonical_json

        batch = json.loads(text)
        envelopes = []
        changed = False
        for envelope_text in batch["envelopes"]:
            envelope = json.loads(envelope_text)
            if not changed and envelope["payload"].get("value") is not None:
                envelope["payload"]["value"] = str(int(float(envelope["payload"]["value"])) + 1)
                changed = True
            envelopes.append(canonical_json(envelope))
        _, resealed = seal_batch_v2(
            site_id=batch["site_id"], gateway_id=batch["gateway_id"], source_id=batch["source_id"],
            source_mode=batch["source_mode"], foundation_version=batch["configuration"]["foundation_version"],
            foundation_valid_from=batch["configuration"]["foundation_valid_from"],
            binding_set_id=batch["mapping"]["binding_set_id"], binding_version=batch["mapping"]["version"],
            snapshot_sha256=batch["mapping"]["snapshot_sha256"], envelope_texts=envelopes)
        return resealed

    @staticmethod
    def fault_fixture(text: str) -> tuple[str, str, str]:
        """A clearly labelled FAULT FIXTURE (not gateway output): a new canonical Batch V2
        of two envelopes copied from a sealed reading under a fixture sequence epoch, 30 s
        later: one valid, one naming a signal no binding maps (per-record invalid).
        Returns (body, valid message ID, invalid message ID)."""
        from datetime import datetime, timedelta

        from assetops_contracts.ingestion_batch_v2 import seal_batch_v2
        from assetops_contracts.source_envelope import canonical_json
        from assetops_contracts.source_envelope_v3 import v3_message_id

        batch = json.loads(text)
        template = next(json.loads(e) for e in batch["envelopes"] if json.loads(e)["payload"].get("value") is not None)

        def later(instant: str) -> str:
            moved = datetime.fromisoformat(instant.replace("Z", "+00:00")) + timedelta(seconds=30)
            return moved.strftime("%Y-%m-%dT%H:%M:%SZ")

        texts, ids = [], []
        for sequence, signal in ((1, template["source"]["signal_id"]), (2, "fault-fixture-unbound-signal")):
            envelope = json.loads(json.dumps(template))
            src = envelope["source"]
            envelope["message"] = {"message_id": v3_message_id(
                site_id=src["site_id"], gateway_id=src["gateway_id"], source_id=src["source_id"],
                sequence_epoch="fault-fixture-epoch", sequence=sequence),
                "sequence_epoch": "fault-fixture-epoch", "sequence": sequence}
            src["signal_id"] = signal
            envelope["timing"]["source_time"] = later(envelope["timing"]["source_time"])
            envelope["timing"]["published_at"] = later(envelope["timing"]["published_at"])
            texts.append(canonical_json(envelope))
            ids.append(envelope["message"]["message_id"])
        _, body = seal_batch_v2(
            site_id=batch["site_id"], gateway_id=batch["gateway_id"], source_id=batch["source_id"],
            source_mode=batch["source_mode"], foundation_version=batch["configuration"]["foundation_version"],
            foundation_valid_from=batch["configuration"]["foundation_valid_from"],
            binding_set_id=batch["mapping"]["binding_set_id"], binding_version=batch["mapping"]["version"],
            snapshot_sha256=batch["mapping"]["snapshot_sha256"], envelope_texts=texts)
        return body, ids[0], ids[1]

    def bearer(self, credential: Path) -> dict[str, str]:
        return {"Authorization": "Bearer " + credential.read_text(encoding="utf-8").strip()}

    def run(self) -> None:
        self.setup()
        try:
            self.flow()
            (self.work / "demo-result.json").write_text(json.dumps(self.result, indent=2), encoding="utf-8")
            say()
            say(f"Result: {json.dumps(self.result)}")
        finally:
            step("Stopping every process this script started")
            self.stop_all()
            say("  stopped: tls-server, lab-api, gateway")

    def flow(self) -> None:
        step("2. Legacy comparison for KOBO-001 in this environment (schema v3: fingerprinted and bound to this copy's store root)")
        out = self.py("-m", "assetops_backend.evidence_migration", "run", "--tenant", "demo", "--site", SITE,
                      check=False)
        say("  " + " | ".join(out.stdout.strip().splitlines()))

        step("3. Provision the gateway: one-time protected upload credential (owner-only DACL)")
        self.start_lab()
        snap = self.snapshot()
        self.gateway_external_id = snap["gateway"]["gateway_external_id"]
        sources = [s["source_external_id"] for s in snap["sources"]]
        credential = self.issue(sources)
        self.write_gateway_config(snap, credential)
        self.start_tls()
        say(f"  TLS upload server {self.https}; Lab/product API {self.http}; gateway pipe {self.gateway_address()}")

        step("4. Central diagnostics: none before the gateway reports, then its first receipt")
        self.health("before the gateway has ever reported")
        self.start_gateway()  # it emits a diagnostic for the current cadence slot and uploads it on start
        self.result["credential_first"] = credential.name
        for _ in range(40):
            gateway = self.health(None)
            if gateway.get("last_server_contact"):
                break
            time.sleep(0.5)
        self.health("after the gateway's first diagnostic receipt")
        local = self.lab("GET", "/gateway/diagnostics")
        say(f"  Lab's local diagnostic read: {json.dumps(local)[:300]}")

        step("5. A registered Kobo Lab run (post-run publication profile v2) executed to the end")
        run_id = self.new_run("main run")
        self.result["main_run"] = run_id
        self.lab("POST", f"/runs/{run_id}/execution/start")
        self.lab("POST", f"/runs/{run_id}/execution/run-to-end")
        pub = self.lab("GET", f"/runs/{run_id}/publication")
        say(f"  publication after run-to-end: {json.dumps(pub)[:500]}")
        before = self.sealed_inventory()
        say(f"  sealed at the gateway after run-to-end: {len(before)} batches, "
            f"{sum(len(m) for m in before.values())} envelopes (the earlier 245/292 proof stopped here)")
        say("  The closing 15:00 reading is due after the run; advance the run's virtual publication clock.")
        adv = self.lab("POST", f"/runs/{run_id}/publication/advance", {"instant": "2026-09-30T15:10:00Z"},
                       expect=None)
        say(f"  advance to 15:10Z: {json.dumps(adv)[:400]}")
        after = self.sealed_inventory()
        say(f"  sealed after the post-run advance: {len(after)} batches, "
            f"{sum(len(m) for m in after.values())} envelopes")
        for batch_id in sorted(set(after) - set(before)):
            for envelope in after[batch_id]:
                say(f"  added by the advance (publication profile registered-kobo-publication v2): batch {batch_id} "
                    f"source {envelope['source']['source_id']} "
                    f"{envelope['source']['device_id']}/{envelope['source']['signal_id']} "
                    f"source_time {envelope['timing']['source_time']} published_at {envelope['timing']['published_at']}")
        self.result["post_run_added"] = sorted(set(after) - set(before))
        self.commit_summary(run_id)

        step("6. Commit: release this run's sealed batches to the gateway (no Evidence written by the Lab)")
        released = self.lab("POST", f"/runs/{run_id}/commit", expect=None)
        say(f"  POST commit: {json.dumps(released)[:300]}")
        say(f"  gateway batches: {self.batch_states()}")

        step("7. Outage: the TLS server is down for the first pass; bytes stay READY")
        self.stop("tls-server")
        result = self.deliver(3)["batches"]
        say(f"  pass during outage: {json.dumps(result)}")
        failed = self.gw_db("SELECT batch_id, sha256, attempt_count, last_error_code FROM upload_batch "
                            "WHERE attempt_count > 0 ORDER BY created_at LIMIT 3")
        for row in failed:
            say(f"  {row[0]} sha256={row[1][:16]}.. attempts={row[2]} last_error={row[3]}")
        self.start_tls()
        time.sleep(6)  # the first retry backs off 5 s
        say("  TLS server back; delivering all batches with progress:")
        self.deliver_all("main")
        retried = failed[0]
        status, receipt = self.call("GET", f"/api/ingestion/batches/{retried[0]}", base=self.https,
                                    headers=self.bearer(credential))
        say(f"  exact-byte retry: gateway sha256 {retried[1]} | central receipt {status} "
            f"payload_sha256={(receipt or {}).get('payload_sha256')} counts={(receipt or {}).get('counts')}")
        self.commit_summary(run_id)
        self.rotation_and_refusals(run_id, credential, snap, sources)
        self.terminal_gap()
        self.readback(run_id)
        self.legacy_gate_after()

    def rotation_and_refusals(self, run_id: str, old: Path, snap: dict[str, Any], sources: list[str]) -> None:
        step("8. Duplicate identical bytes and same batch ID with changed bytes")
        batch_id, text = self.valued_batch()
        raw = text.encode("utf-8")
        before = self.pg_counts()
        status, first = self.call("POST", "/api/ingestion/batches", raw=raw, base=self.https,
                                  headers=self.bearer(old))
        say(f"  identical bytes again: {status} counts={(first or {}).get('counts')} "
            f"completed_at={(first or {}).get('completed_at')}")
        say(f"  ledger rows before/after the identical retry: {before} / {self.pg_counts()}")
        changed = self.reseal_with_changed_value(text).encode("utf-8")
        say(f"  resealed batch: same batch_id {json.loads(changed)['batch_id'] == batch_id}, "
            f"valid canonical Batch V2 with one reading's value changed, bytes differ {changed != raw}")
        status, conflict = self.call("POST", "/api/ingestion/batches", raw=changed, base=self.https,
                                     headers=self.bearer(old))
        say(f"  same batch ID, one changed byte run: {status} {json.dumps(conflict)[:300]}")
        say(f"  ledger rows after the conflicting attempt: {self.pg_counts()}")
        step("8b. FAULT FIXTURE (labelled test input, not gateway output): one valid and one invalid sibling")
        say("  The ordinary sealing gateway never emits an invalid envelope. This script builds a separate Batch V2")
        say("  of two envelopes under a fixture sequence epoch and posts it over the normal authenticated HTTPS route.")
        fixture, valid_id, invalid_id = self.fault_fixture(text)
        status, receipt = self.call("POST", "/api/ingestion/batches", raw=fixture.encode("utf-8"), base=self.https,
                                    headers=self.bearer(old))
        decisions = {d.get("message_id"): d for d in (receipt or {}).get("dispositions") or []}
        say(f"  fault-fixture batch {json.loads(fixture)['batch_id']}: {status} counts={(receipt or {}).get('counts')}")
        for label, mid in (("valid sibling", valid_id), ("invalid sibling", invalid_id)):
            d = decisions.get(mid) or {}
            say(f"  {label}: ordinal {d.get('ordinal')} decision {d.get('decision')} "
                f"evidence_id {d.get('evidence_id')} rejection {json.dumps(d.get('rejection'))[:200]}")
        self.result["fault_fixture"] = {"batch_id": json.loads(fixture)["batch_id"], "valid": valid_id,
                                        "invalid": invalid_id}
        status, wrong = self.call("POST", "/api/ingestion/batches", raw=raw, base=self.https,
                                  headers={"Authorization": "Bearer aog1.0000.not-a-secret"})
        say(f"  wrong credential: {status} {json.dumps(wrong)[:200]}")
        status, plain = self.call("POST", "/api/ingestion/batches", raw=raw, base=self.http,
                                  headers=self.bearer(old))
        say(f"  same upload over plain HTTP: {status} {json.dumps(plain)[:200]}")

        step("9. Credential rotation: issue a new versioned file; the old one stops authenticating at once")
        new = self.issue(sources)
        status, refused = self.call("GET", f"/api/ingestion/batches/{batch_id}", base=self.https,
                                    headers=self.bearer(old))
        say(f"  old credential after rotation: {status} {json.dumps(refused)[:200]}")
        say(f"  old file still on disk, untouched: {old.exists()}")
        self.stop("gateway")
        self.write_gateway_config(snap, new)
        self.start_gateway()
        say(f"  gateway restarted with upload_credential_file -> {new.name}; sealed bytes unchanged")
        status, receipt = self.call("GET", f"/api/ingestion/batches/{batch_id}", base=self.https,
                                    headers=self.bearer(new))
        say(f"  new credential reads the same receipt: {status} payload_sha256="
            f"{(receipt or {}).get('payload_sha256')}")
        self.link.call("emit_diagnostic", {})
        diag = self.deliver(1)["diagnostics"]
        say(f"  diagnostics pass with the new credential: {json.dumps(diag)[:200]}")
        self.health("after the rotation and gateway restart")
        self.new_credential = new
        self.result["credential_current"] = new.name

    def terminal_gap(self) -> None:
        step("10. Terminal publication gap: the gateway clock passes a boundary the run had not reached")
        run_id = self.new_run("gap run")
        self.result["gap_run"] = run_id
        self.lab("POST", f"/runs/{run_id}/execution/start")
        self.lab("POST", f"/runs/{run_id}/execution/step", {"boundaries": 4, "from_boundary": 0})
        moved = self.link.call("advance_publication_clock", {"lab_run_ref": run_id,
                                                             "instant": "2026-09-30T05:00:00Z"})
        say(f"  gateway clock forced to 05:00Z (fault fixture over the local channel): {json.dumps(moved)[:200]}")
        self.lab("POST", f"/runs/{run_id}/execution/run-to-end")
        before = self.lab("GET", f"/runs/{run_id}/publication")
        status, refused = self.call("POST", f"/api/simulator-lab/runs/{run_id}/publication/advance",
                                    {"instant": "2026-09-30T15:10:00Z"})
        after = self.lab("GET", f"/runs/{run_id}/publication")
        say(f"  later advance: {status} {json.dumps(refused)[:300]}")
        say(f"  publication read unchanged by the refusal: {before == after}")
        released = self.lab("POST", f"/runs/{run_id}/commit", expect=None)
        say(f"  POST commit: {json.dumps(released)[:200]}")
        before_n = self.pg_counts()["accepted_evidence"]
        self.deliver_all("gap")
        after_n = self.pg_counts()["accepted_evidence"]
        say(f"  accepted readings before/after the gap run's upload: {before_n} / {after_n}"
            f" (the gap run added {after_n - before_n}); the page total is the main run's readings,"
            " plus the fault fixture's valid sibling, plus these")
        self.commit_summary(run_id)

    def readback(self, run_id: str) -> None:
        step("11. Site Evidence read back from Postgres (selected source-time window)")
        window = "from=2026-09-30T03:00:00Z&to=2026-09-30T15:00:01Z"
        status, ev = self.call("GET", f"/api/sites/{SITE}/evidence?{window}")
        say(f"  evidence {status}: store={ev.get('store')} state={ev.get('state')} states={ev.get('states')}")
        say(f"  counts={json.dumps(ev.get('counts'))[:300]}")
        say(f"  projection={json.dumps(ev.get('projection'))[:300]}")
        status, page = self.call("GET", f"/api/sites/{SITE}/evidence/records?from=2026-09-30T15:00:00Z"
                                        f"&to=2026-09-30T15:00:01Z&limit=50")
        records = (page or {}).get("records") or []
        say(f"  closing-boundary (15:00:00Z) readings accepted: {len(records)}")
        status, rej = self.call("GET", f"/api/sites/{SITE}/evidence/rejections")
        items = (rej or {}).get("rejections") or []
        say(f"  rejections route: {status}; {len(items)} refused readings; kinds "
            f"{sorted({str(r.get('kind')) for r in items})}")
        fixture = self.result.get("fault_fixture") or {}
        for item in items:
            if item.get("batch_id") == fixture.get("batch_id") or item.get("message_id") == fixture.get("invalid"):
                say(f"  after reload, the FAULT FIXTURE's invalid sibling is on the Site rejection route: "
                    f"{json.dumps(item)[:400]}")
        status, everything = self.call("GET", f"/api/sites/{SITE}/evidence")
        listed = [b for b in (everything or {}).get("batches") or [] if b.get("batch_id") == fixture.get("batch_id")]
        say(f"  after reload, the fault-fixture batch on Site Evidence: {json.dumps(listed)[:400]}")
        if records:
            first = records[0]
            status, detail = self.call("GET", f"/api/sites/{SITE}/evidence/records/{first['evidence_id']}")
            say(f"  one 15:00 reading: {status} keys={sorted((detail or {}).keys())[:12]}")
            receipt = (detail or {}).get("receipt") or {}
            say(f"  receipt: batch={receipt.get('batch_id')} ordinal={receipt.get('ordinal')} "
                f"received_at={receipt.get('received_at')} decided_at={receipt.get('decided_at')}")
            link = f"/sites/{SITE}/evidence?{window}&view=analysis&record={first['evidence_id']}"
            say(f"  selected-window link: {link}")
            self.result.update(record=first["evidence_id"], link=link)
        self.health("now")
        if self.args.stale_wait:
            self.stop("gateway")
            wait = 2 * self.args.cadence_seconds + 5
            say(f"  gateway stopped; waiting {wait} s (two declared cadences) with no contact ...")
            time.sleep(wait)
            self.health("after two declared cadences of silence")
            self.start_gateway()
            for _ in range(40):
                if self.health(None).get("status") == "CURRENT":
                    break
                time.sleep(0.5)
            self.health("after the gateway is back")

    def legacy_gate_after(self) -> None:
        step("12. The empty-set comparison still opens the read (registered Commit writes no legacy artifact)")
        out = self.py("-m", "assetops_backend.evidence_migration", "show", "--site", SITE, check=False)
        say("  " + " | ".join(out.stdout.strip().splitlines())[:400])

    def serve(self) -> None:
        snap_needed = not (self.gw / "gateway.json").exists()
        if snap_needed:
            raise SystemExit("No demo work directory yet; run `run` first.")
        # The scripted run drives upload passes itself (interval 3600 s); while
        # serving for the browser, the gateway's own ticker uploads every 15 s so
        # a Commit made on screen reaches the server without a script.
        config_path = self.gw / "gateway.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["upload"]["interval_seconds"] = 15
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        try:
            self.start_tls()
            self.start_gateway()
            self.start_lab()
            say(f"Serving the demo: Lab/product API {self.http} (database {DEMO_DB}), TLS upload {self.https}.")
            say("Frontend, from frontend/:  $env:ASSETOPS_API_PORT=\"%d\"; npm.cmd run dev -- --port 5310 --strictPort"
                % self.args.http_port)
            say(f"Then open http://localhost:5310/sites/{SITE}/evidence . Ctrl+C stops everything.")
            deadline = time.time() + self.args.serve_seconds if self.args.serve_seconds else None
            while all(p.poll() is None for p in self.procs.values()):
                if deadline is not None and time.time() > deadline:
                    say("Serve time elapsed; stopping.")
                    return
                time.sleep(1)
            say("A process exited; stopping the rest.")
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s2_demo_walkthrough.py")
    parser.add_argument("command", choices=("run", "serve", "setup"))
    parser.add_argument("--work", default=str(DEFAULT_WORK))
    parser.add_argument("--tls-port", type=int, default=8643)
    parser.add_argument("--http-port", type=int, default=8610)
    parser.add_argument("--cadence-seconds", type=int, default=60)
    parser.add_argument("--serve-seconds", type=float, default=0,
                        help="serve: stop by itself after this many seconds (0 = until Ctrl+C)")
    parser.add_argument("--no-stale-wait", dest="stale_wait", action="store_false",
                        help="skip the two-cadence silence that shows STALE")
    args = parser.parse_args(argv)
    demo = Demo(args)
    if args.command == "setup":
        demo.setup()
    elif args.command == "run":
        demo.run()
    else:
        demo.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
