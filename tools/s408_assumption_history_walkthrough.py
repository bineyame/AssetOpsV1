"""S4-08: the guarded owner walkthrough for the Site assumption and consequence history
(tasks/S4-08-assumption-consequence-history.md, "Build, proof and handoff").

It wraps the S4-05b provenance walkthrough (`tools/s405_provenance_walkthrough.py`) under private `assetops_s408*`
databases and `var/s408*` work folders, then adds price and fuel cost history to the owner case:

- owner case (`assetops_s408_owner<suffix>`): P01 (2026-10-23) and P02 (2026-10-24) authored batches ("Prepared
  example data"), priced at the demonstration v1 price. This tool then publishes v2 SUCCESSION (2030), v3 June
  CORRECTION, v4 October CORRECTION (1.28: the price changed, the measured result did not), an S4-06 equal-start
  SUCCESSION at 2030-01-01 (v5), and finally a correction that changes price part-way through P01's window (v6),
  so P01's newest version is unpriced. A schedule pass after each recomputes the fuel cost versions. The recorded
  cutoffs before v4 (T1), after v4 (T2) and after v6 (T3) are kept.
- mixed case (`assetops_s408_mixed<suffix>`): P01 with one unbound context device: "Sources do not agree", so every
  recorded amount is withheld.
- closed source: `close-gate` moves the owner case's Performance comparison aside; every version stays listed
  without an amount. `open-gate` restores it.

`prepare` checks every claim through the served API and STOPS (exit 1) on any failed check; it never promises what
the served pages do not show. Commands (API 8968, web 5468):

    prepare                   build both cases, add the history, verify through the API
    links                     print the exact URLs to open (default, explicit cutoffs, next page, exact versions)
    serve [--case owner|mixed]  serve that case's API (foreground; ticks the private schedule)
    close-gate | open-gate    close or reopen the owner case's source gate
    drop                      drop both databases and remove both work folders
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s405_provenance_walkthrough as s405  # noqa: E402

s5, lr, s2 = s405.s5, s405.lr, s405.s2
s405.DB_PREFIX, s405.WORK_PREFIX = "assetops_s408", "s408"
SITE = s405.SITE
CASES = ("owner", "mixed")
STATE = "s408-state.json"
PRICES = Path("conversions") / "demo-diesel-price-publications.json"
API = "/api/sites/" + SITE + "/financial-assumptions/consequences"
failures: list[str] = []


def say(text: str) -> None:
    s405.say(text)


def check(name: str, ok: bool, detail: Any = None) -> None:
    say(f"  {'PASS' if ok else 'FAIL'}  {name}{'' if detail is None else '  ' + json.dumps(detail, default=str)[:300]}")
    if not ok:
        failures.append(name)


def names(suffix: str) -> dict[str, tuple[str, Path]]:
    return {k: v for k, v in s405.names(suffix).items() if k in CASES}


def backend(work: Path, db: str, *argv: str) -> subprocess.CompletedProcess:
    done = subprocess.run([str(s2.PY), *argv], cwd=work / "tree" / "backend", env=lr.tree_env(work, db),
                          capture_output=True, text=True, timeout=900)
    if done.returncode != 0:
        raise SystemExit(f"FAILED: python {' '.join(argv[:3])}\n{done.stdout}\n{done.stderr}")
    return done


def db_now(db: str) -> str:
    """The database clock (the clock `recorded_at` uses), as the exact string the history read returns."""
    (row,) = s405.query(db, "SELECT clock_timestamp()")
    return row[0].astimezone(timezone.utc).isoformat()


def p01_window(db: str) -> tuple[datetime, datetime]:
    rows = s405.query(db, "SELECT window_start, window_end FROM financial_consequence_revision "
                          "WHERE window_start >= '2026-10-23' AND window_start < '2026-10-24' "
                          "ORDER BY recorded_at DESC LIMIT 1")
    if not rows:
        raise SystemExit("FAILED: the owner case has no P01 fuel cost version to build history on.")
    return rows[0][0], rows[0][1]


def history_fixture(work: Path, db: str) -> Path:
    """The demonstration price steps plus v5 (S4-06 equal-start SUCCESSION at 2030-01-01) and v6 (a correction
    that starts part-way through P01's window, so P01 has no single price)."""
    source = json.loads((work / "tree" / "backend" / PRICES).read_text(encoding="utf-8"))
    start, end = p01_window(db)
    split = (start + (end - start) / 2).replace(second=0, microsecond=0)
    source["steps"] += [
        {"step": "v5", "change_kind": "SUCCESSION", "currency": "USD", "value": "1.35", "basis": "AUTHORED_ESTIMATE",
         "source_reference": "Walkthrough price (replaces the scheduled 2030 change at the same start)",
         "valid_from": "2030-01-01T00:00:00Z", "valid_to": None, "expected_prior_step": "v4",
         "idempotency_key": "s408-walkthrough-v5"},
        {"step": "v6", "change_kind": "CORRECTION", "currency": "USD", "value": "1.31", "basis": "AUTHORED_ESTIMATE",
         "source_reference": "Walkthrough correction starting part-way through one finding's time",
         "correction_reason": "Walkthrough: a price change part-way through one finding's time",
         "valid_from": split.strftime("%Y-%m-%dT%H:%M:%SZ"), "valid_to": "2026-10-24T00:00:00Z",
         "expected_prior_step": "v5", "idempotency_key": "s408-walkthrough-v6"},
    ]
    out = work / "s408-prices.json"
    out.write_text(json.dumps(source, indent=2), encoding="utf-8")
    return out


def publish(work: Path, db: str, fixture: Path, *steps: str) -> None:
    argv = ["-m", "assetops_backend.publish_assumption", "fixture", "--site", SITE, "--file", str(fixture)]
    for st in steps:
        argv += ["--step", st]
    for line in backend(work, db, *argv).stdout.splitlines():
        if line.strip().startswith("{"):
            body = json.loads(line)
            say(f"  price {body.get('step')}: {body.get('change_kind')} version {body.get('revision_no')}"
                f"{' (already published)' if body.get('replayed') else ''}")


def add_history(work: Path, db: str) -> dict[str, str]:
    s405.step("S4-08 history: price versions v2-v6 with a schedule pass after each change")
    cut: dict[str, str] = {}
    for _ in range(2):
        s5.tick(work, db)
    cut["T1"] = db_now(db)
    fixture = history_fixture(work, db)
    publish(work, db, fixture, "v1", "v2", "v3", "v4")
    for _ in range(2):
        s5.tick(work, db)
    cut["T2"] = db_now(db)
    publish(work, db, fixture, "v5", "v6")
    for _ in range(2):
        s5.tick(work, db)
    cut["T3"] = db_now(db)
    return cut


class Api:
    def __init__(self, work: Path, db: str, port: int) -> None:
        self.base = f"http://127.0.0.1:{port}"
        log = work / "logs" / f"s408-api-{port}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        self.proc = subprocess.Popen([str(s2.PY), "-m", "uvicorn", "lab_app:app", "--host", "127.0.0.1", "--port",
                                      str(port)], cwd=work / "tree" / "host", env=lr.tree_env(work, db),
                                     stdout=log.open("w"), stderr=subprocess.STDOUT)
        for _ in range(240):
            try:
                status, _ = s5.get_json(f"{self.base}/api/sites/{SITE}", timeout=2)
            except OSError:  # not listening yet
                status = 0
            if status:
                return
            time.sleep(0.5)
        self.stop()
        raise SystemExit(f"FAILED: the API on {port} did not start (log {log})")

    def get(self, path: str, **params: Any) -> tuple[int, Any]:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        return s5.get_json(f"{self.base}{path}{'?' + query if query else ''}")

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=30)


