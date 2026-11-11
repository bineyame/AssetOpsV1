"""DEMO-A U5 / DEMO-SPARSE U5: the Depot (EV-LAB-001) story days of the combined demo dataset, run by
`tools/demo_combined.py` as a child.

    python tools/demo_combined_ev.py build <database-url> <work>
    python tools/demo_combined_ev.py add-day <database-url> <work> <day-json>

Every EV entry of `<work>/days.json` is one registered replay of the W2-05b chain (`test_w205b_ev_replay_postgres`
`Chain`: Host stage -> gateway subprocess -> Batch V2 -> the EV worker), the `native_replay` body
(`tools/w504_ev_work_walkthrough.py:105-146`) on the day's window instead of 2026-10-06. No test module is edited;
this child swaps, in its own process only (the w601 module-swap pattern, `tools/w601_seed.py:529-545`):

- the w205b clock constants by the whole-day delta D - 2026-10-06 (`WINDOW`, `RELEASE`, `ATTEST_FROM/TO`,
  `FIRST/LATE_DECISION`, `ATTESTED_AT`), and `INSTALL_AT`/`SETUP_AT` to `ev.install_at` and +1 h (Addendum 1 R3).
  EV-HB (D-E5.48): `WINDOW` is the day's `story_window` (v4: the declared charging hours 08:00-16:00), and the
  clocks tied to its close (`RELEASE`, `FIRST/LATE_DECISION`, `ATTESTED_AT`) move with that close;
- `registered.RunSetupService` so `Chain.open`'s fixed `now` ("2026-10-06T07:00:00Z", w205b :261) reads `SETUP_AT`;
- `ev_parsing.EV_WINDOW` and an in-memory shifted copy of the kind's scenario document (`open(scenarios=,
  scenario_id=)`), since a Draft's interval must equal its scenario's (`runs/service.py:562-571`);
- `Chain.attest`'s one-epoch-per-Site assertion, re-checked for this day's epoch only (several days share the Site);
- the w504 `E_START`/`E_END` constants for the reads after the replay.

Work rows on the `fault` day only (DEMO-COMBINED U5): w504 `_declare` (`tools/w504_ev_work_walkthrough.py:214`,
mode `positive`: K0 over the day's E, the positive Action raised at its story instant and its intent), then `story.json` `ev`
`visits` (two completed "Connector inspection" visits) and `plans` ("Connector inspection", due S-6 d) through the
work service on the selected session's connector asset, the asset the CONNECTOR fault row names (CO-10/CO-11, R569).
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
from demo_combined import TARIFF_AFTER_INSTALL, at, iso
from demo_story_clock import story_commands, worker_instant

REPO = Path(__file__).resolve().parents[1]
SCENARIOS = REPO / "config" / "scenarios"
BASE_DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
#: WALK1-2 (WN-7, D-W1-1, R675): the Depot's declared charging tariff, published once by the SYSTEM publisher.
FIXTURE_TARIFF = REPO / "backend" / "conversions" / "demo-ev-tariff-publications.json"


def _shift_text(value: str, delta: timedelta) -> str:
    return iso(at(value) + delta)


def story_window(day: "sd.DayRun") -> tuple[datetime, datetime]:
    """EV-HB (D-E5.48): the one window an EV story day records, its day-list entry `[start, end)` (v4: the declared
    charging hours 08:00-16:00 of its Tuesday). The scenario window, the parser window (`ev_parsing.EV_WINDOW`), the
    w205b clocks and the w504 evidence window all take it from here. It opens where the registered scenario opens
    (the forcing is anchored there) and may only run longer."""
    delta = at(day.day + "T00:00:00Z") - BASE_DAY
    doc = yaml.safe_load((SCENARIOS / f"{day.scenario['scenario_id']}.yaml").read_text(encoding="utf-8"))
    opens, closes = at(doc["window"]["start"]) + delta, at(doc["window"]["end"]) + delta
    if day.start != opens or day.end is None or day.end < closes:
        raise SystemExit(f"EV day {day.day} {day.kind}: window {day.start}-{day.end} does not extend the registered "
                         f"{iso(opens)}-{iso(closes)}")
    return day.start, day.end


def story_definition(day: "sd.DayRun"):
    """The day's scenario definition on its `story_window`, parsed with `ev_parsing.EV_WINDOW` equal to that window
    for the call only."""
    from assetops_backend.scenarios import ev_parsing

    lo, hi = story_window(day)
    doc = shifted_document(day.scenario["scenario_id"], at(day.day + "T00:00:00Z") - BASE_DAY,
                           f"{day.scenario['scenario_id']}-{day.epoch}", window=(lo, hi))
    saved = ev_parsing.EV_WINDOW
    ev_parsing.EV_WINDOW = {**saved, "start": iso(lo), "end": iso(hi)}
    try:
        return ev_parsing.parse_ev_scenario_document(doc)
    finally:
        ev_parsing.EV_WINDOW = saved


def shifted_document(scenario_id: str, delta: timedelta, new_id: str,
                     window: tuple[datetime, datetime] | None = None) -> dict:
    """The registered scenario document moved by whole days: window, forcing and observation instants only.
    EV-HB: `window` (the day's `story_window`) replaces the moved window; forcing and observations only move."""
    doc = yaml.safe_load((SCENARIOS / f"{scenario_id}.yaml").read_text(encoding="utf-8"))
    out = copy.deepcopy(doc)
    out["scenario_id"] = new_id
    out["window"] = {**doc["window"], "start": _shift_text(doc["window"]["start"], delta),
                     "end": _shift_text(doc["window"]["end"], delta)}
    if window is not None:
        out["window"].update({"start": iso(window[0]), "end": iso(window[1])})
    for entry in out.get("forcing") or []:
        entry["time"] = _shift_text(entry["time"], delta)
    for entry in out.get("observations") or []:
        for key in ("time", "release_at"):
            if entry.get(key):
                entry[key] = _shift_text(entry[key], delta)
    return out


def _swaps(registered, P, day: "sd.DayRun", install_at: datetime) -> dict:
    """Move the w205b/w504 constants onto `day`; returns the saved values for `_restore`. EV-HB: the window is the
    day's `story_window`; the clocks tied to the window's close (the first and late decisions, the late release and
    the attestation instant) move with its close, by `longer` = how much later it closes than the registered hour."""
    from assetops_backend.scenarios import ev_parsing

    delta = at(day.day + "T00:00:00Z") - BASE_DAY
    lo, hi = story_window(day)
    names = ("INSTALL_AT", "SETUP_AT", "WINDOW", "RELEASE", "ATTEST_FROM", "ATTEST_TO", "FIRST_DECISION",
             "LATE_DECISION", "ATTESTED_AT")
    saved = {n: getattr(registered, n) for n in names}
    saved.update({"_EV_WINDOW": ev_parsing.EV_WINDOW, "_E": (P.E_START, P.E_END),
                  "_RunSetupService": registered.RunSetupService})
    longer = hi - (at(saved["WINDOW"]["end"]) + delta)
    registered.INSTALL_AT, registered.SETUP_AT = install_at, install_at + timedelta(hours=1)
    registered.WINDOW = {**saved["WINDOW"], "start": iso(lo), "end": iso(hi)}
    registered.RELEASE = _shift_text(saved["RELEASE"], delta + longer)
    for n in ("ATTEST_FROM", "ATTEST_TO"):
        setattr(registered, n, saved[n] + delta)
    for n in ("FIRST_DECISION", "LATE_DECISION", "ATTESTED_AT"):
        setattr(registered, n, saved[n] + delta + longer)
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


def write_work(url: str, built, story: dict, asset_id: str, tag: str, shift: timedelta = timedelta(0)) -> dict:
    """The fault day's connector visits and plan (`story.json` `ev`), the Kobo child's `write_work` pattern.
    `shift` is the fault day's move back to the ruled Tuesday (`demo_story_days.SITE_WEEKDAY`): the story's S-relative
    instants move with it, so the visits and the plan keep their places before the fault."""
    from test_w401_work_service_postgres import PRINCIPAL, event, plan, record, request
    from assetops_backend.work.composition import build_work_service

    e = story["ev"]
    tenant, site = built.tenant_id, built.site_id
    work = build_work_service(url)
    out = {"asset_id": asset_id, "visits": [], "plans": []}
    try:
        for v in e["visits"]:
            when, key = at(v["at"]) + shift, f"demo3-ev-{v['key']}-{tag}"
            # POLISH §3 "Request narratives": the request's own title as a sentence, not the test default.
            s, case = work.create_case(tenant, site, request(key, title=v["title"], narrative=f"{v['title']}.",
                                                             occurred_at=iso(when), asset_id=asset_id,
                                                             finding_links=[]), PRINCIPAL)
            assert s == 201, (v["key"], s, case)
            s, rec = work.post_record(tenant, site, case["id"], record(
                f"{key}-rec", activity=v["title"], occurred_at=iso(when + timedelta(minutes=20)),
                outcome_note=v["note"]), PRINCIPAL)
            assert s == 201, (v["key"], s, rec)
            s, a = work.post_event(tenant, site, case["id"], event(
                "ASSIGN", {"assignee": "Charging technician"}, f"{key}-assign",
                occurred_at=iso(when + timedelta(minutes=21))), PRINCIPAL)
            assert s == 201, (v["key"], s, a)
            s, c = work.post_event(tenant, site, case["id"], event(
                "COMPLETE", {"maintenance_record_id": rec["id"]}, f"{key}-complete",
                occurred_at=iso(when + timedelta(minutes=22))), PRINCIPAL)
            assert s == 201 and c["state"] == "COMPLETED", (v["key"], s, c)
            out["visits"].append({"key": v["key"], "id": case["id"], "code": case.get("code"),
                                  "record_id": rec["id"], "occurred_at": iso(when)})
        for p in e["plans"]:
            p = {**p, "at": iso(at(p["at"]) + shift),
                 "due_at": None if p["due_at"] is None else iso(at(p["due_at"]) + shift)}
            s, pl = work.post_plan(tenant, site, plan(
                f"demo3-ev-{p['key']}-{tag}", asset_id=asset_id, title=p["title"], trigger_kind=p["trigger_kind"],
                next_due_at=p["due_at"], next_due_hours=p["due_hours"], occurred_at=p["at"]), PRINCIPAL)
            assert s == 201, (p["key"], s, pl)
            out["plans"].append({"key": p["key"], "id": str(pl.get("canonical_plan_id") or pl.get("id")),
                                 "title": p["title"], "due_at": p["due_at"]})
    finally:
        work._store.dispose()
    return out


def declare_and_work(url: str, built, story: dict, day: "sd.DayRun", replayed: dict) -> dict:
    """The fault day's w504 positive Action + intent, then the connector visits and plan on its connector, all on the
    story clocks (`demo_story_clock`, DD1b1-R Q2). `_db_now` reads the domain clock, so its first read is the Action's
    instant."""
    import w504_ev_work_walkthrough as W

    tag = f"demo3-{day.epoch}"
    with story_commands(url, day.received_at) as (_work, domain):
        saved = W._db_now
        W._db_now = lambda _url: domain()
        try:
            declared = W._declare(url, "positive", tag, replayed)
        finally:
            W._db_now = saved
        asset_id = declared["selection"]["connector_asset_id"]
        if not asset_id:
            raise SystemExit("EV fault day: the selected session names no connector asset; no plan target")
        visits = write_work(url, built, story, asset_id, tag, timedelta(days=day.offset))
    # POLISH §1.3 (P-08): the API returns `action_code`/`intent_id`; record them and the Action's own `raised_at` as
    # posted. DD1b1-R2: story-dated after the evidence, so the Depot's whole-UTC-day board lists it under "in hand"
    # (closes R645: DD1b1-R3 re-probe passed); the exact event-window board does not (BL-38). The create
    # response carries no `raised_at`, so it is the posted body's.
    return {"action": {"id": declared["action"]["id"], "code": declared["action"]["action_code"],
                       "raised_at": declared["action_posted"]["raised_at"]},
            "intent_id": declared["intent"]["intent_id"],
            "finding_id": declared["selection"]["finding_id"],
            "finding_revision_id": declared["selection"]["finding_revision_id"],
            "work": visits}


#: POLISH §3 "Lab Site names" (D-5, R646): the demo build's Depot name, the mock's; the fixture YAML keeps its own.
DISPLAY_NAME = "Depot Charging Hub"


def _install(registered):
    """The chain's install (the reviewed `install_ev_lab` at the swapped `INSTALL_AT`) with the demo display name."""
    from test_s1_bindings_postgres import Clock
    from assetops_backend.sites.ev_lab import install_ev_lab

    return lambda store: install_ev_lab(store, tenant_slug="demo", clock=Clock(registered.INSTALL_AT),
                                        display_name=DISPLAY_NAME)


def run_day(url: str, tmp: Path, day: "sd.DayRun", install_at: datetime, story: dict | None = None,
            story_clock: bool = False) -> dict:
    """One EV story day: the registered replay on the day's window (the `native_replay` body). `story_clock` (prepare
    only, DD1b1-R Q1): the worker and `select_exact` run at `received_at` + 5 min; add-day stays on wall time."""
    from collections import Counter

    os.environ["DATABASE_URL"] = os.environ["ASSETOPS_TEST_DATABASE_URL"] = url
    import test_w205b_ev_replay_postgres as registered
    import test_w206_ev_store_postgres as w206
    import w504_ev_work_cases as P

    registered.SEAL_ONCE = True  # DD0c-R Q1: L1 batching, the demo prepare / add-day producers only
    from run_fixtures import FakeScenarios
    from test_w206_ev_store_postgres import run_worker, select_exact
    from assetops_backend.analytics.composition import build_ev_assessment_worker

    clock = None
    if story_clock:
        worker_at = worker_instant(url, day.received_at)
        clock = lambda: worker_at  # noqa: E731

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
    saved_worker = w206.build_ev_assessment_worker
    if clock is not None:  # `select_exact` builds its own worker through this name
        w206.build_ev_assessment_worker = lambda u, **kw: saved_worker(u, clock=clock, **kw)
    try:
        definition = story_definition(day)  # EV-HB: the day's recorded window (`story_window`)
        assert definition.scenario_id == scenario_id, (definition.scenario_id, scenario_id)
        built = DayChain(case, tmp / f"{day.day}-{day.kind}")
        try:
            built.open(fresh=False, install=_install(registered), scenarios=FakeScenarios((definition,)),
                       scenario_id=scenario_id)
            built.start_release_upload()
            if clock is None:
                outcomes = run_worker(built)
            else:
                worker = build_ev_assessment_worker(url, clock=clock)
                try:
                    outcomes = run_worker(built, worker)
                finally:
                    w206._dispose(worker)
            select_exact(built, P.E_START, P.E_END)
            decisions = Counter(d[1] for b in built.batches() for d in b["dispositions"])
            assert decisions.get("ACCEPTED"), dict(decisions)
            got = {"run_id": str(built.run.run_id), "scenario_id": scenario_id, "case": case,
                   "evidence_window": {"from": iso(P.E_START), "to": iso(P.E_END)},
                   "dispositions": dict(decisions), "worker_outcomes": len(outcomes)}
            if day.kind == "fault" and story is not None:
                got["fault_day"] = declare_and_work(url, built, story, day, dict(got))
            return got
        finally:
            built.close()
    finally:
        w206.build_ev_assessment_worker = saved_worker
        _restore(registered, P, saved)


def publish_tariff(url: str, recorded_at: datetime, site_code: str = "EV-LAB-001") -> dict:
    """WALK1-2 §3.1: publish the demo charging tariff step v1 (`demo_combined_kobo.publish_price`'s pattern). The
    fixture's idempotency key makes a second call a replay, never a second revision. The EV money recompute is
    enqueued by the 0026 trigger and drained by the scheduled ticks. Returns the publisher's JSON line."""
    import contextlib
    import io

    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.publish_assumption import main as publish
    import pg_harness

    store = PostgresAssumptionStore(url, test_recorded_clock_override=lambda: recorded_at)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            code = publish(["fixture", "--site", site_code, "--file", str(FIXTURE_TARIFF), "--step", "v1"],
                           store=store)
    finally:
        pg_harness.dispose(store)
    if code != 0:
        raise SystemExit(f"charging tariff v1 publication failed ({code})")
    line = next(x for x in out.getvalue().splitlines() if x.startswith("{"))
    print(line, flush=True)
    return json.loads(line)


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
            entry.update(run_day(url, tmp, day, install_at, story, story_clock=True))
        entry["status_after_build"] = "ASSESSED" if day.has_run else "NO_RUN"
        records.append(entry)
        print("ev day", day.day, day.kind, entry.get("run_id"), flush=True)
    doc = {"site_code": e["site_code"], "install_at": e["install_at"], "days": records}
    if any(r["run_id"] for r in records):  # the Site exists only once a day's replay has installed it
        doc["tariff"] = publish_tariff(url, install_at + TARIFF_AFTER_INSTALL, e["site_code"])
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
