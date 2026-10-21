"""W4-03 unit 9a: the private two-Site walkthrough for mini-grid decisions and their work connection.

`.agent/W4-03-build-spec.md` "Fixture and one-run commit proof", closure 2 Q1, closure 4 B1/B2/S6/S16 and u5 9a.

    python tools/w403_mini_decisions_walkthrough.py --db assetops_w403_walk_test --work var/w403_walk prepare
    python tools/w403_mini_decisions_walkthrough.py --db assetops_w403_walk_test --work var/w403_walk serve
    python tools/w403_mini_decisions_walkthrough.py --db assetops_w403_walk_test --work var/w403_walk replay
    python tools/w403_mini_decisions_walkthrough.py --db assetops_w403_walk_test --work var/w403_walk capture
    python tools/w403_mini_decisions_walkthrough.py --db assetops_w403_walk_test --work var/w403_walk drop

`prepare` makes the private `*_test` database at head, imports KOBO-001 (the S4 CaseRunner, W1 dispatch Finding F02)
and MG-W402-001 (the W4-02 installer), and writes a random loopback bearer secret to the private work folder.
`serve` runs `create_app(mini_decision_command_access=..., mini_decision_principal=...,
legacy_documents=...)` on 127.0.0.1 (u9b PR-12.4: the KOBO document is the private byte copy of the imported fixture,
its digest checked against the `site_import` record); both callbacks
admit only that bearer for the exact resolved tenant/Site pairs and derive `service:w403-fixture` and its grant on the
server. `replay` runs the W4-02 authored publication and ingestion, the explicit historical reconcile, seeds the MG
work cases in process through W4-01 `WorkService` (`service:w401-fixture`; never a W4-01 HTTP POST), submits the
five W4-03 command types over HTTP, and records the reads (`<work>/replay.json`, no secret). u9b PR-12.5: `replay` is
`replay-positive` (writes `positive.json` and a phase marker) then `replay-late` (requires the marker, writes
`replay.json`); `capture --phase positive` runs between them and `capture --phase late` after. `capture` delegates the
1440/390 captures to `tools/w403-mini-decisions-evidence.mjs`, after seeding the capture stock (four more
Incidents, two more Requests) through W4-01 `WorkService` into `<work>/capture/stock.json`. `drop` drops the
database and work folder that this tool made. Nothing reads private Lab state or inserts accepted evidence directly.

PYTHONPATH must hold backend, backend/tests, contracts, gateway, simulator and host (the brief's list plus tests).
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hmac
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "backend" / "tests" / "fixtures" / "w4" / "w403-mini-decisions.json"
DECISION_PRINCIPAL = "service:w403-fixture"
WORK_PRINCIPAL = "service:w401-fixture"
PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
API_PORT = 9761
MARKER = ".w403-walkthrough-work"
SECRET_FILE = "bearer.secret"
POSITIVE_MARKER = "replay-positive.done"
KOBO_CODE = "KOBO-001"
# u9b PR-12.4: the fixture `prepare` imports KOBO from, and the path the import recorded for it.
KOBO_SOURCE = REPO / "backend" / "tests" / "fixtures" / "s1" / "kobo-001.yaml"
KOBO_RECORDED_PATH = "var/sites/kobo-001.yaml"
KOBO_PRIVATE_COPY = "kobo-001.yaml"


def load_fixture(path: Path = FIXTURE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iso(at: datetime) -> str:
    return at.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def fill(template: dict[str, Any], **values: Any) -> dict[str, Any]:
    """A command from its fixture template: each `<placeholder>` key named in `values` takes the resolved value."""
    out = copy.deepcopy(template)
    for key, value in values.items():
        assert key in out and (out[key] is None or isinstance(out[key], str)), key
        out[key] = value
    assert not [k for k, v in out.items() if isinstance(v, str) and v.startswith("<")], out
    return out


def fixture_callbacks(secret: str, scopes: dict[str, tuple[Any, Any]], grants: set[str] | None = None):
    """Closure 2 Q1 / closure 4 B2: command access and principal for the exact resolved `(tenant, site)` pairs.

    Only a request bearing the loopback bearer secret is admitted; the actor and grant are derived here, never from
    the body. `grants` narrows which Site codes hold the W4-03 write grant (all scoped Sites by default)."""
    from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal

    granted = set(scopes) if grants is None else set(grants)

    def bearer(request) -> bool:
        return hmac.compare_digest(request.headers.get("authorization", ""), f"Bearer {secret}")

    def command_access(request, code: str) -> int | None:
        return None if bearer(request) and code in scopes and code in granted else 403

    def principal(request, code: str):
        if not bearer(request) or code not in scopes:
            return None
        tenant_id, site_id = scopes[code]
        return DecisionPrincipal("SERVICE", DECISION_PRINCIPAL, tenant_id, site_id, GRANT_PREFIX + DECISION_PRINCIPAL)

    return command_access, principal


# ---- in-process steps (database URL in ASSETOPS_TEST_DATABASE_URL / DATABASE_URL) ----

def import_sites(store, engine) -> dict[str, Any]:
    """KOBO-001 through the S4 CaseRunner (W1 F02 dispatch Finding, first three steps) and MG-W402-001 through the W4-02
    installer. Returns scope pairs and the KOBO runner (its Finding store is disposed by the caller)."""
    from test_s4_finding_store_postgres import SPEC, CaseRunner
    from test_w402_reads_postgres import _setup

    runner = CaseRunner(store, engine)
    for step in next(c for c in SPEC["cases"] if c["case_id"] == "F02")["steps"][:3]:
        runner.step(step)
    installed, t, s = _setup(store, engine)
    return {"runner": runner, "installed": installed,
            "scopes": {"KOBO-001": (runner.tenant, runner.site), "MG-W402-001": (t, s)}}


def publish_and_ingest(engine, installed, fixture: dict[str, Any], variant: str) -> list[str]:
    """The W4-02 authored path: each sealed batch is published under `assetops.w4-mini-depth-cases` v1, then accepted
    through public ingestion. Returns the variant's accepted evidence IDs."""
    from test_w402_authored_v4_postgres import cases, ingestion, principal, snapshot

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.composition import build_authored_fixture_specs
    from assetops_backend.publish_source import main as publish_source_main

    src = fixture["source"]
    doc, sha = snapshot(engine, installed.binding_set.id)
    spec, service, specs = cases.load_spec(), ingestion(), build_authored_fixture_specs()
    batches = cases.build_batches(spec, doc, sha, variant)
    url = os.environ["ASSETOPS_TEST_DATABASE_URL"]
    for b in batches:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.json"
            path.write_text(b.body, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = publish_source_main(["--site", fixture["opportunity_site_code"], "--fixture-id",
                                            src["fixture_id"], "--fixture-version", str(src["fixture_version"]),
                                            "--batch-file", str(path)], ledger=PostgresEvidenceLedger(url),
                                           specs=specs)
        if code != 0:
            raise SystemExit(f"publication refused (exit {code}) for {variant} {b.source_id}")
        service.submit(principal(doc), b.body.encode("utf-8"))
    with engine.connect() as c:
        return cases.accepted_ids(c, str(doc["site"]["site_id"]), cases.message_ids(batches))


def ingest_late(engine, installed, fixture: dict[str, Any]) -> list[str]:
    """The late contradictory branch: an authored W4-03 variant accepted through public ingestion after the first
    opportunity selection. It is not published under the W4-02 source (reading 9a-3)."""
    from test_w402_authored_v4_postgres import cases, ingestion, principal, snapshot

    doc, sha = snapshot(engine, installed.binding_set.id)
    spec = {**cases.load_spec(), "variants": [fixture["late_variant"]]}
    batches = cases.build_batches(spec, doc, sha, fixture["late_variant"]["variant"])
    service = ingestion()
    for b in batches:
        service.submit(principal(doc), b.body.encode("utf-8"))
    with engine.connect() as c:
        return cases.accepted_ids(c, str(doc["site"]["site_id"]), cases.message_ids(batches))


def mini_days(engine, days: list[str]) -> None:
    """The W4-02 mini selections of each named local day (its explicit per-hour reconcile)."""
    from datetime import date

    from test_w402_reads_postgres import _reconcile

    _reconcile(engine, [date.fromisoformat(d) for d in days])


def opportunity_cli(reconcile: dict[str, str]) -> list[Any]:
    """The explicit historical reconcile (closure 4 S6), then run pending, through the worker CLI."""
    from assetops_backend.mini_decisions.worker import main as worker_main

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert worker_main(["reconcile", "--site", reconcile["site"], "--from", reconcile["from"],
                            "--to", reconcile["to"]]) == 0
        code = worker_main(["run-pending", "--limit", "100"])
    lines = [json.loads(x) for x in out.getvalue().splitlines() if x.strip()]
    assert code == 0, lines
    return lines


def seed_case(scope, body: dict[str, Any], when: str | None = None) -> str:
    """One W4-01 case through `WorkService` in process with `service:w401-fixture` (B2), never over HTTP.

    `when` replays a recorded `occurred_at`, so the same idempotency key and payload return the same case."""
    from assetops_backend.work.composition import build_work_service

    when = when or iso(datetime.now(timezone.utc) - timedelta(hours=1))
    status, out = build_work_service(os.environ["ASSETOPS_TEST_DATABASE_URL"]).create_case(
        scope[0], scope[1], {**body, "occurred_at": when}, WORK_PRINCIPAL)
    assert status in (200, 201), (status, out)
    return out["id"]


def kobo_revision(engine, site_id) -> tuple[str, str]:
    """The KOBO F02 Finding and its selected (latest) revision, resolved after the run."""
    from sqlalchemy import text

    with engine.connect() as c:
        row = c.execute(text(
            "SELECT f.id AS finding_id, r.id FROM finding f JOIN finding_revision r ON r.finding_id = f.id "
            "WHERE f.site_id = :s ORDER BY r.created_at DESC, r.revision_no DESC LIMIT 1"), {"s": site_id}).one()
    return str(row.finding_id), str(row.id)


# ---- HTTP part (a TestClient in tests, the served loopback API in `replay`) ----

Http = Callable[..., tuple[int, Any]]


def http_replay(http: Http, fixture: dict[str, Any], pins: list[dict[str, Any]], incident: str,
                finding: tuple[str, str] | None) -> dict[str, Any]:
    """The five W4-03 command types over HTTP on their named Sites, then their reads."""
    mg, cmd, rec = fixture["opportunity_site_code"], fixture["commands"], fixture["reconcile"]
    base = f"/api/sites/{mg}"
    out: dict[str, Any] = {}
    status, scenario = http("POST", f"{base}/financials/scenarios", fill(cmd["scenario_positive"],
                                                                         pinned_selection=pins))
    assert status == 201, (status, scenario)
    status, corrected = http("POST", f"{base}/financials/scenarios/{scenario['id']}/revisions", fill(
        cmd["scenario_correction"], pinned_selection=pins, supersedes_revision_id=scenario["revision_id"]))
    assert status == 201, (status, corrected)
    status, no_tariff = http("POST", f"{base}/financials/scenarios", fill(cmd["scenario_missing_tariff"],
                                                                          pinned_selection=pins))
    assert status == 201, (status, no_tariff)
    status, listing = http("GET", f"{base}/opportunities?from={rec['from']}&to={rec['to']}")
    assert status == 200, (status, listing)
    [row] = [r for r in listing["rows"] if r["opportunity"]["first_day"] == fixture["study_days"][0]]
    oid = row["opportunity"]["id"]
    status, link = http("POST", f"{base}/opportunities/{oid}/scenario-links", fill(
        cmd["opportunity_scenario_link"], opportunity_id=oid, scenario_id=scenario["id"]))
    assert status == 201, (status, link)
    status, work = http("POST", f"{base}/work/decision-links", fill(cmd["work_link"], case_id=incident,
                                                                    opportunity_id=oid))
    assert status == 201, (status, work)
    if finding is not None:
        kobo = fixture["alternative_site_code"]
        status, alt = http("POST", f"/api/sites/{kobo}/findings/{finding[0]}/alternatives",
                           fill(cmd["alternative"], finding_revision_id=finding[1]))
        # The S4 F02 revisions carry fixture times; at a DB read time before them the selected revision is not yet
        # visible and the write is 409 DECISION_BASIS_CHANGED (u9 PR-11.1). `run_replay` asserts the exit against DB
        # time; here the observed exit is recorded as-is, with no claim that a row was created.
        out["alternative"] = {"status": status, "body": alt}
    out.update(scenario=scenario, corrected=corrected, no_tariff=no_tariff, opportunity_id=oid,
               scenario_link=link, work_link=work)
    return out


def reads(http: Http, fixture: dict[str, Any], oid: str, cases: list[str], finding: tuple[str, str] | None,
          known_at: str | None = None) -> dict[str, Any]:
    mg, rec = fixture["opportunity_site_code"], fixture["reconcile"]
    base = f"/api/sites/{mg}"
    k = "" if known_at is None else f"&known_at={known_at}"
    out = {"scenarios": http("GET", f"{base}/financials/scenarios")[1],
           "opportunities": http("GET", f"{base}/opportunities?from={rec['from']}&to={rec['to']}{k}")[1],
           "opportunity": http("GET", f"{base}/opportunities/{oid}" + ("" if known_at is None else f"?known_at={known_at}"))[1],
           "contexts": http("GET", f"{base}/work/decision-contexts?case_ids={','.join(cases)}")[1]}
    if finding is not None:
        status, body = http("GET", f"/api/sites/{fixture['alternative_site_code']}/findings/{finding[0]}/"
                                   f"alternatives?revision_id={finding[1]}")
        out["alternatives"] = {"status": status, "body": body}
    return out


def selected_pins(engine, scope, days: list[str]) -> list[dict[str, Any]]:
    """The five selected noon tuples from the public W4-02 renewable read (S16: all five, 6 Oct EXCLUDED included)."""
    from datetime import date

    from test_w403_scenarios_postgres import selected_pins as pins

    return pins(engine, scope[0], scope[1], [date.fromisoformat(d) for d in days])


# ---- operator commands ----

class Walk:
    def __init__(self, db: str, work: str) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,50}_test", db):
            raise SystemExit(f"Refused: --db {db!r} must be a plain lower-case identifier ending in _test")
        path = (REPO / work).resolve() if not Path(work).is_absolute() else Path(work).resolve()
        if path.parent != (REPO / "var").resolve():
            raise SystemExit(f"Refused: --work {path} must be a folder directly under {REPO / 'var'}")
        self.db, self.work = db, path
        self.url = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{db}"
        os.environ["ASSETOPS_TEST_DATABASE_URL"] = os.environ["DATABASE_URL"] = self.url
        for k in ("ASSETOPS_TEST_RUN_ID", "ASSETOPS_TEST_DATABASE_BASE_URL"):
            os.environ.pop(k, None)
        sys.path.insert(0, str(REPO / "backend" / "tests"))

    def owned(self) -> bool:
        return (self.work / MARKER).is_file() and f"db={self.db}" in (self.work / MARKER).read_text(encoding="utf-8")

    def secret(self) -> str:
        return (self.work / SECRET_FILE).read_text(encoding="ascii").strip()

    def ids(self) -> dict[str, Any]:
        return json.loads((self.work / "ids.json").read_text(encoding="utf-8"))

    def prepare(self) -> None:
        if self.work.exists() and any(self.work.iterdir()) and not self.owned():
            raise SystemExit(f"Refused: {self.work} is not empty and was not made by this tool for {self.db}")
        self.work.mkdir(parents=True, exist_ok=True)
        (self.work / MARKER).write_text(f"created by tools/w403_mini_decisions_walkthrough.py\ndb={self.db}\n",
                                        encoding="utf-8")
        import pg_harness
        from sqlalchemy import create_engine

        from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

        pg_harness.fresh_database()
        engine = create_engine(self.url)
        pg_harness.assert_at_head(engine)
        store = PostgresFoundationStore(self.url)
        sites = import_sites(store, engine)
        pg_harness.dispose(sites["runner"].findings, store)
        engine.dispose()
        (self.work / SECRET_FILE).write_text(secrets.token_urlsafe(32), encoding="ascii")
        # PR-12.4: the exact fixture bytes the import read, kept privately for the served app's legacy documents.
        (self.work / KOBO_PRIVATE_COPY).write_bytes(KOBO_SOURCE.read_bytes())
        scopes = {k: [str(v[0]), str(v[1])] for k, v in sites["scopes"].items()}
        (self.work / "ids.json").write_text(json.dumps({"scopes": scopes}, indent=2), encoding="utf-8")
        print(f"prepared {self.db}: {sorted(scopes)}; next: serve, then replay")

    def app(self):
        from uuid import UUID

        from assetops_backend import main

        scopes = {k: (UUID(v[0]), UUID(v[1])) for k, v in self.ids()["scopes"].items()}
        access, principal = fixture_callbacks(self.secret(), scopes)
        return main.create_app(mini_decision_command_access=access, mini_decision_principal=principal,
                               legacy_documents=self.legacy_documents())

    def legacy_documents(self) -> Callable[[], tuple[Any, ...]]:
        """u9b PR-12.4: the served app's legacy Site documents.

        KOBO-001 is the imported fixture's own document: the digest is derived from the private byte copy and must
        equal the `site_import` record (path `var/sites/kobo-001.yaml`), or the app is not built. The operator's
        gitignored `var/sites/kobo-001.yaml` is not used, and the product collision check is unchanged: every other
        legacy document whose code does not collide with KOBO-001 is still returned.
        """
        import hashlib

        from sqlalchemy import create_engine, text

        from assetops_backend.sites.composition import legacy_site_documents
        from assetops_backend.sites.foundation_service import LegacyDocument
        from assetops_backend.sites.identity import site_id_key

        copy_path = self.work / KOBO_PRIVATE_COPY

        def digest() -> str:
            return hashlib.sha256(copy_path.read_bytes()).hexdigest()

        engine = create_engine(self.url)
        try:
            with engine.connect() as c:
                rows = c.execute(text("SELECT i.source_path, i.source_sha256 FROM site_import i JOIN site s "
                                      "ON s.tenant_id = i.tenant_id AND s.id = i.site_id WHERE s.site_code = :code"),
                                 {"code": KOBO_CODE}).all()
        finally:
            engine.dispose()
        if len(rows) != 1 or rows[0][0] != KOBO_RECORDED_PATH:
            raise SystemExit(f"Refused: {KOBO_CODE} import record is {rows!r}, not one {KOBO_RECORDED_PATH} import")
        recorded = rows[0][1]
        if digest() != recorded:
            raise SystemExit(f"Refused: {copy_path} sha256 {digest()} != imported {recorded}")
        others = tuple(d for d in legacy_site_documents() if site_id_key(d.site_code) != site_id_key(KOBO_CODE))

        def documents() -> tuple[Any, ...]:
            now = digest()
            if now != recorded:  # the private copy changed after the check: never serve a made-up digest
                raise RuntimeError(f"{copy_path} sha256 {now} != imported {recorded}")
            return (LegacyDocument(site_code=KOBO_CODE, path=KOBO_RECORDED_PATH, sha256=now), *others)
        return documents

    def serve(self) -> None:
        import uvicorn

        uvicorn.run(self.app(), host="127.0.0.1", port=API_PORT)

    def http(self) -> Http:
        import urllib.error
        import urllib.request

        def call(method: str, path: str, body: Any = None) -> tuple[int, Any]:
            data = None if body is None else json.dumps(body).encode("utf-8")
            req = urllib.request.Request(f"http://127.0.0.1:{API_PORT}{path}", data=data, method=method,
                                         headers={"Authorization": f"Bearer {self.secret()}",
                                                  "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    return r.status, json.loads(r.read() or b"null")
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read() or b"null")
        return call

    def _context(self):
        from uuid import UUID

        from sqlalchemy import create_engine

        fixture, ids = load_fixture(), self.ids()
        scopes = {k: (UUID(v[0]), UUID(v[1])) for k, v in ids["scopes"].items()}
        engine = create_engine(self.url)
        return fixture, scopes, engine, _Installed.read(engine, scopes["MG-W402-001"][1])

    def replay_positive(self) -> dict[str, Any]:
        """u9b PR-12.5 phase 1, idempotent: once its marker exists the stored `positive.json` is returned unchanged."""
        if (self.work / POSITIVE_MARKER).is_file():
            print(f"replay-positive already done: {self.work / 'positive.json'}")
            return json.loads((self.work / "positive.json").read_text(encoding="utf-8"))
        fixture, scopes, engine, installed = self._context()
        try:
            record = run_replay_positive(engine, installed, fixture, scopes, self.http())
        finally:
            engine.dispose()
        (self.work / "positive.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (self.work / POSITIVE_MARKER).write_text(f"opportunity_id={record['writes']['opportunity_id']}\n",
                                                 encoding="utf-8")
        print(f"replay-positive: {self.work / 'positive.json'}; next: capture --phase positive, then replay-late")
        return record

    def replay_late(self) -> None:
        """u9b PR-12.5 phase 2: requires the positive marker; never redoes the positive commands."""
        if not (self.work / POSITIVE_MARKER).is_file():
            raise SystemExit("Refused: replay-late needs replay-positive first (no phase marker)")
        if (self.work / "replay.json").is_file():
            raise SystemExit(f"Refused: {self.work / 'replay.json'} exists; the late phase runs once")
        record = json.loads((self.work / "positive.json").read_text(encoding="utf-8"))
        fixture, scopes, engine, installed = self._context()
        try:
            record = run_replay_late(engine, installed, fixture, self.http(), record)
        finally:
            engine.dispose()
        (self.work / "replay.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"replayed: {self.work / 'replay.json'}")

    def replay(self) -> None:
        self.replay_positive()
        self.replay_late()

    def stock(self) -> dict[str, Any]:
        """u9 9b capture stock: four more MG Incidents and two more Requests through W4-01 `WorkService`.

        Recorded in `<work>/capture/stock.json`, separately from `replay.json`; never a direct case-row insert. The
        W4-01 idempotency keys make a second `capture` return the same cases.
        """
        from uuid import UUID

        fixture, ids = load_fixture(), self.ids()
        [incident] = [c for c in fixture["commands"]["cases"] if c["body"]["kind"] == "INCIDENT"]
        [request] = [c for c in fixture["commands"]["cases"] if c["body"]["kind"] == "MAINTENANCE_REQUEST"]
        scope = tuple(UUID(v) for v in ids["scopes"][incident["site_code"]])
        path = self.work / "capture" / "stock.json"
        # u9b PR-12.5: a second `capture` (late phase) replays the recorded payloads under the same W4-01 keys.
        prior = json.loads(path.read_text(encoding="utf-8")).get("occurred_at", {}) if path.is_file() else {}
        out: dict[str, Any] = {"site_code": incident["site_code"], "principal": WORK_PRINCIPAL, "incidents": {},
                               "requests": {}, "occurred_at": {}}
        for kind, template, n in (("incidents", incident, 4), ("requests", request, 2)):
            for i in range(1, n + 1):
                key = f"w403-capture-{kind}-{i}"
                body = {**template["body"], "idempotency_key": key, "title": f"{template['body']['title']} ({i + 1})"}
                when = prior.get(key) or iso(datetime.now(timezone.utc) - timedelta(hours=1))
                out[kind][key] = seed_case(scope, body, when)
                out["occurred_at"][key] = when
                if key in prior and path.is_file():
                    assert out[kind][key] == json.loads(path.read_text(encoding="utf-8"))[kind][key], key
        out["counts"] = {"incidents_added": len(out["incidents"]), "requests_added": len(out["requests"])}
        (self.work / "capture").mkdir(parents=True, exist_ok=True)
        (self.work / "capture" / "stock.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        return out

    def capture(self, web: str, phase: str = "late") -> None:
        self.stock()
        done = subprocess.run(["node", str(REPO / "tools" / "w403-mini-decisions-evidence.mjs"), web,
                               str(self.work / "capture"), phase], cwd=REPO)
        raise SystemExit(done.returncode)

    def drop(self) -> None:
        if not self.owned():
            raise SystemExit(f"Refused: {self.work} does not record that this tool made {self.db}")
        import psycopg

        admin = f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops"
        with psycopg.connect(admin, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {self.db} WITH (FORCE)")
        shutil.rmtree(self.work)
        print(f"dropped {self.db} and {self.work}")


class _Installed:
    """The MG install's binding-set revision, re-read from the database for a later `replay` process."""

    def __init__(self, binding_set_id) -> None:
        self.binding_set = type("BindingSet", (), {"id": binding_set_id})()

    @classmethod
    def read(cls, engine, site_id) -> "_Installed":
        from sqlalchemy import text

        with engine.connect() as c:
            return cls(c.execute(text("SELECT id FROM signal_binding_set_revision WHERE site_id = :s "
                                      "AND superseded_at IS NULL ORDER BY version DESC LIMIT 1"),
                                 {"s": site_id}).scalar_one())


def run_replay(engine, installed, fixture: dict[str, Any], scopes: dict[str, tuple[Any, Any]], http: Http,
               performance: bool = True) -> dict[str, Any]:
    """The whole replay after `prepare`: both u9b PR-12.5 phases in order (backend regression use)."""
    record = run_replay_positive(engine, installed, fixture, scopes, http, performance)
    return run_replay_late(engine, installed, fixture, http, record)


def kobo_reads(http: Http, fixture: dict[str, Any], finding: tuple[str, str]) -> dict[str, Any]:
    """u9b PR-12.4: the KOBO Site and the exact F02 Finding read the Alternatives page needs, before any capture."""
    kobo = fixture["alternative_site_code"]
    site_status = http("GET", f"/api/sites/{kobo}")[0]
    status, body = http("GET", f"/api/sites/{kobo}/findings/{finding[0]}?revision_id={finding[1]}")
    detail = body.get("detail") if isinstance(body, dict) else None
    return {"site_status": site_status, "finding_status": status,
            "finding_code": detail.get("code") if isinstance(detail, dict) else None}


def run_replay_positive(engine, installed, fixture: dict[str, Any], scopes: dict[str, tuple[Any, Any]], http: Http,
                        performance: bool = True) -> dict[str, Any]:
    """u9b PR-12.5 phase 1: positive publication, five mini days, both Performance cutovers, opportunity reconcile,
    the W4-01 case seed and the five W4-03 HTTP commands, then the current reads (no late or missing evidence)."""
    mg = scopes[fixture["opportunity_site_code"]]
    record: dict[str, Any] = {"schema_version": fixture["schema_version"]}
    record["accepted"] = {"positive": publish_and_ingest(engine, installed, fixture, "positive")}
    mini_days(engine, fixture["study_days"])
    if performance:
        from assetops_backend.performance_migration import main as performance_main

        exits = {}
        # PR-12.4: the KOBO cutover runs after its F02 setup (`prepare`), as the MG one does after its publication.
        for code in (fixture["opportunity_site_code"], fixture["alternative_site_code"]):
            with contextlib.redirect_stdout(io.StringIO()):
                exits[code] = performance_main(["run", "--tenant", "demo", "--site", code])
        record["performance_exits"] = exits
        record["performance_exit"] = exits[fixture["opportunity_site_code"]]
    record["opportunity_runs"] = [opportunity_cli(fixture["reconcile"])]
    pins = selected_pins(engine, mg, fixture["study_days"])
    cases = {c["body"]["idempotency_key"]: seed_case(scopes[c["site_code"]], c["body"])
             for c in fixture["commands"]["cases"]}
    [incident] = [cases[c["body"]["idempotency_key"]] for c in fixture["commands"]["cases"] if c["linked"]]
    finding = kobo_revision(engine, scopes[fixture["alternative_site_code"]][1])
    record["pins"] = pins
    record["cases"] = cases
    record["finding"] = list(finding)
    from sqlalchemy import text

    # u9 PR-11.1: the served app has no test clock. The F02 revision becomes visible only once DB time reaches its
    # fixture SETUP_AT; until then the exact exit is 409 DECISION_BASIS_CHANGED and no Alternative row exists.
    with engine.connect() as c:
        visible = bool(c.execute(text("SELECT min(created_at) <= clock_timestamp() FROM finding_revision "
                                      "WHERE id = :r"), {"r": finding[1]}).scalar_one())
    record["alternative_basis_visible"] = visible
    record["writes"] = http_replay(http, fixture, pins, incident, finding)
    alt = record["writes"]["alternative"]
    if visible:
        assert alt["status"] == 201, alt
    else:
        assert (alt["status"], alt["body"]["detail"]["code"]) == (409, "DECISION_BASIS_CHANGED"), alt
    oid = record["writes"]["opportunity_id"]
    record["positive"] = reads(http, fixture, oid, list(cases.values()), finding)
    if performance:
        record["kobo_reads"] = kobo_reads(http, fixture, finding)
    detail = record["positive"]["opportunity"]
    # positive.json: the selected Opportunity, its exact pins, the current read and its selected provenance.
    record["positive_selection"] = {
        "opportunity_id": oid,
        "revision_id": (detail.get("opportunity") or {}).get("revision_id"),
        "status": detail.get("status"),
        "currentness": detail.get("currentness"),
        "pins": pins,
        "selected_source_provenance": detail.get("selected_source_provenance"),
    }
    return record


def run_replay_late(engine, installed, fixture: dict[str, Any], http: Http, record: dict[str, Any]) -> dict[str, Any]:
    """u9b PR-12.5 phase 2 on the phase-1 record: `k_before_late`, the fixed 13 October late variant and its rerun,
    then the 8-12 October missing branch. The positive commands are not repeated."""
    from sqlalchemy import text

    oid = record["writes"]["opportunity_id"]
    cases = record["cases"]
    # Late contradictory evidence after the first selection: pending first, then a new head after the rerun.
    with engine.connect() as c:
        record["k_before_late"] = iso(c.execute(text("SELECT clock_timestamp()")).scalar_one())
    record["accepted"]["late"] = ingest_late(engine, installed, fixture)
    record["late_pending"] = reads(http, fixture, oid, list(cases.values()), None)
    mini_days(engine, [fixture["late_variant"]["hours"][0]["day"]])
    record["opportunity_runs"].append(opportunity_cli(fixture["reconcile"]))
    record["late_settled"] = reads(http, fixture, oid, list(cases.values()), None)
    record["late_old_cutoff"] = reads(http, fixture, oid, list(cases.values()), None, record["k_before_late"])
    # Missing branch: the W4-02 missing/conflicting day inside a later five-day study.
    record["accepted"]["missing"] = publish_and_ingest(engine, installed, fixture, fixture["source"]["missing_variant"])
    mini_days(engine, fixture["missing_study_days"])
    record["opportunity_runs"].append(opportunity_cli(fixture["missing_reconcile"]))
    mr = fixture["missing_reconcile"]
    record["missing"] = http("GET", f"/api/sites/{fixture['opportunity_site_code']}/opportunities?from={mr['from']}"
                                    f"&to={mr['to']}")[1]
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True)
    parser.add_argument("--work", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "serve", "replay", "replay-positive", "replay-late", "drop"):
        sub.add_parser(name)
    cap = sub.add_parser("capture")
    cap.add_argument("--web", default="http://localhost:6147")
    cap.add_argument("--phase", choices=("positive", "late"), default="late")
    args = parser.parse_args(argv)
    walk = Walk(args.db, args.work)
    if args.command == "capture":
        walk.capture(args.web, args.phase)
    else:
        getattr(walk, args.command.replace("-", "_"))()
    return 0


if __name__ == "__main__":  # pragma: no cover - operator entry point
    raise SystemExit(main())