def verify_owner(api: Api, work: Path, cut: dict[str, str]) -> dict[str, Any]:
    s405.step("Verify the owner case's history through the served API")
    status, body = api.get(API)
    check("default read answers 200", status == 200, status)
    rows = body["rows"]
    check("no current amount is claimed (current_amount_shown false)", body["current_amount_shown"] is False)
    check("default cutoff is fixed by the server", body["cutoff"]["selected_by"] == "SERVER_DEFAULT", body["cutoff"])
    _, prices = api.get(body["links"]["api_prices_at_cutoff"].split("?")[0],
                        recorded_at=body["cutoff"]["recorded_at"])
    check("price read reports the identical cutoff string", prices["cutoff"]["recorded_at"] ==
          body["cutoff"]["recorded_at"], [prices["cutoff"]["recorded_at"], body["cutoff"]["recorded_at"]])
    kinds = {(r["at_cutoff"], r["recorded_amount"]["disposition"], r["change_from_prior"]) for r in rows}
    check("earlier and latest versions are both listed", {r["at_cutoff"] for r in rows} ==
          {"CURRENT_AT_CUTOFF", "HISTORICAL_AT_CUTOFF"}, sorted(kinds))
    shown = [r for r in rows if r["recorded_amount"]["disposition"] == "SHOWN"]
    check("a recorded amount is shown only as labelled history", bool(shown) and all(
        r["recorded_amount"]["label"] and r["recorded_amount"]["is_current_amount"] is False for r in shown),
        len(shown))
    check("a price-only change is recognised", any(r["change_from_prior"] == "PRICE_ONLY" for r in rows))
    unpriced = [r for r in rows if r["state"] == "UNPRICED"]
    check("an unpriced version is listed with no price link and no amount", bool(unpriced) and all(
        r["price"]["state"] == "NO_PRICE_LINK" and r["recorded_amount"]["amount"] is None for r in unpriced))
    sources = {r["source_provenance"]["state"] for r in rows}
    check("every row's source is a confirmed stored source", bool(sources) and sources <= {
        "AUTHORED_DEMONSTRATION", "REGISTERED_SIMULATION"}, sorted(sources))
    at = {}
    for name in ("T1", "T2", "T3"):
        _, at[name] = api.get(API, recorded_at=cut[name])
        check(f"{name}: explicit cutoff is kept", at[name]["cutoff"]["recorded_at"] ==
              datetime.fromisoformat(cut[name]).astimezone(timezone.utc).isoformat(), at[name]["cutoff"])
        check(f"{name}: no row recorded after the cutoff", all(
            datetime.fromisoformat(r["recorded_at"]) <= datetime.fromisoformat(cut[name]) for r in at[name]["rows"]))
    t1_current = {r["consequence_revision_id"] for r in at["T1"]["rows"] if r["at_cutoff"] == "CURRENT_AT_CUTOFF"}
    t3 = {r["consequence_revision_id"]: r["at_cutoff"] for r in at["T3"]["rows"]}
    check("a version latest at T1 is an earlier version at T3", any(t3.get(c) == "HISTORICAL_AT_CUTOFF"
                                                                    for c in t1_current), sorted(t1_current))
    _, first = api.get(API, recorded_at=cut["T3"], limit=2)
    pages = [first]
    while pages[-1].get("next_cursor"):
        _, nxt = api.get(API, recorded_at=cut["T3"], after=pages[-1]["next_cursor"], limit=2)
        pages.append(nxt)
    paged = [r["consequence_revision_id"] for p in pages for r in p["rows"]]
    check("paging at T3 neither duplicates nor skips", len(pages) > 1 and sorted(paged) == sorted(t3), len(pages))
    status, refused = api.get(API, recorded_at=cut["T3"], after="not-a-cursor")
    check("a cursor this list did not issue is refused with no rows", status == 400, refused)
    status, _ = api.get("/api/sites/NOPE-001/financial-assumptions/consequences")
    check("an unknown Site is refused", status == 404, status)
    pick = next(r for r in rows if r["at_cutoff"] == "CURRENT_AT_CUTOFF" and r["state"] == "PRICED")
    return {"cutoffs": cut, "default_cutoff": body["cutoff"]["recorded_at"], "pick": pick,
            "next_cursor_T3": first.get("next_cursor"),
            "rows_T3": [{k: r[k] for k in ("finding_id", "finding_revision_id", "consequence_revision_id",
                                           "revision_no", "at_cutoff", "state", "change_from_prior")}
                        | {"amount": r["recorded_amount"]["disposition"]} for r in at["T3"]["rows"]]}


