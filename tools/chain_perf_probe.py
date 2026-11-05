"""CH-5a1 §A7: the chain read-path performance probe. Report only, no pass/fail (CH-5b turns it into perf_budget.py).

    python tools/chain_perf_probe.py --database-url <clone url> --work <work dir with keys.json> [--runs 5]
                                     [--profile] [--outbox]

In process, through a TestClient over `lab_app` (`demo_combined_finish.app_client`), on a settled clone; no serve,
no tick. Cold is the first request in a fresh process (QW-1 packet: "Cold is the first request in a fresh process";
one child process per cold run). Warm is `--runs` repeats in one process after one discarded request. Per URL it
prints the median, min and max (ms), the body size in bytes, and the top 10 read-scope ledger names by ms
(`read_scope.scope` is wrapped to keep the request's `ReadScope`; no production endpoint), with `chain.money_head` on
its own line. `--profile` (R3/P1): cProfile of one warm Portfolio (story week), top 20 by cumulative time under
`select_evidence_scope` and `select_financial_scope`. `--outbox` (P8 stub): outbox and consumption row counts and the
R8 statement's ms per Site; the full P8 runs on L3m.
"""
from __future__ import annotations

import argparse
import contextlib
import cProfile
import io
import json
import pstats
import statistics
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
WEEK = "from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z"
URLS = {
    "kobo_board_31oct": "/api/sites/KOBO-001/outcome-board?date=2026-10-31",
    "cold_board_failure_night": "/api/sites/COLD-LAB-001/outcome-board?from=2026-10-31T16:00:00Z&to=2026-10-31T17:05:00Z",
    "ev_board_27oct": "/api/sites/EV-LAB-001/outcome-board?from=2026-10-27T08:00:00Z&to=2026-10-27T09:00:00Z",
    "summary_week": f"/api/estate/outcome-summary?{WEEK}",
    "portfolio_week": f"/api/estate/portfolio?{WEEK}",
    # CH-5c P1 (CH-5a2b residual): the Findings index now runs the full claims read per Site
    "findings_week": f"/api/estate/findings?{WEEK}&lens=all&state=all",
}


def client(url: str, work: Path):
    sys.path.insert(0, str(TOOLS))
    from demo_combined_finish import app_client

    return app_client(url, work)


def capture_scopes() -> list:
    """Wrap `read_scope.scope` (perf.route looks it up as a module attribute) and keep each request's ReadScope."""
    from assetops_backend import read_scope

    kept: list = []
    inner = read_scope.scope

    @contextlib.contextmanager
    def scope(route: str):
        with inner(route) as sc:
            kept.append(sc)
            yield sc

    read_scope.scope = scope
    return kept


def one(c, kept: list, path: str) -> dict:
    kept.clear()
    t0 = time.perf_counter()
    r = c.get(path)
    ms = (time.perf_counter() - t0) * 1000
    sc = kept[-1] if kept else None
    return {"status": r.status_code, "ms": round(ms, 1), "bytes": len(r.content),
            "top": [] if sc is None else [(n, round(v, 1)) for n, v in sc.top_ms(10)],
            "money_head": None if sc is None else round(sc.ms.get("chain.money_head", 0.0), 1),
            "max_per_key": None if sc is None else sc.max_per_key()}


def child(args) -> int:
    kept = capture_scopes()
    c = client(args.database_url, args.work)
    print("RESULT " + json.dumps(one(c, kept, URLS[args.one])))
    return 0


def stats(ms: list[float]) -> str:
    return f"median {statistics.median(ms):>8.0f}  min {min(ms):>8.0f}  max {max(ms):>8.0f}"


