"""S4-04 phase 2: the repeatable owner walkthrough for the Site Finding index (tasks/S4-04-site-finding-index.md,
"Reproducible owner walkthrough").

It composes the existing Finding-case producer (`tools/s4_finding_cases.py`, labelled authenticated fixture
batches over TLS, the S3 worker and the S4 matcher) in ONE private database and work directory, and adds:

- an independent **assessed empty** day (2026-10-25): a delivered non-candidate block, assessed and matched, so
  the index reads CURRENT with zero rows and a complete S3/S4 watermark;
- the **positive** day (2026-10-15, the F06 day; the wider 2026-10-01..2026-10-23 window covers F01-F08), whose
  canonical Findings and exact revisions drive order, cursor pages and the S5-01 card parity;
- a **dirty/stale** day (2026-10-27): assessed and matched, then late evidence is delivered and not assessed;
- a **failed** day (2026-10-28): the scoped failing-job pattern of `tools/s5_overview_walkthrough.py`;
- an **unassessed** day (2026-10-30): nothing is delivered for it.

Commands (database `assetops_s404_owner*` and work directory `var/s404_owner*` only; API 8934, web 5434):

    prepare        build the tree and database, seed every fixture, run the Performance comparison (source gate),
                   and verify every window through the index read; writes <work>/s404-manifest.json; exits 1 when
                   the assessed-empty completeness or any expected status cannot be proved
    serve          serve the API on 8934 (foreground) and print the frontend command and owner URLs; installs no
                   schedule
    late           deliver a late Candidate block on the positive day (2026-10-15 16:00-16:40), not assessed
    settle         tick S3 assessment (`assess_dispatch process-jobs`) and S4 matching (`match-findings`) to
                   completion, then re-run the Performance comparison
    gate --close | gate --open   move the Performance comparison reports aside / back (the source gate)
    drop           drop the database and remove the work directory

Run from the repository root with the repository venv (`.venv`). `var/sites/kobo-001.yaml` must exist.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s2_demo_walkthrough as s2  # noqa: E402
import s4_finding_cases as s4  # noqa: E402

SITE = "KOBO-001"
DOMAIN = "mini-grid-dispatch"
DB_PREFIX = "assetops_s404_owner"
WORK_PREFIX = "s404_owner"
MANIFEST = "s404-manifest.json"
GATE_DIR = Path("var") / "evidence" / "migration-performance"
DAYS = {"positive": "2026-10-15", "empty": "2026-10-25", "dirty": "2026-10-27", "failed": "2026-10-28",
        "unassessed": "2026-10-30"}
WIDE = ("2026-10-01T00:00:00Z", "2026-10-24T00:00:00Z")
CANDIDATE = {"pv": "40", "dis": "20", "soc": "80", "stop_before": True, "stop_after": True}
NO_CANDIDATE = {"pv": "5", "dis": "5", "soc": "80", "stop_before": True, "stop_after": True}
LATE_BLOCK = ("2026-10-15T16:00:00Z", "2026-10-15T16:40:00Z")
say, step = s2.say, s2.step


def window(day: str) -> tuple[str, str]:
    from datetime import date, timedelta

    nxt = date.fromisoformat(day) + timedelta(days=1)
    return f"{day}T00:00:00Z", f"{nxt.isoformat()}T00:00:00Z"


def block(start: str, end: str, kind: dict[str, Any]) -> dict[str, Any]:
    return {"from": start, "to": end, **kind}


def fixture(case_id: str, day: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    return {"case_id": case_id, "label": f"S4-04 walkthrough {case_id}", "day": day, "steps": steps}


def index_url(api_port: int, frm: str, to: str, **extra: str) -> str:
    query = urllib.parse.urlencode({"domain": DOMAIN, "from": frm, "to": to, **extra})
    return f"http://127.0.0.1:{api_port}/api/sites/{SITE}/finding-index?{query}"


def get_json(url: str, timeout: float = 60) -> tuple[int, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8") or "null")


def summary(status: int, body: Any) -> dict[str, Any]:
    if status != 200:
        detail = (body or {}).get("detail") if isinstance(body, dict) else body
        return {"http": status, "code": detail.get("code") if isinstance(detail, dict) else None,
                "reason": detail.get("reason") if isinstance(detail, dict) else None}
    return {"http": 200, "status": body["status"], "total_count": body["total_count"],
            "rows": [[r["finding_id"], r["finding_revision_id"], r["episode"]["start"]] for r in body["rows"]],
            "next_cursor": bool(body["next_cursor"]), "selection_token": body["selection_token"],
            "days": body["discovery"]["days"], "reasons": body["status_reasons"][:6]}


class IndexWalk(s4.Cases):
    """The S4 Finding-case producer in a private database, plus the S4-04 index fixtures."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        self.out: dict[str, Any] = {"database": args.db, "days": DAYS, "wide_window": WIDE, "checks": []}

    def deliver_case(self, case_id: str, day: str, blocks: list[dict[str, Any]], *, assess: bool = True,
                     match: bool = True, decided: str = "2026-10-31T08:00:00Z") -> None:
        steps: list[dict[str, Any]] = [{"do": "deliver", "decided": decided, "blocks": blocks}]
        if assess:
            steps.append({"do": "assess"})
        if match:
            steps.append({"do": "match", "expect": [], "collateral": True})
        self.run_case(fixture(case_id, day, steps))

    def fixtures(self) -> None:
        for n, case in enumerate(self.spec["cases"], start=4):
            step(f"{n}. {case['case_id']} {case['label']} ({case['day']})")
            self.run_case(case)
        step(f"EMPTY {DAYS['empty']}: one non-candidate block, assessed and matched (assessed zero rows)")
        self.deliver_case("E1", DAYS["empty"], [block(f"{DAYS['empty']}T10:00:00Z", f"{DAYS['empty']}T10:30:00Z",
                                                      NO_CANDIDATE)])
        step(f"DIRTY {DAYS['dirty']}: assessed and matched, then late evidence left unassessed")
        self.deliver_case("D1", DAYS["dirty"], [block(f"{DAYS['dirty']}T10:00:00Z", f"{DAYS['dirty']}T10:30:00Z",
                                                      NO_CANDIDATE)])
        step(f"FAILED {DAYS['failed']}: delivered, then a scoped failing assessment (walkthrough-only model)")
        self.deliver_case("X1", DAYS["failed"], [block(f"{DAYS['failed']}T10:00:00Z",
                                                       f"{DAYS['failed']}T10:30:00Z", NO_CANDIDATE)],
                          assess=False, match=False)
        import s5_overview_walkthrough as s5

        done = self.py("-c", s5.FAIL_STAGE, self.db_url, DAYS["failed"], cwd=self.tree / "backend")
        say("  " + done.stdout.strip().splitlines()[-1])
        self.deliver_case("D2", DAYS["dirty"], [block(f"{DAYS['dirty']}T12:00:00Z", f"{DAYS['dirty']}T12:30:00Z",
                                                      NO_CANDIDATE)], assess=False, match=False,
                          decided="2026-11-01T08:00:00Z")
        say(f"UNASSESSED {DAYS['unassessed']}: nothing delivered")

    def run_all(self) -> None:
        self.setup()
        try:
            self.prepare()
            self.fixtures()
        finally:
            step("Stopping every process this script started")
            self.stop_all()


