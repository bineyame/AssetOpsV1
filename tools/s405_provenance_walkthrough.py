"""S4-05b phase 2: the repeatable owner walkthrough for stored source provenance
(tasks/S4-05b-producers-reads-walkthrough.md, "Phase 2"; labels per D-2026-10-16-s405b-label).

It reuses the S5-01 composition (`tools/s5_overview_walkthrough.py`), whose producers now publish before upload:

- owner case, private DB `assetops_s405_owner<suffix>`, work `var/s405_owner<suffix>`:
  P01 (2026-10-23) and P02 (2026-10-24) authored batches, each exact batch published before upload
  ("Prepared example data"); the ordinary registered Lab run (2026-10-02), registered by the Lab Commit before the
  gateway releases it ("Generated test data"); a FAILED day and an unassessed day.
- old case, private DB `assetops_s405_old<suffix>`, work `var/s405_old<suffix>`: the same-day P01 batches uploaded
  by the pre-S4-05b producer, with no publication (the old host). Nothing is backfilled: "Source unverified" and no
  current amount.
- mixed case, private DB `assetops_s405_mixed<suffix>`, work `var/s405_mixed<suffix>`: P01 with one ordinary
  context device uploaded unbound beside the published batches, so the selected citation set and the consequence's
  records disagree: "Sources do not agree" and no current amount.

Commands (DBs `assetops_s405*` and work folders `var/s405*` only; API 8935, web 5435):

    prepare            build and verify all three cases through the served API; STOPS (exit 1) on any failed check
    links              print the exact Finding, Evidence, consequence/Financials and Overview URLs of every case
    serve [--case C]   serve case C (owner|old|mixed, default owner) on the API port, ticking the private schedule
                       every two minutes so the money gates stay current; Ctrl+C stops it
    drop               drop the three databases and remove the three work folders
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s5_overview_walkthrough as s5  # noqa: E402

lr, s4, s2 = s5.lr, s5.s4, s5.s2
SITE = s5.SITE
DB_PREFIX, WORK_PREFIX = "assetops_s405", "s405"
CASES = ("owner", "old", "mixed")
STATE = "s405-state.json"
EVIDENCE = "s405-walkthrough.json"
DAYS = s5.DAYS
TICK_SECONDS = 120


def say(text: str) -> None:
    s4.say(text)


def step(text: str) -> None:
    s4.step(text)


def names(suffix: str) -> dict[str, tuple[str, Path]]:
    var = (s2.REPO / "var").resolve()
    return {case: (f"{DB_PREFIX}_{case}{suffix}", var / f"{WORK_PREFIX}_{case}{suffix}") for case in CASES}


def query(db: str, sql: str, *params: Any) -> list[tuple]:
    import psycopg

    with psycopg.connect(s5.pg_url(db)) as c:
        return list(c.execute(sql, params).fetchall())


def latest_on(db: str, day: str) -> list[dict[str, Any]]:
    """The latest FindingRevision of every Finding whose episode starts on `day` (UTC)."""
    rows = query(db, "SELECT r.finding_id::text, r.id::text, r.revision_no FROM finding_revision r WHERE "
                     "r.revision_no = (SELECT max(x.revision_no) FROM finding_revision x WHERE x.finding_id = "
                     "r.finding_id) AND (r.episode_start AT TIME ZONE 'UTC')::date = %s::date "
                     "ORDER BY r.episode_start, r.finding_id", day)
    return [{"finding_id": f, "revision_id": r, "revision_no": n} for f, r, n in rows]


def history_on(db: str, finding_id: str) -> dict[str, Any]:
    """Earlier FindingRevisions and every consequence revision of this Finding (audit-only history)."""
    revs = query(db, "SELECT id::text, revision_no FROM finding_revision WHERE finding_id = %s ORDER BY revision_no",
                 finding_id)
    cons = query(db, "SELECT c.id::text, c.revision_no, c.state, c.finding_revision_id::text FROM "
                     "financial_consequence_revision c JOIN finding_revision r ON r.id = c.finding_revision_id "
                     "WHERE r.finding_id = %s ORDER BY r.revision_no, c.revision_no", finding_id)
    return {"revisions": [{"id": i, "revision_no": n} for i, n in revs],
            "consequences": [{"id": i, "revision_no": n, "state": s, "finding_revision_id": fr}
                             for i, n, s, fr in cons]}


def financials_line(api_port: int, pick: dict[str, Any]) -> dict[str, Any]:
    base = f"http://127.0.0.1:{api_port}/api/sites/{SITE}/findings/{pick['finding_id']}"
    status, body = s5.get_json(f"{base}/financials?revision_id={pick['revision_id']}")
    if status != 200 or not isinstance(body, dict):
        return {"http": status, "body": body}
    c, sp = body.get("consequence") or {}, body.get("source_provenance") or {}
    fr, cr = sp.get("finding_revision") or {}, sp.get("consequence_revision") or {}
    e_status, evidence = s5.get_json(f"{base}/evidence?revision_id={pick['revision_id']}")
    return {"http": status, "finding_id": pick["finding_id"], "finding_revision_id": pick["revision_id"],
            "money": c.get("state"), "amount": c.get("amount"), "currency": c.get("currency"),
            "consequence_revision_id": c.get("consequence_revision_id"),
            "finding_source": fr.get("state"), "consequence_source": cr.get("state"),
            "source_reasons": [r.get("code") for r in (fr.get("reasons") or []) + (cr.get("reasons") or [])],
            "publication_ids": sorted(set(fr.get("publication_ids") or []) | set(cr.get("publication_ids") or [])),
            "fixtures": cr.get("fixtures") or fr.get("fixtures"), "runs": cr.get("runs") or fr.get("runs"),
            "cited_accepted_evidence_ids": len(fr.get("cited_accepted_evidence_ids") or []),
            "problematic_accepted_evidence_ids": cr.get("problematic_accepted_evidence_ids")
            or fr.get("problematic_accepted_evidence_ids") or [],
            "evidence_http": e_status,
            "evidence_source": ((evidence or {}).get("source_provenance") or {}).get("state")
            if isinstance(evidence, dict) else None}


class S405Walk(s5.S5Walk):
    """The S5-01 composition for the owner case; P01 alone, with a publication policy, for old and mixed."""

    def __init__(self, args: argparse.Namespace, case: str) -> None:
        super().__init__(args)
        self.s405_case = case
        self.out.update(s405=case)

    def post(self, envelopes: list[tuple[str, str]], fixture: tuple[str, str] | None = None) -> list[str]:
        if fixture is None or self.s405_case == "owner":
            return super().post(envelopes, fixture)
        if self.s405_case == "old":  # the pre-S4-05b producer: uploads without any publication
            return super().post(envelopes, None)
        power = self.p01_spec["power_rules"]["device"]
        plain = sorted({device for device, _ in envelopes if device != power})[:1]
        self.out["unbound_context_devices"] = plain
        bound = [e for e in envelopes if e[0] not in plain]
        return super().post(bound, fixture) + super().post([e for e in envelopes if e[0] in plain], None)

    def walk(self) -> None:
        if self.s405_case == "owner":
            super().walk()  # S5-01's producers in order; ends in self.verify()
            return
        o = self.out
        step("S2 Evidence comparison for KOBO-001 (opens the imported Site)")
        done = self.py("-m", "assetops_backend.evidence_migration", "run", "--tenant", "demo", "--site", SITE,
                       check=False)
        o["evidence_comparison"] = {"exit": done.returncode, "tail": (done.stdout or done.stderr)[-400:]}
        step("SYSTEM diesel price v1 (so P01 would be priced if its source allowed it)")
        done = self.backend("-m", "assetops_backend.publish_assumption", "fixture", "--site", SITE, "--file",
                            str(Path("conversions") / "demo-diesel-price-publications.json"), "--step", "v1")
        o["price_v1"] = json.loads(done.stdout.strip().splitlines()[-1])
        self.seed_p01()
        step("Schedule pass in the served environment, then the Performance comparison (source gate)")
        for n in (1, 2):
            o.setdefault("ticks", []).append({"label": f"prepare {n}", **s5.tick(self.work, self.db)})
        self.gate("after the prepare ticks")
        self.verify()

    def verify(self) -> None:
        step(f"Verify the {self.s405_case} case through the served API ({self.args.api_port})")
        self.start("s405-api", ["-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                                str(self.args.api_port)], self.tree / "host", "Application startup complete")
        days = {"p01": DAYS["p01"]} if self.s405_case != "owner" else {k: DAYS[k] for k in ("p01", "p02", "ordinary")}
        lines: dict[str, Any] = {}
        try:
            for name, day in days.items():
                picks = latest_on(self.db, day)
                lines[name] = {"day": day, "findings": [financials_line(self.args.api_port, x) for x in picks],
                               "overview": s5.summary_line(day, *s5.overview(self.args.api_port, day))}
                for pick in picks:
                    pick.update(history_on(self.db, pick["finding_id"]))
                lines[name]["picks"] = picks
        finally:
            self.stop("s405-api")
        self.out["verify"] = lines
        for name, line in lines.items():
            for f in line["findings"]:
                say(f"  {name:8} {json.dumps({k: f.get(k) for k in ('money', 'amount', 'finding_source', 'consequence_source', 'source_reasons')})[:400]}")
            say(f"  {name:8} overview {json.dumps({k: line['overview'].get(k) for k in ('money', 'source', 'amount')})}")

        def first(name: str) -> dict[str, Any]:
            found = lines.get(name, {}).get("findings") or [{}]
            return found[0]

        p01 = first("p01")
        if self.s405_case == "owner":
            p02, ordinary = first("p02"), first("ordinary")
            self.expect("P01: Prepared example data on the Finding and its consequence, with a current amount",
                        p01.get("finding_source") == p01.get("consequence_source") == "AUTHORED_DEMONSTRATION"
                        and p01.get("money") == "PRICED" and p01.get("amount") is not None, p01)
            self.expect("P01 Overview: PRICED with the same stored source",
                        lines["p01"]["overview"].get("money") == "PRICED"
                        and lines["p01"]["overview"].get("source") == "AUTHORED_DEMONSTRATION", lines["p01"]["overview"])
            self.expect("P02: Prepared example data, its own publication(s)",
                        p02.get("finding_source") == "AUTHORED_DEMONSTRATION"
                        and set(p02.get("publication_ids") or []).isdisjoint(p01.get("publication_ids") or []), p02)
            regs = [f for f in lines["ordinary"]["findings"] if f.get("finding_source") == "REGISTERED_SIMULATION"]
            self.expect("ordinary registered run: Generated test data, with its recorded run, and no current amount",
                        bool(regs) and all(f.get("amount") is None and f.get("runs") for f in regs),
                        lines["ordinary"]["findings"])
        else:
            want = "UNKNOWN" if self.s405_case == "old" else "MIXED"
            label = "Source unverified" if self.s405_case == "old" else "Sources do not agree"
            self.expect(f"P01 ({self.s405_case}): {label} on the Finding and consequence, no current amount",
                        p01.get("finding_source") == want and p01.get("consequence_source") == want
                        and p01.get("money") == "MIXED_OR_UNKNOWN_SOURCE" and p01.get("amount") is None, p01)
            self.expect(f"P01 ({self.s405_case}) Overview: MIXED_OR_UNKNOWN_SOURCE, no amount",
                        lines["p01"]["overview"].get("money") == "MIXED_OR_UNKNOWN_SOURCE"
                        and lines["p01"]["overview"].get("amount") == [None, None, None], lines["p01"]["overview"])
            if self.s405_case == "old":
                self.expect("old host: no publication was backfilled", not p01.get("publication_ids"), p01)
            else:
                self.expect("mixed: the unbound context readings are named", bool(
                    p01.get("problematic_accepted_evidence_ids")), p01)
        self.state.update(case=self.s405_case, verify=lines)

    def save(self) -> None:
        (self.work / STATE).write_text(json.dumps(self.state, indent=2, default=str), encoding="utf-8")

    def run(self) -> None:
        self.setup()
        try:
            self.prepare()
            self.walk()
            self.save()
        finally:
            step("Stopping every process this script started")
            self.stop_all()
        self.out["failures"] = list(self.failures)
        (self.work / EVIDENCE).write_text(json.dumps(self.out, indent=2, default=str), encoding="utf-8")
        say(f"Evidence: {self.work / EVIDENCE} ({len(self.failures)} failed checks)")


def prepare(args: argparse.Namespace, cases: dict[str, tuple[str, Path]]) -> int:
    failures: dict[str, list[str]] = {}
    started = time.time()
    for case, (db, work) in cases.items():
        if args.only and case != args.only:
            continue
        step(f"=== {case} case: database {db}, work {work}")
        s2.DEMO_DB = db
        walk_args = SimpleNamespace(work=str(work), artifact=None, tls_port=args.tls_port, http_port=args.http_port,
                                    cadence_seconds=60, db=db, variant="admission", through="withheld",
                                    api_port=args.api_port, web_port=args.web_port)
        walk = S405Walk(walk_args, case)  # type: ignore[arg-type]
        walk.args_work = str(work)
        walk.run()
        failures[case] = list(walk.failures)
    say(f"prepare finished in {time.time() - started:.0f} s; failed checks: "
        f"{ {k: len(v) for k, v in failures.items()} }")
    bad = [f"{k}: {x}" for k, v in failures.items() for x in v]
    if bad:
        say("STOPPED: the walkthrough does not promise what the served pages do not show. Failed checks:")
        for f in bad:
            say(f"  - {f}")
        return 1
    return 0


def links(args: argparse.Namespace, cases: dict[str, tuple[str, Path]]) -> int:
    web = f"http://localhost:{args.web_port}/sites/{SITE}"
    for case, (db, work) in cases.items():
        state_file = work / STATE
        if not state_file.exists():
            say(f"\n[{case}] not prepared ({state_file} missing)")
            continue
        state = json.loads(state_file.read_text(encoding="utf-8"))
        say(f"\n[{case}] run `serve --case {case}` first (database {db})")
        for name, line in state["verify"].items():
            say(f"  {name} ({line['day']}): Site Overview {web}?date={line['day']}")
            for pick, seen in zip(line["picks"], line["findings"]):
                fid, rid = pick["finding_id"], pick["revision_id"]
                say(f"    expected: {seen.get('finding_source')} / money {seen.get('money')} / amount "
                    f"{seen.get('amount')}")
                say(f"    Finding:    {web}/findings/{fid}?revision_id={rid}")
                say(f"    Evidence:   {web}/findings/{fid}/evidence?revision_id={rid}")
                say(f"    Financials: {web}/financials?finding_id={fid}&revision_id={rid}")
                for c in pick.get("consequences", []):
                    tag = "current head" if c["id"] == seen.get("consequence_revision_id") else "history, audit only"
                    say(f"    fuel cost version {c['revision_no']} ({c['state']}, {tag}): {web}/financials?finding_id="
                        f"{fid}&revision_id={c['finding_revision_id']}&consequence_revision_id={c['id']}")
                for r in pick.get("revisions", []):
                    if r["id"] != rid:
                        say(f"    earlier Finding version {r['revision_no']} (history): {web}/findings/{fid}"
                            f"?revision_id={r['id']}")
    return 0


def serve(args: argparse.Namespace, cases: dict[str, tuple[str, Path]]) -> int:
    db, work = cases[args.case]
    if not (work / STATE).exists():
        raise SystemExit(f"No {STATE} in {work}: run `prepare` first.")
    s5.tick(work, db)
    s5.comparison(work, db)
    log = work / "logs" / f"api-{args.api_port}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([str(s2.PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                             str(args.api_port)], cwd=work / "tree" / "host", env=lr.tree_env(work, db),
                            stdout=log.open("w"), stderr=subprocess.STDOUT)
    say(f"API for the {args.case} case ({db}) on http://127.0.0.1:{args.api_port} (log {log}).")
    say("In a second terminal, from frontend/:")
    say(f'  $env:ASSETOPS_API_PORT="{args.api_port}"; npm.cmd run dev -- --port {args.web_port} --strictPort')
    say(f"Then open the [{args.case}] URLs that `links` prints. Ctrl+C stops the API.")
    try:
        last = time.time()
        while proc.poll() is None:
            time.sleep(2)
            if time.time() - last >= TICK_SECONDS:
                s5.tick(work, db)
                last = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=20)
    return 0


def drop(cases: dict[str, tuple[str, Path]]) -> int:
    import psycopg

    admin = s2.PG_ADMIN.format(pw=os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev"),
                               port=os.environ.get("ASSETOPS_PG_PORT", "55432"))
    for db, work in cases.values():
        with psycopg.connect(admin, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
        say(f"dropped {db}")
        if work.exists():
            shutil.rmtree(work)
            say(f"removed {work}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s405_provenance_walkthrough.py")
    parser.add_argument("command", choices=("prepare", "links", "serve", "drop"))
    parser.add_argument("--suffix", default="", help="appended to every database and work folder name")
    parser.add_argument("--case", choices=CASES, default="owner", help="serve: which case's database to serve")
    parser.add_argument("--only", choices=CASES, default=None, help="prepare: build one case only")
    parser.add_argument("--api-port", type=int, default=8935)
    parser.add_argument("--web-port", type=int, default=5435)
    parser.add_argument("--tls-port", type=int, default=8936)
    parser.add_argument("--http-port", type=int, default=8937)
    args = parser.parse_args(argv)
    if args.suffix and not args.suffix.replace("_", "").isalnum():
        raise SystemExit(f"Refusing suffix {args.suffix!r}: letters, digits and underscores only.")
    cases = names(args.suffix)
    var = (s2.REPO / "var").resolve()
    for db, work in cases.values():
        if not (db.startswith(DB_PREFIX) and db.replace("_", "").isalnum() and not db.endswith("_test")):
            raise SystemExit(f"Refusing database {db!r}: use a private {DB_PREFIX}* database.")
        if work.parent != var or not work.name.startswith(WORK_PREFIX):
            raise SystemExit(f"Refusing work folder {work}: use var/{WORK_PREFIX}* in this repository.")
    if args.command == "drop":
        return drop(cases)
    if args.command == "links":
        return links(args, cases)
    if args.command == "serve":
        return serve(args, cases)
    return prepare(args, cases)


if __name__ == "__main__":
    raise SystemExit(main())
