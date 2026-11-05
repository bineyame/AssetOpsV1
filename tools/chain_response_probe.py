"""CH-5c L3: the stored-route checks on a settled clone. Report only.

    python tools/chain_response_probe.py --database-url <clone url> --work <work dir with keys.json> <command>

Commands:
- `prebuild`: the tick's pre-build (`chain/prebuild.run`) through the served app (`lab_app`), with its seconds.
- `fresh`: stored equals fresh (Q4) for every pre-built request: the stored bytes against a store-less compose in
  the same process, after replacing only the `known_at` and `selection_token` values that differ (their paths are
  printed). Any other difference fails.
- `watermarks`: every pre-built request's watermark (tenant-wide for estate routes, the board's own Site), as JSON;
  `--compare <file>` reports any that moved (the R5-2 idle-tick test).
- `wmtime`: the watermark statement's median ms over 20 runs, tenant-wide and per Site (the 50 ms stop).
- `sweep`: the CH5c-R7 C4 completeness sweep (`sweep` below) at each `--t0` (default: now + 1 min), at most
  `--limit` composed candidates per path, `--only` filtering the paths by substring. It writes store rows.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

TOOLS = Path(__file__).resolve().parent
WALL = ("known_at", "selection_token")


def _client(url: str, work: Path, store: bool):
    os.environ["ASSETOPS_RESPONSE_STORE"] = "on" if store else "off"
    sys.path.insert(0, str(TOOLS))
    from demo_combined_finish import app_client

    return app_client(url, work)


def _mask(a, b, path="", out=None):
    """`b` with each differing WALL value replaced by `a`'s; `out` collects the replaced paths."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        res = {}
        for k, v in b.items():
            if k in WALL and k in a and a[k] != v and not isinstance(v, (dict, list)):
                out.append(f"{path}.{k}")
                res[k] = a[k]
            else:
                res[k] = _mask(a.get(k), v, f"{path}.{k}", out) if k in a else v
        return res
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [_mask(x, y, f"{path}[{i}]", out) for i, (x, y) in enumerate(zip(a, b))]
    return b


def fresh(url: str, work: Path) -> int:
    from assetops_backend.chain import prebuild
    from assetops_backend.chain.response_store import HEADER

    from assetops_backend.chain.composition import prebuilt_requests
    from chain_watermark_guard import chain_paths

    stored_c = _client(url, work, True)
    stored = {p: stored_c.get(p) for p in prebuild.paths()}
    # CH-5b2: the chain and "Why?" routes are not pre-built; the first GET stores, the second is the served hit.
    for p in chain_paths(stored_c, prebuilt_requests()):
        stored_c.get(p)
        stored[p] = stored_c.get(p)
    os.environ["ASSETOPS_RESPONSE_STORE"] = "off"
    from lab_app import build_app
    from fastapi.testclient import TestClient

    fresh_c = TestClient(build_app())
    bad = 0
    for p, s in stored.items():
        f = fresh_c.get(p)
        masked: list[str] = []
        same = s.status_code == f.status_code == 200 and (
            s.content == f.content or _mask(s.json(), f.json(), "", masked) == s.json())
        bad += not same
        print(f"{'ok  ' if same else 'DIFF'} {s.headers.get(HEADER)} {len(s.content):>7}B masked={masked} {p}")
    print(f"fresh: {len(stored) - bad}/{len(stored)} stored bodies equal a fresh compose")
    return 1 if bad else 0


def _requests(url: str):
    """(path, tenant, watermark Sites) per pre-built request, as the routes choose them."""
    from sqlalchemy import create_engine, text

    from assetops_backend.chain import prebuild

    engine = create_engine(url)
    with engine.connect() as c:
        sites = {r.site_code: (r.tenant_id, r.id) for r in c.execute(text("SELECT tenant_id, id, site_code FROM site"))}
    engine.dispose()
    tenant = next(iter({t for t, _ in sites.values()}))
    out = []
    for p in prebuild.paths():
        parts = urlsplit(p).path.split("/")
        if parts[2] == "sites":
            t, s = sites[parts[3]]
            out.append((p, t, (s,)))
        else:
            out.append((p, tenant, None))
    return out


