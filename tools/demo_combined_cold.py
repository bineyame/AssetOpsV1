"""DEMO-A U4 / DEMO-SPARSE U5: the GreenHarvest (COLD-LAB-001) story days of the combined demo dataset, run by
`tools/demo_combined.py` as a child.

    python tools/demo_combined_cold.py build <database-url> <work>
    python tools/demo_combined_cold.py add-day <database-url> <work> <day-json>

Every cold entry of `<work>/days.json` is one shifted replay of the W2-02 chain (`test_w502_cold_scenario_producer`
`ShiftedChain`): registered Lab run -> real gateway process -> Batch V2 acceptance -> the cold worker. The
`failure` day runs the w502 `positive` BUILD body (`tools/w502_cold_work_walkthrough.py` `BUILD`: Finding, Action,
Incident, work request and its completion, OUT-C visits and plans); `normal` and `degraded` days are the replay
alone (no work rows). No test module is edited; this child swaps, in its own process only:

- `pg_harness.fresh_database` -> no-op (the chain must not wipe the Kobo rows already in the database);
- `producer.target_delta` -> the day's 16:00 start; `producer.BASE_SCENARIO` -> the kind's registered scenario;
- `producer.shifted_case` -> always the `ordinary` mode, while the chain's `case` carries the day's unique epoch
  (gateway epoch `cold-ordinary-day-<n>`, attestation keys), so several days share one Site;
- the w202 Batch V2 ingestion clock -> the day's `received_at` (D 17:05) instead of wall time;
- `ShiftedChain.attest`'s recording instant (`datetime.now`) -> the day's setup instant (start - 1 h): with the
  knowledge cutoff at `received_at`, an attestation recorded at wall time is not yet known, so every reading
  would be excluded `CLOCK_UNATTESTED` and no Finding written (first dev prepare, 2026-10-31);
- in a prepare only (`demo_story_clock`, DD1b1-R Q1, Q2), the worker and the failure day's work and Action commands.

The Site is installed once at `cold.install_at` (S-26d 06:00); each later `install_cold_lab` is idempotent.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import demo_story_days as sd
from demo_combined import at, iso
from demo_story_clock import story_commands, worker_instant

REPO = Path(__file__).resolve().parents[1]
SCENARIOS = REPO / "config" / "scenarios"
#: DD0c-R Q1: the demo child seals each run once (L1 batching); the parity test flips it off.
SEAL_ONCE = True


def _patch(url: str):
    """The process-local swaps listed in the module docstring; returns the producer test module."""
    os.environ["DATABASE_URL"] = os.environ["ASSETOPS_TEST_DATABASE_URL"] = url
    import pg_harness
    import test_w202_cold_replay_postgres as w202
    import test_w502_cold_scenario_producer as P

    pg_harness.fresh_database = lambda *a, **k: url
    P.SEAL_ONCE = SEAL_ONCE  # DD0c-R Q1: L1 batching, the demo prepare / add-day producers only
    producer = P.producer
    original = getattr(producer, "_demo_original_shifted_case", producer.shifted_case)
    producer._demo_original_shifted_case = original
    producer.shifted_case = lambda r, mode, tag: original(r, "ordinary", tag)
    base = getattr(P, "_demo_base_chain", P.ShiftedChain)
    P._demo_base_chain = base
    return P, w202, base


#: DD1a1-R5: the epochs (Site-days) already attested in this process.
_ATTESTED: set[str] = set()


def _day_swaps(P, w202, base, day: "sd.DayRun", tmp: Path):
    """Point the shifted chain at one story day; returns the chain factory BUILD and `produce` call."""
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService

    producer = P.producer
    # DD1a1-R5: one gateway state per Site-day (sequence continues across its runs); a complement sends only
    # the source instants `keep` allows.
    w202.GATEWAY_STATE = tmp / f"gw-{day.epoch}"
    P.KEEP = day.keep()
    producer.BASE_SCENARIO = SCENARIOS / f"{day.scenario['scenario_id']}.yaml"
    producer.target_delta = lambda _now, start=day.start: start - producer.BASE_START
    received = day.received_at
    w202.PostgresEvidenceLedger = lambda u, **kw: PostgresEvidenceLedger(
        u, **{"test_decision_clock_override": lambda: received, **kw})
    w202.BatchIngestionService = lambda ledger, _clock: BatchIngestionService(ledger, lambda: received)
    w202.DIAGNOSTIC_CLOCK = lambda: received  # DATA-5: the day's gateway diagnostics are stored (Cold Health)
    recorded = day.start - timedelta(hours=1)

    class _RecordedNow(datetime):
        @classmethod
        def now(cls, tz=None):
            return recorded.astimezone(tz or timezone.utc)

    class DayChain(base):
        def attest(self) -> None:
            # DD1a1-R5: attest once per Site-day (the day's first run; its window spans the whole day), the
            # later runs of that day share the epoch and the attestation keys.
            if day.epoch in _ATTESTED:
                return
            _ATTESTED.add(day.epoch)
            saved, P.datetime = P.datetime, _RecordedNow
            try:
                super().attest()
            finally:
                P.datetime = saved

    P.ShiftedChain = lambda m, tmp: DayChain(f"{m}-{day.epoch}", tmp)
    return P.ShiftedChain


#: POLISH §3 "Lab Site names" (D-5, R646): the demo build's GreenHarvest name, the mock's; the fixture YAML keeps its own.
DISPLAY_NAME = "GreenHarvest Cold Room"


def install(url: str, install_at) -> None:
    from test_s1_bindings_postgres import Clock
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.cold_lab import install_cold_lab
    import pg_harness

    store = PostgresFoundationStore(url)
    try:
        install_cold_lab(store, tenant_slug="demo", clock=Clock(install_at), display_name=DISPLAY_NAME)
    finally:
        pg_harness.dispose(store)


def _refuse_enqueue_window(_built) -> None:
    """DD1b1-R Q1: this job's `available_at` is `now()`, so a story clock would never lease it. Stop, do not patch."""
    raise SystemExit("STORY_CLOCK_WINDOW: a built Cold day needs `enqueue_window`, which a story-clock worker never leases.")


