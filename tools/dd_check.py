"""DD checker (spec `specs/DD-demo-data/spec.md` §8.1; D-DD.14, D-DD.31): the independent check of the demo world.

    python tools/dd_check.py --database-url URL [--only C-DD1,C-DD13] [--json]

Each check is a question that can FAIL with its detail. The checker shares no module, list or expected figure with
the simulator or the generators: it reads the clone by SQL, the product's reads through an in-process ASGI client on
the app factory (no port is opened), the manifest's blocks by its own YAML read, and `history.json` by its own JSON
read after asserting its sha256 equals the history golden's `file_sha256`.

Exit 0 when every selected check passes, 1 when any fails, 2 on a usage or input error (a pin mismatch is one).
A check whose unit has not landed is a stub that FAILs, naming the unit that makes it live.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml"
HISTORY = ROOT / "Docs/demo-sprint/product-direction-layer4/history.json"
HISTORY_GOLDEN = ROOT / "simulator/tests/world/golden/history_v1.json"

#: The checker's own reading of the manifest's verticals as product Site types (spec §1 cast table).
SITE_TYPE = {"MINI_GRID": "MINIGRID", "COLD_CHAIN": "COLDCHAIN", "EV_DEPOT": "EV_CHARGING"}

#: Stubs: each check's question and the unit that makes it live (spec §8.1 "Live from").
STUBS = {
    "C-DD2": "DD2.5", "C-DD3": "DD2.5", "C-DD4": "DD2.5", "C-DD5": "DD4.4", "C-DD6": "DD4.4", "C-DD7": "DD4.4",
    "C-DD8": "DD3.3", "C-DD9": "DD6.1", "C-DD10": "DD6.1", "C-DD11": "DD3.1", "C-DD12": "DD3.1",
    "C-DD14": "DD5.2", "C-DD15": "DD6.1", "C-DD16": "DD3.2", "C-DD17": "DD3.3", "C-DD18": "DD6.1",
    "C-DD19": "DD3.3", "C-DD20": "DD4.4",
}
ORDER = tuple(f"C-DD{i}" for i in range(1, 21))


class InputError(Exception):
    """A checker input is missing or does not match its pin; no check is judged."""


@dataclass
class Result:
    check: str
    passed: bool
    detail: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Inputs:
    manifest: dict
    history: dict
    database_url: str


def read_inputs(database_url: str, manifest: Path = MANIFEST, history: Path = HISTORY,
                golden: Path = HISTORY_GOLDEN) -> Inputs:
    pinned = json.loads(golden.read_text(encoding="utf-8"))["file_sha256"]
    raw = history.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != pinned:
        raise InputError(f"history.json sha256 {actual} is not the golden's {pinned}")
    with manifest.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)
    return Inputs(manifest=doc, history=json.loads(raw), database_url=database_url)


# --- manifest reads (the checker's own) -------------------------------------------------------------------------------

def expected_cast(manifest: dict) -> tuple[dict[str, set[tuple[str, str]]], dict[str, dict[str, str]]]:
    """Per tenant slug: {(site code, product type)}; and per tenant: Site display name -> code."""
    sites: dict[str, set[tuple[str, str]]] = {}
    names: dict[str, dict[str, str]] = {}
    for tenant in manifest["tenants"]:
        slug, kind = tenant["tenant"], SITE_TYPE.get(tenant["vertical"], f"?{tenant['vertical']}")
        sites[slug] = {(s["code"], kind) for s in tenant["sites"]}
        names[slug] = {s["site"]: s["code"] for s in tenant["sites"]}
    return sites, names


def expected_triples(manifest: dict, names: dict[str, dict[str, str]]) -> dict[str, set[tuple[str, str, str]]]:
    """Per tenant slug: demo_workflow's (person, role, Site code or "") triples."""
    out: dict[str, set[tuple[str, str, str]]] = {}
    for tenant in manifest["demo_workflow"]["tenants"]:
        slug = tenant["tenant"]
        out[slug] = {(p["name"], p["role"], names[slug][p["site"]] if "site" in p else "") for p in tenant["people"]}
    return out


# --- clone reads (SQL) ------------------------------------------------------------------------------------------------

def stored_cast(database_url: str) -> tuple[dict[str, set[tuple[str, str]]], dict[str, set[tuple[str, str, str]]]]:
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url)
    try:
        with engine.connect() as c:
            tenants = {r.slug: set() for r in c.execute(text("SELECT slug FROM tenant"))}
            for r in c.execute(text("SELECT t.slug, s.site_code, s.site_type FROM site s "
                                    "JOIN tenant t ON t.id = s.tenant_id")):
                tenants.setdefault(r.slug, set()).add((r.site_code, r.site_type))
            triples: dict[str, set[tuple[str, str, str]]] = {slug: set() for slug in tenants}
            rows = c.execute(text(
                "SELECT t.slug, a.display_name, g.role, coalesce(s.site_code, '') AS site_code "
                "FROM role_grant g JOIN tenant t ON t.id = g.tenant_id "
                "JOIN operator_account a ON a.id = g.person_id LEFT JOIN site s ON s.id = g.site_id "
                "WHERE g.action = 'GRANTED' AND NOT EXISTS "
                "(SELECT 1 FROM role_grant r WHERE r.grant_id = g.id AND r.action = 'REMOVED')"))
            for r in rows:
                triples.setdefault(r.slug, set()).add((r.display_name, r.role, r.site_code))
    finally:
        engine.dispose()
    return tenants, triples