def verify_closed(api_port: int, work: Path, db: str) -> None:
    s405.step("Close the owner case's source gate: every version stays listed without an amount")
    s5.gate(work, True)
    try:
        api = Api(work, db, api_port)
        try:
            _, body = api.get(API)
            check("closed source keeps every version listed", bool(body["rows"]) and not body["source_gate"]["open"])
            check("closed source shows no amount", {r["recorded_amount"]["disposition"] for r in body["rows"]} ==
                  {"SOURCE_CLOSED"})
        finally:
            api.stop()
    finally:
        s5.gate(work, False)


def verify_mixed(api: Api) -> None:
    s405.step("Verify the mixed case: recorded amounts withheld")
    _, body = api.get(API)
    priced = [r for r in body["rows"] if r["state"] == "PRICED"]
    check("mixed case lists its versions", bool(body["rows"]))
    check("mixed source withholds every recorded amount", bool(priced) and all(
        r["recorded_amount"]["disposition"] == "MIXED_OR_UNKNOWN_SOURCE" for r in priced),
        sorted({r["source_provenance"]["state"] for r in body["rows"]}))


def prepare(args: argparse.Namespace, cases: dict[str, tuple[str, Path]]) -> int:
    started = time.time()
    if not args.skip_base:
        args.only = None
        code = s405.prepare(args, cases)
        if code:
            return code
    (owner_db, owner), (mixed_db, mixed) = cases["owner"], cases["mixed"]
    cut = add_history(owner, owner_db)
    api = Api(owner, owner_db, args.api_port)
    try:
        state = verify_owner(api, owner, cut)
    finally:
        api.stop()
    verify_closed(args.api_port, owner, owner_db)
    api = Api(mixed, mixed_db, args.api_port)
    try:
        verify_mixed(api)
    finally:
        api.stop()
    (owner / STATE).write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    say(f"prepare finished in {time.time() - started:.0f} s; {len(failures)} failed checks")
    if failures:
        say("STOPPED: the walkthrough does not promise what the served pages do not show. Failed checks:")
        for f in failures:
            say(f"  - {f}")
        return 1
    return 0