def profile(c, kept: list) -> None:
    from assetops_backend.estate import portfolio

    profs = {"select_evidence_scope": cProfile.Profile(), "select_financial_scope": cProfile.Profile()}
    orig = {n: getattr(portfolio, n) for n in profs}

    def wrap(name):
        def run(*a, **k):
            return profs[name].runcall(orig[name], *a, **k)
        return run

    for n in profs:
        setattr(portfolio, n, wrap(n))
    try:
        res = one(c, kept, URLS["portfolio_week"])
    finally:
        for n, f in orig.items():
            setattr(portfolio, n, f)
    print(f"\n== P1 profile: one warm GET {URLS['portfolio_week']} ({res['ms']} ms, status {res['status']})")
    for n, p in profs.items():
        buf = io.StringIO()
        pstats.Stats(p, stream=buf).sort_stats("cumulative").print_stats(20)
        lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
        start = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("ncalls")), 0)
        print(f"-- {n}: top 20 by cumulative")
        for ln in lines[start:start + 21]:
            print("   " + ln[:200])


def outbox(url: str) -> None:
    from sqlalchemy import create_engine, text

    from assetops_backend.chain.adapters.postgres_chain_read import PostgresChainRead

    eng = create_engine(url)
    with eng.connect() as conn:
        n_out = conn.execute(text("SELECT count(*) FROM event_outbox")).scalar()
        n_con = conn.execute(text("SELECT count(*) FROM event_consumption")).scalar()
        sites = conn.execute(text("SELECT tenant_id, id, site_code FROM site ORDER BY site_code")).all()
    eng.dispose()
    print(f"\n== P8 stub: event_outbox {n_out} rows, event_consumption {n_con} rows")
    port = PostgresChainRead(url)
    try:
        for t, s, code in sites:
            port.findings_settled(t, s, None)  # warm the connection
            t0 = time.perf_counter()
            settled = port.findings_settled(t, s, None)
            print(f"   R8 {code}: settled={settled} {(time.perf_counter() - t0) * 1000:.1f} ms")
    finally:
        port.dispose()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python tools/chain_perf_probe.py")
    p.add_argument("--database-url", required=True)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--runs", type=int, default=5)
    p.add_argument("--only", nargs="*", choices=sorted(URLS), help="limit to these URL keys")
    p.add_argument("--profile", action="store_true")
    p.add_argument("--outbox", action="store_true")
    p.add_argument("--no-cold", action="store_true")
    p.add_argument("--one", choices=sorted(URLS), help=argparse.SUPPRESS)  # internal: one cold child
    args = p.parse_args(argv)
    if args.one:
        return child(args)
    keys = args.only or list(URLS)
    cold: dict[str, list[dict]] = {k: [] for k in keys}
    if not args.no_cold:
        for k in keys:
            for _ in range(args.runs):
                out = subprocess.run([sys.executable, __file__, "--database-url", args.database_url, "--work",
                                      str(args.work), "--one", k], capture_output=True, text=True)
                line = next((ln for ln in out.stdout.splitlines() if ln.startswith("RESULT ")), None)
                if line is None:
                    print(f"cold {k}: child failed rc={out.returncode}: {out.stderr[-400:]}")
                    continue
                cold[k].append(json.loads(line[7:]))
    kept = capture_scopes()
    c = client(args.database_url, args.work)
    warm: dict[str, list[dict]] = {}
    for k in keys:
        one(c, kept, URLS[k])  # discarded
        warm[k] = [one(c, kept, URLS[k]) for _ in range(args.runs)]
    for k in keys:
        w = warm[k]
        print(f"\n== {k}  {URLS[k]}")
        if cold[k]:
            print(f"   cold ({len(cold[k])}): {stats([r['ms'] for r in cold[k]])}")
        print(f"   warm ({len(w)}): {stats([r['ms'] for r in w])}")
        print(f"   status {sorted({r['status'] for r in w})}  bytes {w[-1]['bytes']}  max_per_key {w[-1]['max_per_key']}")
        print(f"   money_head {w[-1]['money_head']} ms")
        print("   top ledger (last warm run): " + ", ".join(f"{n} {v}" for n, v in w[-1]["top"]))
    if args.profile:
        profile(c, kept)
    if args.outbox:
        outbox(args.database_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
