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
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
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

    stored_c = _client(url, work, True)
    stored = {p: stored_c.get(p) for p in prebuild.paths()}
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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python tools/chain_response_probe.py")
    p.add_argument("--database-url", required=True)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("command", choices=("prebuild", "fresh", "watermarks", "wmtime"))
    p.add_argument("--out", type=Path)
    p.add_argument("--compare", type=Path)
    a = p.parse_args(argv)
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