# --------------------------------------------------------------------------------------------- follow-ups

def tree_py(work: Path, db: str, *argv: str, check: bool = True) -> subprocess.CompletedProcess:
    import s402c_late_power_walkthrough as lr

    return lr.tree_py(work, db, *argv, check=check)


def comparison(work: Path, db: str) -> dict[str, Any]:
    live = work / "tree" / GATE_DIR
    if live.with_name(live.name + ".closed").exists():
        say("  Performance gate is closed (gate --close): the comparison is not re-run.")
        return {"open": False, "closed_by_walkthrough": True}
    done = tree_py(work, db, "-m", "assetops_backend.performance_migration", "run", "--tenant", "demo",
                   "--site", SITE, check=False)
    say(f"  Performance comparison (source gate): exit {done.returncode} -> "
        f"{'OPEN' if done.returncode == 0 else 'CLOSED'}")
    if done.returncode:
        say("  " + (done.stdout or done.stderr)[-600:].replace("\n", "\n  "))
    return {"open": done.returncode == 0, "exit": done.returncode}


def settle(work: Path, db: str) -> dict[str, Any]:
    """Tick S3 assessment and S4 matching to completion (no schedule is installed)."""
    out: dict[str, Any] = {"passes": []}
    ident = json.loads((work / MANIFEST).read_text(encoding="utf-8"))["identity"]
    for n in range(1, 6):
        jobs = json.loads(tree_py(work, db, *s4.ASSESS, "process-jobs").stdout.strip().splitlines()[-1])
        match = json.loads(tree_py(work, db, *s4.ASSESS, "match-findings", "--tenant-id", ident["tenant_id"],
                                   "--site-id", ident["site_id"]).stdout.strip().splitlines()[-1])
        out["passes"].append({"jobs": [j.get("status") for j in jobs], "planned": match.get("planned"),
                              "new_findings": match.get("finding_ids"), "new_revisions": match.get("revision_ids")})
        say(f"  settle pass {n}: {len(jobs)} job(s) {[j.get('status') for j in jobs]}, matcher planned "
            f"{match.get('planned')}, new Findings {len(match.get('finding_ids') or [])}, new revisions "
            f"{len(match.get('revision_ids') or [])}")
        if not jobs and not match.get("planned"):
            break
    out["gate"] = comparison(work, db)
    return out