def watermarks(url: str) -> dict[str, str]:
    from sqlalchemy import create_engine

    from assetops_backend.chain.composition import read_watermark

    engine = create_engine(url)
    out = {}
    for p, t, s in _requests(url):
        with engine.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            out[p] = read_watermark(c, t, s)
    engine.dispose()
    return out


def wmtime(url: str) -> None:
    from sqlalchemy import create_engine

    from assetops_backend.chain.composition import read_watermark

    engine = create_engine(url)
    seen = {}
    for _, t, s in _requests(url):
        seen.setdefault("tenant" if s is None else str(s[0]), (t, s))
    for label, (t, s) in seen.items():
        ms = []
        for _ in range(20):
            with engine.connect() as c:
                t0 = time.perf_counter()
                read_watermark(c, t, s)
                ms.append((time.perf_counter() - t0) * 1000)
        print(f"wmtime {label}: median {statistics.median(ms):.2f} ms max {max(ms):.2f} ms")
    engine.dispose()


#: CH5c-R7 C4: the sweep's horizon and the candidate offset (each seeded instant +-1 us).
HORIZON = timedelta(days=40)
MICRO = timedelta(microseconds=1)


def seeded_instants(url: str, lo: datetime, hi: datetime) -> set[datetime]:
    """C4: every `timestamptz` value in the change-logged input tables (the `<table>_cic_ins` triggers) in
    [lo, hi]. jsonb-embedded times are not read (named residual)."""
    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    out: set[datetime] = set()
    try:
        with engine.connect() as c:
            tables = [r[0] for r in c.execute(text(
                "SELECT DISTINCT c.relname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid "
                "WHERE t.tgname LIKE '%\\_cic\\_ins' ORDER BY 1"))]
            for table in tables:
                cols = [r[0] for r in c.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_schema = current_schema() "
                    "AND table_name = :t AND data_type = 'timestamp with time zone'"), {"t": table})]
                for col in cols:
                    out.update(r[0] for r in c.execute(text(
                        f'SELECT DISTINCT "{col}" FROM "{table}" WHERE "{col}" BETWEEN :lo AND :hi'),
                        {"lo": lo, "hi": hi}))
    finally:
        engine.dispose()
    return out


def candidates(seeded: set[datetime], t0: datetime, zones: list[str], lookback: timedelta) -> list[datetime]:
    """C4: each seeded instant and the same plus the lookback, each +-1 us, and each local midnight, in
    (t0, t0 + HORIZON], sorted."""
    from zoneinfo import ZoneInfo

    out: set[datetime] = set()
    for v in seeded:
        for base in (v, v + lookback):
            out.update((base - MICRO, base, base + MICRO))
    for zone in zones or ["UTC"]:
        z = ZoneInfo(zone)
        local = t0.astimezone(z)
        for d in range(HORIZON.days + 1):
            out.add(datetime.combine(local.date() + timedelta(days=d + 1), datetime.min.time(), tzinfo=z))
    return sorted(t for t in out if t0 < t <= t0 + HORIZON)


def sweep(on: Any, composed: Any, paths: list[str], until_of: Any, t0: datetime, cands: list[datetime],
          limit: int | None = None) -> dict[str, Any]:
    """CH5c-R7 C4: compose every path at `t0` through `on` (store on; `until_of(etag)` is that row's
    `valid_until`) and through the compose-only client `composed` at `t0` and at each candidate `t`, with
    `read_scope.clock` and `read_scope.read_instant` moved to the instant. Records a violation when a body
    (Q4-masked) differs from the `t0` body at a `t` before `valid_until(t0)`. A candidate at or after
    `valid_until(t0)` satisfies the claim whatever its body, so only earlier candidates are composed (`limit`
    caps them per path, earliest first)."""
    from assetops_backend import read_scope
    from assetops_backend.chain.response_store import HEADER

    at = [t0]
    real_clock, real_instant = read_scope.clock, read_scope.read_instant
    read_scope.clock = lambda: at[0]
    read_scope.read_instant = lambda db_value: at[0]
    report: dict[str, Any] = {"t0": t0.isoformat(), "candidates": len(cands), "paths": {}, "violations": []}
    try:
        for path in paths:
            first = on.get(path)
            tag = first.headers.get("etag")
            assert first.status_code == 200 and tag, (path, first.status_code, first.headers.get(HEADER))
            until = until_of(tag.strip('"'))
            base = composed.get(path)
            assert base.status_code == 200, (path, base.status_code)
            base_body = base.json()
            assert _mask(first.json(), base_body) == first.json(), f"{path}: the stored body != a compose at t0"
            todo = [t for t in cands if until is None or t < until]
            todo = todo if limit is None else todo[:limit]
            differed = []
            for t in todo:
                at[0] = t
                try:
                    body = composed.get(path)
                finally:
                    at[0] = t0
                if body.status_code != 200 or _mask(base_body, body.json()) != base_body:
                    differed.append(t.isoformat())
                    report["violations"].append({"path": path, "t": t.isoformat(),
                                                 "valid_until": None if until is None else until.isoformat()})
            report["paths"][path] = {"state": first.headers.get(HEADER),
                                     "valid_until": None if until is None else until.isoformat(),
                                     "composed": len(todo), "differed": differed}
    finally:
        read_scope.clock, read_scope.read_instant = real_clock, real_instant
    return report