def _failure_day(url: str, out: Path, day: "sd.DayRun", story_clock: bool) -> dict:
    """The w502 positive BUILD body; on the story clock (DD1b1-R Q2) its cases, Action, links and intent are story-dated."""
    import w502_cold_work_walkthrough as W

    # POLISH Addendum 9 Q2: the demo build passes each request title as its narrative; standalone w502 does not.
    ns = {"__name__": "__w502_build__", "DEMO_NARRATIVES": True}

    def build() -> None:
        argv = sys.argv
        sys.argv = ["w502-build", "positive", str(out)]
        try:
            exec(compile(W.BUILD, "w502_cold_work_walkthrough.BUILD", "exec"), ns)
        finally:
            sys.argv = argv

    if story_clock:
        import test_w502_domain_intent_postgres as intent

        with story_commands(url, day.received_at) as (_work, domain):
            ns["DEMO_ACTION_AT"] = domain.start
            saved = intent.now_utc
            intent.now_utc = lambda _engine: domain()
            try:
                build()
            finally:
                intent.now_utc = saved
    else:
        build()
    doc = json.loads((out / "positive.json").read_text(encoding="utf-8"))
    if story_clock and doc.get("blocked"):
        raise SystemExit(f"STORY_CLOCK_BLOCKED: the Cold failure day is blocked: {doc['blocked']}")
    return {"run_id": str(getattr(ns["built"].run, "run_id", "")), "scenario_id": doc.get("scenario_id"), "work": doc.get("out_c"),
            "blocked": doc.get("blocked")}