def late(work: Path, db: str, args: argparse.Namespace) -> None:
    """Deliver one late Candidate block on the positive day through the producer's TLS path (not assessed)."""
    walk = IndexWalk(args)
    walk.identity = json.loads((work / MANIFEST).read_text(encoding="utf-8"))["identity"]
    walk.start_tls()
    try:
        walk.doc = json.loads(bytes(walk.pg(
            "SELECT r.snapshot_canonical FROM signal_binding_set_revision r WHERE r.id = %s",
            walk.identity["binding_set_revision_id"])[0][0]))
        walk.snapshot_sha = walk.identity["snapshot_sha256"]
        [(walk.gateway_external_id,)] = walk.pg("SELECT g.gateway_external_id FROM gateway g JOIN site s ON "
                                                "s.id = g.site_id WHERE s.site_code = %s", SITE)
        walk.credential = Path(json.loads((work / MANIFEST).read_text(encoding="utf-8"))["credential"])
        walk.seq = {tuple(k.split("|")): v for k, v in
                    json.loads((work / MANIFEST).read_text(encoding="utf-8")).get("sequences", {}).items()}
        walk.deliver_case("L1", DAYS["positive"], [block(*LATE_BLOCK, CANDIDATE)], assess=False, match=False,
                          decided="2026-11-02T08:00:00Z")
        save_sequences(work, walk)
    finally:
        walk.stop_all()
    say("Late evidence delivered and NOT assessed: the positive window now reads not current. Reload the old "
        "page-2 address (it must restart), then run `settle`.")


def save_sequences(work: Path, walk: IndexWalk) -> None:
    manifest = json.loads((work / MANIFEST).read_text(encoding="utf-8"))
    manifest["sequences"] = {"|".join(k): v for k, v in walk.seq.items()}
    (work / MANIFEST).write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")


def gate(work: Path, close: bool) -> None:
    live = work / "tree" / GATE_DIR
    aside = live.with_name(live.name + ".closed")
    src, dst = (live, aside) if close else (aside, live)
    if not src.exists():
        raise SystemExit(f"Nothing to move: {src} does not exist")
    if dst.exists():
        raise SystemExit(f"Refused: {dst} already exists")
    src.rename(dst)
    say(f"{'Closed' if close else 'Reopened'}: moved {src} -> {dst}. "
        + ("Unpinned index reads now return 409 PERFORMANCE_CUTOVER_CLOSED; exact revision links stay audit-only."
           if close else "Run `settle` to tick any reopened S3/S4 work, then reload."))


def start_api(work: Path, db: str, port: int) -> subprocess.Popen:
    import s402c_late_power_walkthrough as lr

    log = work / "logs" / f"api-{port}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen([str(s2.PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port", str(port)],
                            cwd=work / "tree" / "host", env=lr.tree_env(work, db), stdout=log.open("w"),
                            stderr=subprocess.STDOUT)


def wait_api(port: int, proc: subprocess.Popen) -> None:
    for _ in range(120):
        if proc.poll() is not None:
            raise SystemExit(f"API exited ({proc.returncode}); see the log")
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/sites", timeout=5)
            return
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    raise SystemExit("API did not start in 120 s")


def verify(work: Path, db: str, port: int) -> list[str]:
    """Read every window through the served index and check the expected states; write the manifest."""
    proc = start_api(work, db, port)
    failures: list[str] = []
    try:
        wait_api(port, proc)
        manifest = json.loads((work / MANIFEST).read_text(encoding="utf-8"))
        reads: dict[str, Any] = {}
        expect = {"empty": "CURRENT", "positive": "CURRENT", "dirty": "STALE_PROJECTION", "failed": "FAILED",
                  "unassessed": "UNASSESSED"}
        for name, day in DAYS.items():
            reads[name] = summary(*get_json(index_url(port, *window(day))))
            got = reads[name].get("status")
            if got != expect[name]:
                failures.append(f"{name} {day}: expected {expect[name]}, read {reads[name]}")
        if reads["empty"].get("total_count") != 0:
            failures.append(f"assessed empty day is not a CURRENT zero: {reads['empty']}")
        if len(reads["positive"].get("rows") or []) < 2:
            failures.append(f"positive day has fewer than two canonical Findings: {reads['positive']}")
        reads["wide"] = summary(*get_json(index_url(port, *WIDE)))
        status, page1 = get_json(index_url(port, *WIDE, limit="2"))
        reads["wide_page1"] = summary(status, page1)
        if status == 200 and page1.get("next_cursor"):
            reads["wide_page2"] = summary(*get_json(index_url(port, *WIDE, limit="2", cursor=page1["next_cursor"])))
            manifest["wide_page2_cursor"] = page1["next_cursor"]
        else:
            failures.append(f"wide window has no second page at limit 2: {reads['wide_page1']}")
        manifest["reads"] = reads
        manifest["failures"] = failures
        (work / MANIFEST).write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    finally:
        proc.terminate()
        proc.wait(timeout=30)
    return failures