def sweep_clone(url: str, work: Path, t0s: list[datetime], limit: int | None, only: str | None) -> int:
    """C4 on a clone (L3): the sweep over the pre-built requests at each `t0`, on the served app (`lab_app`)."""
    from sqlalchemy import create_engine, text

    from assetops_backend.chain import prebuild
    from assetops_backend.estate.coverage import VERIFIED_LOOKBACK

    on = _client(url, work, True)
    os.environ["ASSETOPS_RESPONSE_STORE"] = "compose"
    from fastapi.testclient import TestClient
    from lab_app import build_app

    composed = TestClient(build_app())
    engine = create_engine(url)

    def until_of(tag: str) -> Any:
        with engine.connect() as c:
            return c.execute(text("SELECT valid_until FROM chain_response WHERE etag = :e"), {"e": tag}).scalar_one()

    with engine.connect() as c:
        zones = sorted({r[0] for r in c.execute(text("SELECT DISTINCT timezone FROM site"))})
    paths = [p for p in prebuild.paths() if only is None or only in p]
    bad = 0
    try:
        for t0 in t0s:
            seeded = seeded_instants(url, t0 - VERIFIED_LOOKBACK - HORIZON, t0 + HORIZON)
            cands = candidates(seeded, t0, zones, VERIFIED_LOOKBACK)
            report = sweep(on, composed, paths, until_of, t0, cands, limit)
            bad += len(report["violations"])
            print(json.dumps({"t0": report["t0"], "paths": len(paths), "seeded": len(seeded),
                              "candidates": len(cands),
                              "composed": sum(v["composed"] for v in report["paths"].values()),
                              "states": sorted({v["state"] for v in report["paths"].values()}),
                              "valid_until": sorted({v["valid_until"] or "-" for v in report["paths"].values()}),
                              "violations": report["violations"]}))
    finally:
        engine.dispose()
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python tools/chain_response_probe.py")
    p.add_argument("--database-url", required=True)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("command", choices=("prebuild", "fresh", "watermarks", "wmtime", "sweep"))
    p.add_argument("--out", type=Path)
    p.add_argument("--compare", type=Path)
    p.add_argument("--t0", action="append", default=[], help="sweep: an ISO instant (repeatable)")
    p.add_argument("--limit", type=int)
    p.add_argument("--only")
    a = p.parse_args(argv)
    if a.command == "sweep":
        t0s = [datetime.fromisoformat(t) for t in a.t0] or [datetime.now(timezone.utc) + timedelta(minutes=1)]
        return sweep_clone(a.database_url, a.work, t0s, a.limit, a.only)
    if a.command == "prebuild":
        from assetops_backend.chain import prebuild

        client = _client(a.database_url, a.work, True)
        print(json.dumps(prebuild.run(a.database_url, client)))
        return 0
    if a.command == "fresh":
        return fresh(a.database_url, a.work)
    if a.command == "wmtime":
        wmtime(a.database_url)
        return 0
    now = watermarks(a.database_url)
    if a.out:
        a.out.write_text(json.dumps(now, indent=1), encoding="utf-8")
    if a.compare:
        before = json.loads(a.compare.read_text(encoding="utf-8"))
        moved = {k: (before.get(k), v) for k, v in now.items() if before.get(k) != v}
        print(json.dumps({"requests": len(now), "moved": moved}, indent=1))
        return 1 if moved else 0
    print(json.dumps(now, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