def run_day(url: str, tmp: Path, day: "sd.DayRun", story_clock: bool = False) -> dict:
    """One cold story day. `failure` runs the w502 positive BUILD body; other kinds the replay only. `story_clock`
    (prepare only, DD1b1-R Q1): the worker runs at `received_at` + 5 min; add-day stays on wall time."""
    P, w202, base = _patch(url)
    factory = _day_swaps(P, w202, base, day, tmp)
    out = tmp / f"{day.day}-{day.kind}-{day.start:%H%M}"  # DD-1a1: 24 runs per full day
    out.mkdir(parents=True)
    saved = P.run, P.enqueue_window
    if story_clock:
        import test_w203_cold_replay_postgres as w203

        worker_at = worker_instant(url, day.received_at)
        P.run = lambda built: w203.run(built, clock=lambda: worker_at)
        P.enqueue_window = _refuse_enqueue_window
    try:
        if day.kind == "failure":
            return _failure_day(url, out, day, story_clock)
        built = P.produce(lambda m: factory(m, out / "chain").open(), "ordinary")
        try:
            return {"run_id": str(getattr(built.run, "run_id", "")), "scenario_id": built.shifted.scenario_id}
        finally:
            built.close()
    finally:
        P.run, P.enqueue_window = saved


def findings_on(url: str, day: str) -> list[str]:
    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    lo = at(day + "T00:00:00Z")
    try:
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT DISTINCT f.finding_id FROM finding_revision f JOIN site s ON s.id = f.site_id "
                "WHERE s.site_code = 'COLD-LAB-001' AND f.episode_start < :hi "
                "AND (f.episode_end IS NULL OR f.episode_end > :lo) ORDER BY f.finding_id"), {"lo": lo, "hi": lo + timedelta(days=1)}).fetchall()
    finally:
        engine.dispose()
    return [str(r[0]) for r in rows]


def build(url: str, work: Path, story: dict) -> dict:
    days = [d for d in sd.from_payload(json.loads((work / "days.json").read_text(encoding="utf-8"))["days"])
            if d.site == "cold"]
    c = story["cold"]
    install(url, at(c["install_at"]))
    tmp = Path(tempfile.mkdtemp(prefix="cold-replay-", dir=str(work)))
    records = []
    for day in days:
        entry = {"day": day.day, "offset": day.offset, "kind": day.kind, "scenario": day.scenario,
                 "epoch": day.epoch, "assess": day.assess,
                 "received_at": iso(day.received_at) if day.received_at else None, "run_id": None}
        if day.has_run:
            entry.update(run_day(url, tmp, day, story_clock=True))
        entry["findings"] = findings_on(url, day.day)
        entry["status_after_build"] = "NO_RUN" if not day.has_run else "ASSESSED"
        records.append(entry)
        print("cold day", day.day, day.kind, entry.get("run_id"), len(entry["findings"]), "findings", flush=True)
    doc = {"site_code": c["site_code"], "install_at": c["install_at"], "days": records}
    (work / "cold.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    print("cold:", len([r for r in records if r["run_id"]]), "runs;",
          sum(len(r["findings"]) for r in records), "findings")
    return doc


def add_day(url: str, work: Path, planned: dict) -> dict:
    """`demo_combined.py add-day` for COLD-LAB-001: one replay on a free day, delivered at the DB now the parent
    read (`received_at`). The cold worker runs in the replay, so the day is assessed when this returns."""
    day = sd.from_payload([planned])[0]
    tmp = Path(tempfile.mkdtemp(prefix="cold-add-day-", dir=str(work)))
    out = run_day(url, tmp, day)
    out["findings"] = findings_on(url, day.day)
    print(json.dumps({"added": day.day, "kind": day.kind, "run_id": out.get("run_id"), "findings": out["findings"]}))
    return out


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "add-day":
        add_day(sys.argv[2], Path(sys.argv[3]), json.loads(sys.argv[4]))
        raise SystemExit(0)
    if len(sys.argv) != 4 or sys.argv[1] != "build":
        raise SystemExit("usage: demo_combined_cold.py build|add-day <database-url> <work> [<day-json>]")
    work_dir = Path(sys.argv[3])
    build(sys.argv[2], work_dir, json.loads((work_dir / "story.json").read_text(encoding="utf-8")))