def owner_urls(web: int) -> list[tuple[str, str]]:
    def page(frm: str, to: str, **extra: str) -> str:
        query = urllib.parse.urlencode({"from": frm, "to": to, "domain": DOMAIN, **extra})
        return f"http://localhost:{web}/sites/{SITE}/findings?{query}"

    urls = [(name, page(*window(day))) for name, day in DAYS.items()]
    urls.append(("wide (page size 2)", page(*WIDE, limit="2")))
    return urls


def args_work(args: argparse.Namespace) -> Path:
    path = Path(args.work)
    return (s2.REPO / path).resolve() if not path.is_absolute() else path.resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s404_finding_index_walkthrough.py")
    parser.add_argument("command", choices=("prepare", "serve", "late", "settle", "gate", "drop"))
    parser.add_argument("--db", default=DB_PREFIX)
    parser.add_argument("--work", default=f"var/{WORK_PREFIX}")
    parser.add_argument("--api-port", type=int, default=8934)
    parser.add_argument("--web-port", type=int, default=5434)
    parser.add_argument("--tls-port", type=int, default=8935)
    parser.add_argument("--http-port", type=int, default=8936)
    parser.add_argument("--cadence-seconds", type=int, default=60)
    parser.add_argument("--artifact", default=None)
    parser.add_argument("--close", action="store_true")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args(argv)
    work = args_work(args)
    var = (s2.REPO / "var").resolve()
    if not args.db.startswith(DB_PREFIX) or not args.db.replace("_", "").isalnum():
        raise SystemExit(f"Refused: --db must start with {DB_PREFIX}")
    if work.parent != var or not work.name.startswith(WORK_PREFIX):
        raise SystemExit(f"Refused: --work must be var/{WORK_PREFIX}*")
    args.work = str(work)
    s2.DEMO_DB = args.db  # read by Demo at construction; no other database is touched

    if args.command == "prepare":
        started = time.time()
        walk = IndexWalk(args)
        walk.run_all()
        manifest = {"site_code": SITE, "domain": DOMAIN, "database": args.db, "days": DAYS,
                    "windows": {name: window(day) for name, day in DAYS.items()} | {"wide": WIDE},
                    "identity": walk.identity, "credential": str(walk.credential),
                    "cases": walk.cases, "producer_failures": walk.failures}
        (work / MANIFEST).write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        save_sequences(work, walk)
        step("Performance comparison (source gate)")
        gate_state = comparison(work, args.db)
        step("Verify every window through the served index")
        failures = verify(work, args.db, args.api_port) + walk.failures
        if not gate_state.get("open"):
            failures.append("Performance comparison did not pass: every unpinned index read is closed")
        say(json.dumps(json.loads((work / MANIFEST).read_text(encoding="utf-8"))["reads"], indent=1)[:4000])
        say(f"Prepared in {time.time() - started:.0f} s; {len(failures)} failed check(s)"
            + ("" if not failures else ":\n  " + "\n  ".join(failures)))
        return 1 if failures else 0
    if args.command == "drop":
        import psycopg

        with psycopg.connect(IndexWalk(args).admin_url, autocommit=True) as conn:
            conn.execute(f"DROP DATABASE IF EXISTS {args.db} WITH (FORCE)")
        if work.exists():
            shutil.rmtree(work)
        say(f"Dropped {args.db} and removed {work}.")
        return 0
    if not (work / MANIFEST).exists():
        raise SystemExit(f"No {MANIFEST} in {work}: run prepare first.")
    if args.command == "gate":
        if args.close == args.open:
            raise SystemExit("gate needs exactly one of --close / --open")
        gate(work, args.close)
        return 0
    if args.command == "settle":
        out = settle(work, args.db)
        return 0 if out["gate"].get("open") or out["gate"].get("closed_by_walkthrough") else 1
    if args.command == "late":
        late(work, args.db, args)
        return 0
    # serve
    comparison(work, args.db)
    proc = start_api(work, args.db, args.api_port)
    say(f"API for {args.db}: python -m uvicorn lab_app:app --host 127.0.0.1 --port {args.api_port} "
        f"(log {work / 'logs' / f'api-{args.api_port}.log'})")
    say("Frontend, from frontend/:")
    say(f'  $env:ASSETOPS_API_PORT="{args.api_port}"; npm.cmd run dev -- --port {args.web_port} --strictPort')
    for name, url in owner_urls(args.web_port):
        say(f"  {name:18} {url}")
    say("No schedule is installed: `late`, `gate` and `settle` are explicit. Ctrl+C stops the API.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
