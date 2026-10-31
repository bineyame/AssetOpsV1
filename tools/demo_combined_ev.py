"""DEMO-A U5 / DEMO-SPARSE U5: the Depot (EV-LAB-001) story days of the combined demo dataset, run by
`tools/demo_combined.py` as a child.

    python tools/demo_combined_ev.py build <database-url> <work>
    python tools/demo_combined_ev.py add-day <database-url> <work> <day-json>

Every EV entry of `<work>/days.json` is one registered replay of the W2-05b chain (`test_w205b_ev_replay_postgres`
`Chain`: Host stage -> gateway subprocess -> Batch V2 -> the EV worker), the `native_replay` body
(`tools/w504_ev_work_walkthrough.py:105-146`) on the day's window instead of 2026-10-06. No test module is edited;
this child swaps, in its own process only (the w601 module-swap pattern, `tools/w601_seed.py:529-545`):

- the w205b clock constants by the whole-day delta D - 2026-10-06 (`WINDOW`, `RELEASE`, `ATTEST_FROM/TO`,
  `FIRST/LATE_DECISION`, `ATTESTED_AT`), and `INSTALL_AT`/`SETUP_AT` to `ev.install_at` and +1 h (Addendum 1 R3);
- `registered.RunSetupService` so `Chain.open`'s fixed `now` ("2026-10-06T07:00:00Z", w205b :261) reads `SETUP_AT`;
- `ev_parsing.EV_WINDOW` and an in-memory shifted copy of the kind's scenario document (`open(scenarios=,
  scenario_id=)`), since a Draft's interval must equal its scenario's (`runs/service.py:562-571`);
- `Chain.attest`'s one-epoch-per-Site assertion, re-checked for this day's epoch only (several days share the Site);
- the w504 `E_START`/`E_END` constants for the reads after the replay.

Work rows on the `fault` day (w504 `_declare`, connector visits and plan from `story.json` `ev`): see the phase
handoff; not wired yet.
"""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

import demo_story_days as sd
from demo_combined import at, iso

REPO = Path(__file__).resolve().parents[1]
SCENARIOS = REPO / "config" / "scenarios"
BASE_DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)


def _shift_text(value: str, delta: timedelta) -> str:
    return iso(at(value) + delta)


def shifted_document(scenario_id: str, delta: timedelta, new_id: str) -> dict:
    """The registered scenario document moved by whole days: window, forcing and observation instants only."""
    doc = yaml.safe_load((SCENARIOS / f"{scenario_id}.yaml").read_text(encoding="utf-8"))
    out = copy.deepcopy(doc)
    out["scenario_id"] = new_id
    out["window"] = {**doc["window"], "start": _shift_text(doc["window"]["start"], delta),
                     "end": _shift_text(doc["window"]["end"], delta)}
    for entry in out.get("forcing") or []:
        entry["time"] = _shift_text(entry["time"], delta)
    for entry in out.get("observations") or []:
        for key in ("time", "release_at"):
            if entry.get(key):
                entry[key] = _shift_text(entry[key], delta)
    return out


def _swaps(registered, P, day: "sd.DayRun", install_at: datetime) -> dict:
    """Move the w205b/w504 constants onto `day`; returns the saved values for `_restore`."""
    from assetops_backend.scenarios import ev_parsing

    delta = at(day.day + "T00:00:00Z") - BASE_DAY
    names = ("INSTALL_AT", "SETUP_AT", "WINDOW", "RELEASE", "ATTEST_FROM", "ATTEST_TO", "FIRST_DECISION",
             "LATE_DECISION", "ATTESTED_AT")
    saved = {n: getattr(registered, n) for n in names}
    saved.update({"_EV_WINDOW": ev_parsing.EV_WINDOW, "_E": (P.E_START, P.E_END),
                  "_RunSetupService": registered.RunSetupService})
    registered.INSTALL_AT, registered.SETUP_AT = install_at, install_at + timedelta(hours=1)
    registered.WINDOW = {**saved["WINDOW"], "start": _shift_text(saved["WINDOW"]["start"], delta),
                         "end": _shift_text(saved["WINDOW"]["end"], delta)}
    registered.RELEASE = _shift_text(saved["RELEASE"], delta)
    for n in ("ATTEST_FROM", "ATTEST_TO", "FIRST_DECISION", "LATE_DECISION", "ATTESTED_AT"):
        setattr(registered, n, saved[n] + delta)
    ev_parsing.EV_WINDOW = {**ev_parsing.EV_WINDOW, "start": registered.WINDOW["start"],
                            "end": registered.WINDOW["end"]}
    P.E_START, P.E_END = at(registered.WINDOW["start"]), at(registered.WINDOW["end"])
    setup_text = iso(registered.SETUP_AT)
    original = saved["_RunSetupService"]
    registered.RunSetupService = lambda *a, now=None, **kw: original(*a, now=lambda: setup_text, **kw)
    return saved


