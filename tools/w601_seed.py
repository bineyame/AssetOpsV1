"""W6-01a (A1): the W6-01 global work fixture producer (`.agent/W6-01-build-spec.md` section 4).

    python tools/w601_seed.py --db assetops_w601_<unit>_test --fixture {incidents|zero|empty_scope|historical|cursor_change}
        --clock 2026-10-22T12:00:00Z [--append]

Creates (drops first) the private `*_test` database, migrates it to head, imports two tenants and their Sites
(`demo`: KOBO-001, KOBO-002; `w601-other`: KOBO-001) and writes work through the real W4 `WorkService` with the
server-side fixture SERVICE principal `service:w401-fixture` (A1Q Q9), never a browser-supplied actor. Each run has
one frozen fixture clock and an ordered write clock `11:59:00Z`, `11:59:01Z`, ... from `--clock` (successor writes
for `historical` and the `cursor_change --append` step use `12:00:01Z`, `12:00:02Z`). Incident roots occur at
`--clock` minus 2 days 3 hours, requests at minus 2 days 2 hours; a correction keeps its root and occurs one day
before `--clock`. Prints the stored IDs and codes read back from the database as JSON.

`empty_scope` seeds the same rows as `incidents`; the empty scope is the read's access callback denying every Site.
B1 and E1 extend the fixture list (maintenance, preventive, detail, operational). `linked` needs real Finding and
Action producers and is not provided by A1.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
for extra in (REPO, REPO / "backend", REPO / "contracts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from assetops_backend.evidence.composition import build_link_rows_reader  # noqa: E402
from assetops_backend.sites.adapters.import_files import read_import_source  # noqa: E402
from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore  # noqa: E402
from assetops_backend.sites.foundation_service import ImportSource, import_site  # noqa: E402
from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore  # noqa: E402
from assetops_backend.work.service import WorkService  # noqa: E402
from assetops_backend.work_api import W401_FIXTURE_SERVICE_PRINCIPAL_ID  # noqa: E402

PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PG_PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
DB_NAME = re.compile(r"^assetops_w601_[a-z0-9_]{1,40}_test$")
KOBO_SOURCE = REPO / "backend" / "tests" / "fixtures" / "s1" / "kobo-001.yaml"
FIXTURES = ("incidents", "zero", "empty_scope", "historical", "cursor_change")
ACTOR = {"kind": "SERVICE", "id": W401_FIXTURE_SERVICE_PRINCIPAL_ID,
         "attestation": "service=w401-fixture;job=w601-seed;rule=w601/1"}
SITES = (("demo", "KOBO-001"), ("demo", "KOBO-002"), ("w601-other", "KOBO-001"))


def db_url(db: str) -> str:
    return f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{db}"


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() != timedelta(0):
        raise SystemExit("--clock must be a UTC instant")
    return parsed.astimezone(timezone.utc)


def z(at: datetime) -> str:
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class WriteClock:
    """The ordered fixture write clock: each W4 command takes the next instant, one second apart."""

    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        value, self.now = self.now, self.now + timedelta(seconds=1)
        return value


def create_database(db: str) -> str:
    """Drop and recreate the private `*_test` database, then migrate it to head."""
    if not DB_NAME.match(db):
        raise SystemExit(f"--db must match {DB_NAME.pattern} (a private *_test database)")
    import psycopg
    from alembic import command
    from alembic.config import Config

    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PG_PORT}/assetops", autocommit=True) as admin:
        admin.execute(f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)')
        admin.execute(f'CREATE DATABASE "{db}"')
    config = Config(str(REPO / "backend" / "alembic.ini"))
    config.attributes["database_url"] = db_url(db)
    command.upgrade(config, "head")
    return db_url(db)


def import_sites(url: str, clock: datetime) -> dict[tuple[str, str], dict[str, Any]]:
    """Two tenants, three imported Sites, each imported three days before `--clock` (before the window's `to`)."""
    source = read_import_source(str(KOBO_SOURCE))
    store = PostgresFoundationStore(url)
    out = {}
    try:
        for slug, code in SITES:
            record = source.record if code == "KOBO-001" else replace(source.record, site_id=code)
            result = import_site(store, tenant_slug=slug, configured_tenant_slug=slug,
                                 source=ImportSource(path=f"var/sites/{slug}-{code.lower()}.yaml",
                                                     sha256=source.sha256, record=record),
                                 legacy_documents=(), clock=lambda: clock - timedelta(days=3))
            out[(slug, code)] = {"tenant": result.tenant.id, "site": result.site.id, "site_code": code}
    finally:
        engine = getattr(store, "_engine", None)
        if engine is not None:
            engine.dispose()
    return out


class Writer:
    """W4 `WorkService` commands with the injected fixture principal and the ordered write clock."""

    def __init__(self, url: str, clock: Callable[[], datetime], sites: dict[tuple[str, str], dict[str, Any]],
                 fixture_clock: datetime) -> None:
        self.svc = WorkService(PostgresWorkStore(url, link_rows=build_link_rows_reader(),
                                                 test_db_clock_override=clock))
        self.sites, self.clock, self.n = sites, fixture_clock, 0
        self.written: list[dict[str, Any]] = []

    def _key(self) -> str:
        self.n += 1
        return f"w601-{self.n:04d}"

    def incident(self, site: tuple[str, str], title: str) -> dict[str, Any]:
        s = self.sites[site]
        body = {"kind": "INCIDENT", "occurred_at": z(self.clock - timedelta(days=2, hours=3)), "asset_id": None,
                "finding_links": [], "action_links": [], "title": title,
                "narrative": "Operator reported a stop; cause not established.", "cited_accepted_evidence_ids": [],
                "actor": dict(ACTOR), "idempotency_key": self._key()}
        _, made = self.svc.create_case(s["tenant"], s["site"], body, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.written.append({"tenant": slug_of(site), "site_code": s["site_code"], "case_id": made["id"],
                             "code": made["code"], "kind": "INCIDENT", "revision_id": made["revision"]["id"]})
        return made

    def request(self, site: tuple[str, str], incident_id: str | None, title: str) -> dict[str, Any]:
        s = self.sites[site]
        body = {"kind": "MAINTENANCE_REQUEST", "occurred_at": z(self.clock - timedelta(days=2, hours=2)),
                "asset_id": None, "finding_links": [], "action_links": [], "title": title,
                "narrative": "Inspection requested.", "cited_accepted_evidence_ids": [], "actor": dict(ACTOR),
                "idempotency_key": self._key(), **({} if incident_id is None else {"incident_id": incident_id})}
        _, made = self.svc.create_case(s["tenant"], s["site"], body, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        self.written.append({"tenant": slug_of(site), "site_code": s["site_code"], "case_id": made["id"],
                             "code": made["code"], "kind": "MAINTENANCE_REQUEST", "incident_id": incident_id})
        return made

    def assign(self, site: tuple[str, str], case_id: str, assignee: str) -> None:
        s = self.sites[site]
        self.svc.post_event(s["tenant"], s["site"], case_id, {
            "kind": "ASSIGN", "occurred_at": z(self.clock - timedelta(days=1)), "payload": {"assignee": assignee},
            "actor": dict(ACTOR), "idempotency_key": self._key()}, W401_FIXTURE_SERVICE_PRINCIPAL_ID)

    def correct(self, site: tuple[str, str], case_id: str, revision_id: str, title: str) -> dict[str, Any]:
        s = self.sites[site]
        _, made = self.svc.post_revision(s["tenant"], s["site"], case_id, {
            "supersedes_revision_id": revision_id, "title": title, "narrative": "Corrected after review.",
            "reason": "Title corrected", "occurred_at": z(self.clock - timedelta(days=1)), "actor": dict(ACTOR),
            "idempotency_key": self._key()}, W401_FIXTURE_SERVICE_PRINCIPAL_ID)
        return made

    def close(self) -> None:
        self.svc._store.dispose()


def slug_of(site: tuple[str, str]) -> str:
    return site[0]


A, B, OTHER = ("demo", "KOBO-001"), ("demo", "KOBO-002"), ("w601-other", "KOBO-001")


def seed(url: str, fixture: str, clock: datetime, *, append: bool = False) -> dict[str, Any]:
    """Write one fixture into an already migrated database whose Sites `import_sites` created."""
    if fixture not in FIXTURES:
        raise SystemExit(f"--fixture must be one of {', '.join(FIXTURES)}")
    sites = import_sites(url, clock) if not append else _existing_sites(url)
    base = clock - timedelta(minutes=1)
    if append:
        if fixture != "cursor_change":
            raise SystemExit("--append applies only to --fixture cursor_change")
        writer = Writer(url, WriteClock(clock + timedelta(seconds=2)), sites, clock)
        try:
            writer.incident(A, "Late incident appended after page one")
        finally:
            writer.close()
        return {"fixture": fixture, "append": True, "written": writer.written, **_ids(sites)}
    writer = Writer(url, WriteClock(base), sites, clock)
    try:
        if fixture != "zero":
            first = writer.incident(A, "Generator stopped")
            second = writer.incident(A, "Inverter fault reported")
            writer.incident(A, "Battery alarm acknowledged")
            writer.incident(A, "Feeder breaker tripped")
            writer.incident(B, "Pump stopped")
            writer.incident(B, "Panel door open")
            writer.incident(OTHER, "Other tenant incident")
            writer.assign(A, first["id"], "Field team A")
            writer.request(A, first["id"], "Inspect starter")
            writer.correct(A, second["id"], second["revision"]["id"], "Inverter fault confirmed")
        if fixture == "historical":
            later = Writer(url, WriteClock(clock + timedelta(seconds=1)), sites, clock)
            try:
                later.correct(A, first["id"], first["revision"]["id"], "Generator stopped twice")
                later.incident(B, "Late incident after the historical cutoff")
            finally:
                later.close()
            writer.written.extend(later.written)
    finally:
        writer.close()
    return {"fixture": fixture, "clock": z(clock), "written": writer.written, **_ids(sites)}


def _existing_sites(url: str) -> dict[tuple[str, str], dict[str, Any]]:
    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    try:
        with engine.connect() as c:
            rows = c.execute(text("SELECT t.slug, s.site_code, t.id, s.id FROM site s JOIN tenant t "
                                  "ON t.id = s.tenant_id")).all()
    finally:
        engine.dispose()
    return {(r[0], r[1]): {"tenant": r[2], "site": r[3], "site_code": r[1]} for r in rows}


def _ids(sites: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    return {"sites": [{"tenant": slug, "site_code": code, "tenant_id": str(v["tenant"]), "site_id": str(v["site"])}
                      for (slug, code), v in sorted(sites.items())]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", required=True)
    parser.add_argument("--fixture", required=True, choices=FIXTURES)
    parser.add_argument("--clock", required=True)
    parser.add_argument("--append", action="store_true", help="cursor_change: append one row at --clock + 2 s")
    args = parser.parse_args(argv)
    clock = utc(args.clock)
    if args.append:
        if not DB_NAME.match(args.db):
            raise SystemExit(f"--db must match {DB_NAME.pattern}")
        url = db_url(args.db)
    else:
        url = create_database(args.db)
    print(json.dumps(seed(url, args.fixture, clock, append=args.append), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
