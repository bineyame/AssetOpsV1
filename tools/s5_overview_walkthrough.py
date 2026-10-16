"""S5-01 phase 2: the repeatable owner walkthrough for the selected-window Site Overview (tasks/S5-01-site-overview.md,
"Owner walkthrough"). It composes the existing producers in ONE private database and work directory:

- P01 (2026-10-23) from `backend/conversions/s4-power-demo-cases-v1.json` (`tools/s402b_power_cases.py`);
- the ordinary F01-gateway day (2026-10-02) from `tools/s4_finding_cases.py` (registered Lab run, durable gateway,
  TLS);
- P02 (2026-10-24) from `backend/conversions/s4-power-late-demo-cases-v1.json` through LR-01's
  `tools/s402c_late_power_walkthrough.py` (admission-numbered late mean, stopped at WITHHELD_GENERATOR_SERIES);
- a deliberately FAILED day (2026-10-07), the scoped failing-job pattern of `tools/s3_dispatch_walkthrough.py`;
- an unassessed day (2026-11-10): nothing is delivered for it.

Commands (database `assetops_s501_owner*` and work directory `var/s501_owner*` only; API 8925, web 5425):

    prepare   build the tree and database, seed every day, pass the S2 Evidence and Performance comparisons, tick
              the schedule and verify every day through the served Overview; STOPS (exit 1) instead of promising
              an amount that is not there
    serve     re-run the Performance comparison (unless the gate is closed) and serve the API on 8925 (foreground)
    attest    LR-01's SYSTEM-only labelled simulated clock attestation for P02 (no tick)
    tick      one explicit schedule pass in the `default` environment the API reads (no OS schedule installed),
              then the Performance comparison
    stop-schedule   mark the private schedule stopped and age its heartbeat and Site head past the production
                    thresholds, so the served Overview reads SCHEDULE_STOPPED at once
    start-schedule  clear the stop and run one schedule pass, restoring private observation
    gate --close | gate --open   move the Performance comparison reports aside / back (the source gate)
    drop      drop the database and remove the work directory

The schedule heartbeat uses the production thresholds (`scheduling/health.py`: 300 s environment, 900 s Site).
With no OS schedule installed, the served Overview reads SCHEDULE_STOPPED (no amount) once five minutes pass after
the last `tick`: run `tick` again before viewing an amount.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s402c_late_power_walkthrough as lr  # noqa: E402

p, s4, s2 = lr.p, lr.s4, lr.s2
SITE = "KOBO-001"
DB_PREFIX = "assetops_s501_owner"
WORK_PREFIX = "s501_owner"
ENVIRONMENT = "default"  # the environment the served Overview reads (main.py build_site_overview_read)
STATE = "s501-state.json"
EVIDENCE = "s501-walkthrough.json"
STOPPED_FLAG = "schedule-stopped"
GATE_DIR = Path("var") / "evidence" / "migration-performance"
DAYS = {"ordinary": "2026-10-02", "failed": "2026-10-07", "p01": "2026-10-23", "p02": "2026-10-24",
        "unassessed": "2026-11-10"}

FAIL_STAGE = r'''
import sys
from datetime import datetime, timedelta, timezone
from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
from assetops_backend.analytics.assessment_inputs import Window
from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
from assetops_backend.evidence.composition import build_evidence_ledger

url, failed_day = sys.argv[1:3]
tenant, site = build_evidence_ledger(url).site_scope("demo", "KOBO-001")
store = PostgresAssessmentStore(url)
now = datetime.now(timezone.utc)
start = datetime.fromisoformat(failed_day + "T00:00:00+00:00")

class StagedFailure:
    """Walkthrough-only: a model that always fails, scoped to one day, to show a FAILED day (S3 walkthrough)."""
    ANALYTIC_ID, MODEL_VERSION = "dispatch", "dispatch-3.1"

    @staticmethod
    def assess(_inputs):
        raise RuntimeError("walkthrough staged failure: the assessment could not be computed")

store.enqueue(tenant, site, "dispatch", Window(start, start + timedelta(days=1)), now)
for attempt in range(3):
    DispatchAssessmentWorker(store, model=StagedFailure, clock=lambda: now + timedelta(seconds=attempt),
                             backoff=timedelta(0)).run_pending(reconcile=False)
print("staged: FAILED", failed_day)
'''


def say(text: str) -> None:
    s4.say(text)


def step(text: str) -> None:
    s4.step(text)


def pg_url(db: str) -> str:
    return (f"postgresql://assetops:{os.environ.get('ASSETOPS_PG_PASSWORD', 'assetops-local-dev')}"
            f"@127.0.0.1:{os.environ.get('ASSETOPS_PG_PORT', '55432')}/{db}")


def get_json(url: str, timeout: float = 30) -> tuple[int, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode("utf-8"))
        except ValueError:
            return error.code, None


def overview(api_port: int, day: str, pin: tuple[str, str] | None = None) -> tuple[int, Any]:
    query = f"date={day}" + (f"&finding_id={pin[0]}&finding_revision_id={pin[1]}" if pin else "")
    return get_json(f"http://127.0.0.1:{api_port}/api/sites/{SITE}/overview?{query}")


def summary_line(day: str, status: int, body: Any) -> dict[str, Any]:
    if status != 200 or not isinstance(body, dict) or "money" not in body:
        return {"day": day, "http": status, "body": body}
    m, k = body["money"], body.get("known_finding") or {}
    return {"day": day, "http": status, "freshness": body["freshness"]["state"],
            "reasons": body["freshness"]["reasons"], "source_open": body["freshness"]["source_open"],
            "assessment": body["assessment"]["state"], "money": m["state"],
            "gate": (m.get("eligibility") or {}).get("state"), "amount": [m["amount_low"], m["amount_high"],
                                                                           m["currency"]],
            "demonstration": (m.get("demonstration") or {}).get("case_id"), "finding_id": k.get("id"),
            "finding_revision_id": k.get("revision_id"), "consequence_revision_id": m.get("consequence_revision_id"),
            "accepted_source": body["watermarks"]["accepted_source"],
            "analytic_selection_seq": body["watermarks"]["analytic_selection_seq"],
            "match_pass_id": body["watermarks"]["match_pass_id"], "previous_pin": body.get("previous_pin")}


class S5Walk(lr.Lr01Walk):
    """Every producer in one database; the LR-01 walk supplies P02 and the SYSTEM price."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__(args)
        self.p01_spec = json.loads((s2.REPO / p.POWER_SPEC_PATH).read_text(encoding="utf-8"))
        self.price_done: Any = None
        self.out.update(s501=True, days=DAYS)

    def backend(self, *argv: str, check: bool = True):
        # The LR-01 walk publishes SYSTEM price v1 as its step 0; this walk publishes it first (before P01), so the
        # second publication is the first one's result, not a duplicate assumption revision.
        if "assetops_backend.publish_assumption" in argv and self.price_done is not None:
            return self.price_done
        done = super().backend(*argv, check=check)
        if "assetops_backend.publish_assumption" in argv:
            self.price_done = done
        return done

    def seed_p01(self) -> None:
        case = self.p01_spec["cases"][0]
        step(f"P01. {case['case_id']} ({case['day']}, {self.p01_spec['label']})")
        late_spec = self.power_spec
        self.power_spec = self.p01_spec
        try:
            self.run_power_case(case)
        finally:
            self.power_spec = late_spec
        self.drain("P01 consequence")

    def stage_failed_day(self) -> None:
        step(f"FAILED day {DAYS['failed']}: a scoped failing assessment (walkthrough-only model)")
        done = self.backend("-c", FAIL_STAGE, self.db_url, DAYS["failed"])
        say("  " + done.stdout.strip().splitlines()[-1])

    def walk(self) -> None:
        o = self.out
        step("S2 Evidence comparison for KOBO-001 (opens the imported Overview)")
        done = self.py("-m", "assetops_backend.evidence_migration", "run", "--tenant", "demo", "--site", SITE,
                       check=False)
        o["evidence_comparison"] = {"exit": done.returncode, "tail": (done.stdout or done.stderr)[-400:]}
        say("  " + " | ".join(done.stdout.strip().splitlines()[-3:]))
        step("SYSTEM diesel price v1 (before P01, so P01 can be priced)")
        done = self.backend("-m", "assetops_backend.publish_assumption", "fixture", "--site", SITE, "--file",
                            str(Path("conversions") / "demo-diesel-price-publications.json"), "--step", "v1")
        o["price_v1"] = json.loads(done.stdout.strip().splitlines()[-1])
        self.seed_p01()
        step("F01-gateway: ordinary registered gateway day (Lab run, durable gateway, TLS)")
        self.gateway_case()
        step("P02 through the LR-01 walk (admission numbering), stopped at WITHHELD_GENERATOR_SERIES")
        super().walk()
        self.stage_failed_day()
        step("Schedule pass in the served environment, then the Performance comparison (source gate)")
        for n in (1, 2):
            o.setdefault("ticks", []).append({"label": f"prepare {n}", **tick(self.work, self.db)})
        self.gate("after the prepare ticks")
        self.verify()

    def verify(self) -> None:
        step(f"Verify every day through the served Overview (API {self.args.api_port})")
        self.start("overview-api", ["-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                                    str(self.args.api_port)], self.tree / "host", "Application startup complete")
        try:
            lines = {name: summary_line(day, *overview(self.args.api_port, day)) for name, day in DAYS.items()}
        finally:
            self.stop("overview-api")
        self.out["verify"] = lines
        for name, line in lines.items():
            say(f"  {name:10} {json.dumps(line)[:400]}")
        p01, p02 = lines["p01"], lines["p02"]
        self.expect("P01 2026-10-23: PRICED, labelled demonstration data, settled neighbourhood (CURRENT)",
                    p01.get("money") == "PRICED" and p01.get("demonstration") is not None
                    and p01.get("freshness") == "CURRENT", p01)
        self.expect("P02 2026-10-24: WITHHELD_GENERATOR_SERIES, no amount",
                    p02.get("money") == "WITHHELD_GENERATOR_SERIES" and p02["amount"] == [None, None, None], p02)
        self.expect("ordinary 2026-10-02: no current amount", lines["ordinary"].get("money") != "PRICED"
                    and lines["ordinary"].get("amount") == [None, None, None], lines["ordinary"])
        self.expect("2026-11-10: Unknown (UNASSESSED), no amount",
                    lines["unassessed"].get("freshness") == "UNASSESSED"
                    and lines["unassessed"].get("assessment") == "UNKNOWN", lines["unassessed"])
        self.expect("2026-10-07: FAILED, no amount", lines["failed"].get("assessment") == "FAILED"
                    and lines["failed"].get("money") != "PRICED", lines["failed"])
        state = self.state
        state.update(days=DAYS, p02_finding_id=p02.get("finding_id"),
                     p02_withheld_revision_id=p02.get("finding_revision_id"),
                     p02_withheld_consequence_revision_id=p02.get("consequence_revision_id"),
                     p01_finding_id=p01.get("finding_id"), p01_revision_id=p01.get("finding_revision_id"),
                     p01_consequence_revision_id=p01.get("consequence_revision_id"))

    def save(self) -> None:
        super().save()
        (self.work / STATE).write_text(json.dumps(self.state, indent=2), encoding="utf-8")

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
        self.out["state"] = self.state
        (self.work / EVIDENCE).write_text(json.dumps(self.out, indent=2, default=str), encoding="utf-8")
        say(f"Evidence: {self.work / EVIDENCE} ({len(self.failures)} failed checks)")


# ------------------------------------------------------------------------------------------- follow-up commands

def tick(work: Path, db: str) -> dict[str, Any]:
    if (work / STOPPED_FLAG).exists():
        raise SystemExit("The private schedule is stopped (stop-schedule). Run start-schedule first.")
    done = lr.tree_py(work, db, "-m", "assetops_backend.scheduling.run", "tick", "--environment", ENVIRONMENT,
                      "--max-sites", "5", "--s3-jobs", "10", "--consequence-items", "100", check=False)
    body = lr.last_json(done) or {"stderr": done.stderr[-800:]}
    say(f"  schedule pass ({ENVIRONMENT}): exit {done.returncode} {body.get('outcome')}")
    return {"exit": done.returncode, "outcome": body.get("outcome"), "failure": body.get("failure")}


def gate_closed(work: Path) -> bool:
    live = work / "tree" / GATE_DIR
    return live.with_name(live.name + ".closed").exists()


def comparison(work: Path, db: str) -> None:
    if gate_closed(work):
        say("  Performance gate is closed (gate --close): the comparison is not re-run.")
        return
    lr.performance_gate(work, db)


def gate(work: Path, close: bool) -> None:
    """`tools/s402b_fuel_cost_walkthrough.py` `gate(work, close)`: move the comparison reports aside or back."""
    live = work / "tree" / GATE_DIR
    aside = live.with_name(live.name + ".closed")
    src, dst = (live, aside) if close else (aside, live)
    if not src.exists():
        raise SystemExit(f"Nothing to move: {src} does not exist")
    if dst.exists():
        raise SystemExit(f"Refused: {dst} already exists")
    src.rename(dst)
    say(f"{'Closed' if close else 'Reopened'}: moved {src} -> {dst}.")


def age_schedule(db: str, work: Path) -> None:
    import psycopg

    (work / STOPPED_FLAG).write_text("stopped by tools/s5_overview_walkthrough.py stop-schedule\n", encoding="utf-8")
    with psycopg.connect(pg_url(db), autocommit=True) as c:
        a = c.execute("UPDATE schedule_tick_head SET heartbeat_at = heartbeat_at - interval '2 hours' "
                      "WHERE environment = %s", (ENVIRONMENT,)).rowcount
        b = c.execute("UPDATE schedule_site_head SET last_completed_at = last_completed_at - interval '2 hours', "
                      "last_failed_at = last_failed_at - interval '2 hours'").rowcount
    say(f"Private schedule stopped: heartbeat aged on {a} environment head(s), {b} Site head(s); `tick` refuses "
        "until start-schedule.")


def check_served(args: argparse.Namespace, state: dict[str, Any]) -> None:
    """When the API is up, show what the P02 day now reads: a reload of the owner's page, whose address carries the
    Finding version last shown (the page writes the served version back into the address)."""
    pin = (state.get("p02_finding_id"), state.get("p02_shown_revision_id") or state.get("p02_withheld_revision_id"))
    try:
        status, body = overview(args.api_port, DAYS["p02"], pin if all(pin) else None)
    except OSError:
        say(f"  (API on {args.api_port} is not running; start `serve` to reload the page.)")
        return
    line = summary_line(DAYS["p02"], status, body)
    say(f"  P02 {DAYS['p02']} now: {json.dumps(line)[:700]}")
    if line.get("finding_revision_id"):
        state["p02_shown_revision_id"] = line["finding_revision_id"]
        (args_work(args) / STATE).write_text(json.dumps(state, indent=2), encoding="utf-8")


def args_work(args: argparse.Namespace) -> Path:
    return (s2.REPO / args.work).resolve() if not Path(args.work).is_absolute() else Path(args.work).resolve()


def followup(args: argparse.Namespace, work: Path) -> int:
    state_file = work / STATE
    if args.command == "gate":
        gate(work, args.close)
        check_served(args, json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {})
        return 0
    if not state_file.exists():
        raise SystemExit(f"No {STATE} in {work}: run `prepare --db {args.db} --work {args.work}` first.")
    state = json.loads(state_file.read_text(encoding="utf-8"))
    if args.command == "attest":
        out = lr.record_attestation(work, args.db, state, "record")
        state["attestations"] += 1
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        say("Attestation recorded. Reload P02 BEFORE ticking: no amount (see the walkthrough for the two states).")
        check_served(args, state)
        return 0 if out["exit"] == 0 else 1
    if args.command == "tick":
        out = tick(work, args.db)
        comparison(work, args.db)
        check_served(args, state)
        return 0 if out["exit"] == 0 else 1
    if args.command == "stop-schedule":
        age_schedule(args.db, work)
        check_served(args, state)
        return 0
    if args.command == "start-schedule":
        (work / STOPPED_FLAG).unlink(missing_ok=True)
        out = tick(work, args.db)
        comparison(work, args.db)
        check_served(args, state)
        return 0 if out["exit"] == 0 else 1
    # serve
    comparison(work, args.db)
    log = work / "logs" / f"api-{args.api_port}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen([str(s2.PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                             str(args.api_port)], cwd=work / "tree" / "host", env=lr.tree_env(work, args.db),
                            stdout=log.open("w"), stderr=subprocess.STDOUT)
    say(f"API for {args.db}: python -m uvicorn lab_app:app --host 127.0.0.1 --port {args.api_port} (log {log})")
    say("Frontend, from frontend/:")
    say(f'  $env:ASSETOPS_API_PORT="{args.api_port}"; npm.cmd run dev -- --port {args.web_port} --strictPort')
    for name, day in DAYS.items():
        say(f"  {name:10} http://localhost:{args.web_port}/sites/{SITE}?date={day}")
    say("Ctrl+C stops the API.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s5_overview_walkthrough.py")
    parser.add_argument("command", choices=("prepare", "serve", "attest", "tick", "stop-schedule", "start-schedule",
                                            "gate", "drop"))
    parser.add_argument("--db", required=True, help=f"private database, {DB_PREFIX}*")
    parser.add_argument("--work", required=True, help=f"private work directory, var/{WORK_PREFIX}*")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--close", action="store_true", help="gate: close the Performance source gate")
    group.add_argument("--open", action="store_true", help="gate: reopen the Performance source gate")
    parser.add_argument("--api-port", type=int, default=8925)
    parser.add_argument("--web-port", type=int, default=5425)
    parser.add_argument("--tls-port", type=int, default=8926)
    parser.add_argument("--http-port", type=int, default=8927)
    args = parser.parse_args(argv)
    if not (args.db.startswith(DB_PREFIX) and args.db.replace("_", "").isalnum() and not args.db.endswith("_test")):
        raise SystemExit(f"Refusing database {args.db!r}: use a private {DB_PREFIX}* database.")
    work = (s2.REPO / args.work).resolve() if not Path(args.work).is_absolute() else Path(args.work).resolve()
    var = (s2.REPO / "var").resolve()
    if work.parent != var or not work.name.startswith(WORK_PREFIX):
        raise SystemExit(f"Refusing work directory {args.work!r}: use var/{WORK_PREFIX}* in this repository.")
    if args.command == "gate" and not (args.close or args.open):
        raise SystemExit("gate needs --close or --open")
    if args.command == "drop":
        import psycopg

        admin = s2.PG_ADMIN.format(pw=os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev"),
                                   port=os.environ.get("ASSETOPS_PG_PORT", "55432"))
        with psycopg.connect(admin, autocommit=True) as c:
            c.execute(f"DROP DATABASE IF EXISTS {args.db} WITH (FORCE)")
        say(f"dropped {args.db}")
        if work.exists():
            shutil.rmtree(work)
            say(f"removed {work}")
        return 0
    if args.command != "prepare":
        return followup(args, work)
    s2.DEMO_DB = args.db
    walk_args = SimpleNamespace(work=str(work), artifact=None, tls_port=args.tls_port, http_port=args.http_port,
                                cadence_seconds=60, db=args.db, variant="admission", through="withheld",
                                api_port=args.api_port, web_port=args.web_port)
    walk = S5Walk(walk_args)  # type: ignore[arg-type]
    walk.args_work = str(work)
    started = time.time()
    walk.run()
    say(f"prepare finished in {time.time() - started:.0f} s with {len(walk.failures)} failed checks.")
    if walk.failures:
        say("STOPPED: the walkthrough does not promise what the served Overview does not show. Failed checks:")
        for f in walk.failures:
            say(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