def _restore(registered, P, saved: dict) -> None:
    from assetops_backend.scenarios import ev_parsing

    for n, v in saved.items():
        if not n.startswith("_"):
            setattr(registered, n, v)
    ev_parsing.EV_WINDOW = saved["_EV_WINDOW"]
    P.E_START, P.E_END = saved["_E"]
    registered.RunSetupService = saved["_RunSetupService"]


def run_day(url: str, tmp: Path, day: "sd.DayRun", install_at: datetime) -> dict:
    """One EV story day: the registered replay on the day's window (the `native_replay` body)."""
    from collections import Counter

    os.environ["DATABASE_URL"] = os.environ["ASSETOPS_TEST_DATABASE_URL"] = url
    import test_w205b_ev_replay_postgres as registered
    import w504_ev_work_cases as P
    from run_fixtures import FakeScenarios
    from test_w206_ev_store_postgres import run_worker, select_exact
    from assetops_backend.scenarios.ev_parsing import parse_ev_scenario_document

    base_id = day.scenario["scenario_id"]
    case = f"{base_id.removeprefix('ev-')}-{day.epoch}"  # unique gateway epoch `ev-<case>` per story day
    scenario_id = f"{base_id}-{day.epoch}"

    class DayChain(registered.Chain):
        def attest(self) -> None:
            try:
                super().attest()
            except AssertionError:  # earlier story days' attestations share the Site; check this epoch only
                from sqlalchemy import text

                with self.engine.connect() as c:
                    mine = c.execute(text("SELECT count(*) FROM source_clock_attestation WHERE site_id = :s AND "
                                          "sequence_epoch = :e"), {"s": self.site_id, "e": f"ev-{self.case}"})
                    sources = c.execute(text("SELECT count(*) FROM source s JOIN gateway g ON g.id = s.gateway_id "
                                             "WHERE g.site_id = :s"), {"s": self.site_id})
                    assert mine.scalar_one() == sources.scalar_one() > 0

    saved = _swaps(registered, P, day, install_at)
    try:
        definition = parse_ev_scenario_document(shifted_document(base_id, at(day.day + "T00:00:00Z") - BASE_DAY,
                                                                 scenario_id))
        built = DayChain(case, tmp / f"{day.day}-{day.kind}")
        try:
            built.open(fresh=False, scenarios=FakeScenarios((definition,)), scenario_id=scenario_id)
            built.start_release_upload()
            outcomes = run_worker(built)
            select_exact(built, P.E_START, P.E_END)
            decisions = Counter(d[1] for b in built.batches() for d in b["dispositions"])
            assert decisions.get("ACCEPTED"), dict(decisions)
            return {"run_id": str(built.run.run_id), "scenario_id": scenario_id, "case": case,
                    "evidence_window": {"from": iso(P.E_START), "to": iso(P.E_END)},
                    "dispositions": dict(decisions), "worker_outcomes": len(outcomes)}
        finally:
            built.close()
    finally:
        _restore(registered, P, saved)


def build(url: str, work: Path, story: dict) -> dict:
    days = [d for d in sd.from_payload(json.loads((work / "days.json").read_text(encoding="utf-8"))["days"])
            if d.site == "ev"]
    e = story["ev"]
    install_at = at(e["install_at"])
    tmp = Path(tempfile.mkdtemp(prefix="ev-replay-", dir=str(work)))
    records = []
    for day in days:
        entry = {"day": day.day, "offset": day.offset, "kind": day.kind, "scenario": day.scenario,
                 "epoch": day.epoch, "received_at": iso(day.received_at) if day.received_at else None,
                 "run_id": None}
        if day.has_run:
            entry.update(run_day(url, tmp, day, install_at))
        entry["status_after_build"] = "ASSESSED" if day.has_run else "NO_RUN"
        records.append(entry)
        print("ev day", day.day, day.kind, entry.get("run_id"), flush=True)
    doc = {"site_code": e["site_code"], "install_at": e["install_at"], "days": records}
    (work / "ev.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    print("ev:", len([r for r in records if r["run_id"]]), "runs")
    return doc


def add_day(url: str, work: Path, planned: dict) -> dict:
    day = sd.from_payload([planned])[0]
    story = json.loads((work / "story.json").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp(prefix="ev-add-day-", dir=str(work)))
    out = run_day(url, tmp, day, at(story["ev"]["install_at"]))
    print(json.dumps({"added": day.day, "kind": day.kind, "run_id": out.get("run_id"), "findings": []}))
    return out


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "add-day":
        add_day(sys.argv[2], Path(sys.argv[3]), json.loads(sys.argv[4]))
        raise SystemExit(0)
    if len(sys.argv) != 4 or sys.argv[1] != "build":
        raise SystemExit("usage: demo_combined_ev.py build|add-day <database-url> <work> [<day-json>]")
    work_dir = Path(sys.argv[3])
    build(sys.argv[2], work_dir, json.loads((work_dir / "story.json").read_text(encoding="utf-8")))