def links(args: argparse.Namespace, cases: dict[str, tuple[str, Path]]) -> int:
    db, work = cases["owner"]
    state = json.loads((work / STATE).read_text(encoding="utf-8"))
    web = f"http://localhost:{args.web_port}/sites/{SITE}"
    page = f"{web}/financials/assumptions"
    q = lambda **p: page + "?" + urllib.parse.urlencode(p)  # noqa: E731
    say(f"[owner] run `serve --case owner` (database {db}), then open:")
    say(f"  Default (a new moment each load; the address stays as is): {page}")
    for name, label in (("T1", "before the October price change"), ("T2", "after the October price change"),
                        ("T3", "after the part-way correction (newest P01 version unpriced)")):
        say(f"  Recorded at {name}, {label}: {q(recorded_at=state['cutoffs'][name])}")
    if state.get("next_cursor_T3"):
        say(f"  Second page at T3: {q(recorded_at=state['cutoffs']['T3'], history_after=state['next_cursor_T3'], history_limit=2)}")
    p = state["pick"]
    say(f"  A latest version's own Financials view: {web}/financials?finding_id={p['finding_id']}&revision_id="
        f"{p['finding_revision_id']}&consequence_revision_id={p['consequence_revision_id']}")
    say(f"  Its Finding: {web}/findings/{p['finding_id']}?revision_id={p['finding_revision_id']}")
    say("  Closed source: stop serve, run `close-gate`, serve again and reload the default address; then `open-gate`.")
    say(f"[mixed] run `serve --case mixed` (database {cases['mixed'][0]}), then open: {page}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/s408_assumption_history_walkthrough.py")
    parser.add_argument("command", choices=("prepare", "links", "serve", "close-gate", "open-gate", "drop"))
    parser.add_argument("--suffix", default="")
    parser.add_argument("--case", choices=CASES, default="owner")
    parser.add_argument("--skip-base", action="store_true", help="prepare: reuse already-built cases")
    parser.add_argument("--api-port", type=int, default=8968)
    parser.add_argument("--web-port", type=int, default=5468)
    parser.add_argument("--tls-port", type=int, default=8969)
    parser.add_argument("--http-port", type=int, default=8970)
    args = parser.parse_args(argv)
    if args.suffix and not args.suffix.replace("_", "").isalnum():
        raise SystemExit(f"Refusing suffix {args.suffix!r}: letters, digits and underscores only.")
    cases = names(args.suffix)
    var = (s2.REPO / "var").resolve()
    for db, work in cases.values():
        if not (db.startswith("assetops_s408") and db.replace("_", "").isalnum() and not db.endswith("_test")):
            raise SystemExit(f"Refusing database {db!r}: use a private assetops_s408* database.")
        if work.parent != var or not work.name.startswith("s408"):
            raise SystemExit(f"Refusing work folder {work}: use var/s408* in this repository.")
    if args.command == "drop":
        return s405.drop(cases)
    if args.command == "links":
        return links(args, cases)
    if args.command in ("close-gate", "open-gate"):
        s5.gate(cases["owner"][1], args.command == "close-gate")
        return 0
    if args.command == "serve":
        return s405.serve(SimpleNamespace(**{**vars(args)}), cases)
    return prepare(args, cases)


if __name__ == "__main__":
    raise SystemExit(main())