# --- the checks ---------------------------------------------------------------------------------------------------------

def judge_cast(manifest: dict, stored_sites: dict[str, set[tuple[str, str]]],
               stored_triples: dict[str, set[tuple[str, str, str]]]) -> Result:
    """C-DD1: exactly the three tenants, nine Sites (codes, product types) and demo_workflow's triples."""
    sites, names = expected_cast(manifest)
    triples = expected_triples(manifest, names)
    detail: list[str] = []
    if set(stored_sites) != set(sites):
        detail.append(f"tenants {sorted(stored_sites)} != expected {sorted(sites)}")
    for slug in sorted(sites):
        got = stored_sites.get(slug, set())
        if got != sites[slug]:
            detail.append(f"{slug} Sites: missing {sorted(sites[slug] - got)}, extra {sorted(got - sites[slug])}")
        have = stored_triples.get(slug, set())
        if have != triples[slug]:
            detail.append(f"{slug} people: missing {sorted(triples[slug] - have)}, extra {sorted(have - triples[slug])}")
    return Result("C-DD1", not detail, detail)


def check_cast(inputs: Inputs) -> Result:
    stored_sites, stored_triples = stored_cast(inputs.database_url)
    return judge_cast(inputs.manifest, stored_sites, stored_triples)


def _client_for(database_url: str, slug: str):
    """The product app served as `slug`, in process (no port)."""
    from starlette.testclient import TestClient

    os.environ["DATABASE_URL"] = database_url
    os.environ["ASSETOPS_TENANT_SLUG"] = slug
    from assetops_backend.main import create_app

    return TestClient(create_app())


def check_tenant_isolation(inputs: Inputs, client_for: Callable[[str, str], object] = _client_for) -> Result:
    """C-DD13: no tenant reads another's Sites through the product's reads; TENANT-1's refusal is DD5.2's."""
    sites, _ = expected_cast(inputs.manifest)
    detail: list[str] = []
    saved = {k: os.environ.get(k) for k in ("DATABASE_URL", "ASSETOPS_TENANT_SLUG")}
    try:
        for slug in sorted(sites):
            own = {code for code, _ in sites[slug]}
            others = sorted(code for other, rows in sites.items() if other != slug for code, _ in rows)
            client = client_for(inputs.database_url, slug)
            listed = client.get("/api/sites")
            if listed.status_code != 200:
                detail.append(f"{slug}: GET /api/sites returned {listed.status_code}")
            else:
                body = listed.json()
                items = body.get("sites", body) if isinstance(body, dict) else body
                codes = {item.get("site_id") for item in items}
                if codes != own:
                    detail.append(f"{slug}: /api/sites lists {sorted(codes)}, not its own {sorted(own)}")
            for code in others:
                status = client.get(f"/api/sites/{code}").status_code
                if status != 404:
                    detail.append(f"{slug}: GET /api/sites/{code} (another tenant's) returned {status}, not 404")
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    return Result("C-DD13", not detail, detail, pending=["TENANT-1 refused and counted: planted by DD5.2"])


def stub(check: str) -> Result:
    return Result(check, False, [f"not live: its unit {STUBS[check]} has not landed"])


LIVE: dict[str, Callable[[Inputs], Result]] = {"C-DD1": check_cast, "C-DD13": check_tenant_isolation}


def run(inputs: Inputs, only: tuple[str, ...] = ORDER) -> list[Result]:
    results = []
    for check in only:
        if check in LIVE:
            try:
                results.append(LIVE[check](inputs))
            except Exception as error:  # noqa: BLE001 - an unreadable store is a FAIL with its detail
                results.append(Result(check, False, [f"could not be judged: {type(error).__name__}: {error}"]))
        else:
            results.append(stub(check))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--only", default=",".join(ORDER))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    only = tuple(c.strip() for c in args.only.split(",") if c.strip())
    unknown = sorted(set(only) - set(ORDER))
    if unknown or not args.database_url:
        print(f"DD_CHECK_USAGE unknown checks {unknown}" if unknown else "DD_CHECK_USAGE --database-url is required",
              file=sys.stderr)
        return 2
    try:
        inputs = read_inputs(args.database_url)
    except (InputError, OSError, KeyError, ValueError) as error:
        print(f"DD_CHECK_INPUT {error}", file=sys.stderr)
        return 2
    results = run(inputs, only)
    if args.json:
        print(json.dumps([r.__dict__ for r in results], indent=1))
    else:
        for r in results:
            print(f"{r.check} {'PASS' if r.passed else 'FAIL'}")
            for line in r.detail:
                print(f"  {line}")
            for line in r.pending:
                print(f"  pending: {line}")
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
