"""MD-0: the mechanism test dataset (build sheet `.agent/build-sheet-MD-0.md`, rulings §1 MD0-R and §14 MD0-PF).

Phase 1 (this file so far): the fixture loader with its schema rules (§2.1), the `MECHANISM_DB_ONLY` database
guard (R2, D-AW-1), the Dn date map and the `late_fill` declared-gap refusal (§4). Seeding (`seed_database`),
`late_fill`'s write path and `build_work` follow in later phases (`.agent/MD-0-phase-1-handoff.md`).

Inputs only: the fixture never carries an expected output (R3). Every write goes through an existing writer at its
story time (R1, R4); no snapshot, thread or study row is ever inserted directly and no row is UPDATEd.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

FIXTURE = Path(__file__).resolve().parents[1] / "conversions" / "mechanism-v1.json"
FIXTURE_ID, FIXTURE_VERSION = "assetops.mechanism-dataset", "1"
DAY_SETS = ("full", "states")

#: R2 / D-AW-1: the only databases MD-0 may seed or fill. The pg_harness worker pattern is
#: `<stem>_pt<run>_<tag>_test` (`pg_harness.database_name`).
MECHANISM_DB_RE = re.compile(r"^assetops_mechanism(_close)?_test$")
WORKER_DB_RE = re.compile(r"^[a-z0-9_]+_pt[0-9a-z]+_(main|tpl|gw[0-9]+)_test$")
ALWAYS_REFUSED_RE = re.compile(r"^assetops_(polish|demo)")
PROTECTED = ("assetops_polish_full_test", "assetops_demo3_full_test")  # B/chain/backfill.py:29

OUTPUT_KEYS = {"grade", "state", "status", "eligible_days", "minutes"}
OUTCOME_ID_RE = re.compile(r"\b(MG|CC|EV)-\d")


class MechanismRefused(ValueError):
    """A refused MD-0 request; `str(error)` is the code (`MECHANISM_DB_ONLY`, `DAY_HAS_EVIDENCE`, ...)."""


def mechanism_db_allowed(name: str) -> bool:
    """Pure: may MD-0 write into the database called `name`? Polish, demo and protected DBs are always refused."""
    if name in PROTECTED or ALWAYS_REFUSED_RE.match(name):
        return False
    return bool(MECHANISM_DB_RE.match(name) or WORKER_DB_RE.match(name))


def require_mechanism_db(engine) -> str:
    """Reads `current_database()` and raises `MechanismRefused("MECHANISM_DB_ONLY")` unless it is allowed."""
    from sqlalchemy import text

    with engine.connect() as c:
        name = c.execute(text("SELECT current_database()")).scalar_one()
    if not mechanism_db_allowed(name):
        raise MechanismRefused("MECHANISM_DB_ONLY")
    return name


# --- the fixture ---------------------------------------------------------------------------------------------


def day(spec: dict, n: int) -> date:
    """Dn = day_zero + n (D1 Mon 19 Oct 2026 ... D14 Sun 1 Nov 2026)."""
    return date.fromisoformat(spec["story"]["day_zero"]) + timedelta(days=n)


def local_instant(spec: dict, site: str, n: int, hhmm: str) -> datetime:
    """Site-local Dn at HH:MM ("24:00" is the next midnight), as a UTC instant."""
    tz = ZoneInfo(spec["sites"][site]["time_zone"])
    h, m = (int(x) for x in hhmm.split(":"))
    base = datetime.combine(day(spec, n), datetime.min.time(), tzinfo=tz)
    return (base + timedelta(hours=h, minutes=m)).astimezone(timezone.utc)


def _walk(node: Any, path: str = ""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")


def validate(spec: dict) -> None:
    """The §2.1 L0 schema rules; raises `ValueError` naming the first broken rule."""
    if spec.get("schema") != {"id": FIXTURE_ID, "version": int(FIXTURE_VERSION)}:
        raise ValueError("schema: not assetops.mechanism-dataset v1")
    text_ = json.dumps(spec)
    if OUTCOME_ID_RE.search(text_):
        raise ValueError("outcome id in the fixture (OL-1)")
    for path, key, _ in _walk(spec):
        if key in OUTPUT_KEYS:
            raise ValueError(f"output key {key!r} at {path}")
    for where, value in _value_nodes(spec):
        if "source" not in value:
            raise ValueError(f"no source at {where}")
    if set(spec["day_sets"]) != set(DAY_SETS):
        raise ValueError("day_sets must be full and states")
    gaps = {(g["site"], g["day"]) for g in spec["gaps"]}
    fixed = _event_and_action_days(spec)
    if gaps & fixed:
        raise ValueError(f"a gap falls on an event, action or study day: {sorted(gaps & fixed)}")
    for name, sets in spec["day_sets"].items():
        if name == "source":
            continue
        for site, days in sets.items():
            if site == "source":
                continue
            if any((site, d) in gaps and spec_gap(spec, site, d)["kind"] == "nothing_delivered" for d in days):
                raise ValueError(f"day set {name} delivers a nothing_delivered gap on {site}")
    ev = spec["sites"]["ev"]["sessions"]
    for name in DAY_SETS:
        for n in spec["day_sets"][name]["ev"]:
            if day(spec, n).weekday() != 1:
                raise ValueError(f"EV D{n} is not a Tuesday")
    start = int(ev["first_local"].split(":")[0])
    if not (8 <= start and start + ev["per_day"] * ev["length_minutes"] / 60 <= 16):
        raise ValueError("EV sessions fall outside TUE 08:00-16:00")


def _value_nodes(spec: dict):
    """Every dict that declares an input value, so needs a `source` (§2.1)."""
    yield "delivery", spec["delivery"]
    for name in DAY_SETS:
        yield f"day_sets.{name}", spec["day_sets"][name]
    for g in spec["gaps"]:
        yield f"gaps.{g['id']}", g
    yield "late_fill", spec["late_fill"]
    for site, s in spec["sites"].items():
        for key in ("configuration", "reading_rules", "noon", "sessions"):
            if key in s:
                yield f"{site}.{key}", s[key]
        nd = s.get("normal_day")
        if nd is not None:
            for i, b in enumerate(nd.get("blocks") or [nd]):
                yield f"{site}.normal_day[{i}]", b
        for key in ("controls", "events", "actions", "studies", "publications"):
            for i, x in enumerate(s.get(key, [])):
                yield f"{site}.{key}[{i}]", x


def _event_and_action_days(spec: dict) -> set[tuple[str, int]]:
    out: set[tuple[str, int]] = set()
    for site, s in spec["sites"].items():
        for e in s.get("events", []):
            out.add((site, e["day"]))
        for a in s.get("actions", []):
            for step in a.values():
                if isinstance(step, dict) and "day" in step:
                    out.add((site, step["day"]))
        for st in s.get("studies", []):
            out |= {(site, d) for d in range(st["from_day"], st["to_day"] + 1)}
    return out


def spec_gap(spec: dict, site: str, n: int) -> dict | None:
    return next((g for g in spec["gaps"] if g["site"] == site and g["day"] == n), None)


def load(path: Path = FIXTURE) -> dict:
    spec = json.loads(path.read_text(encoding="utf-8"))
    validate(spec)
    return spec


def fill_target(spec: dict, site_code: str, n: int, kind: str = "normal") -> dict:
    """§4: the declared fillable gap for (site_code, Dn), or `MechanismRefused` with the FILL-1 code."""
    site = next((k for k, s in spec["sites"].items() if s["site_code"] == site_code), None)
    gap = spec_gap(spec, site, n) if site else None
    if gap is None:  # an undeclared day is already one of the dataset's declared days
        raise MechanismRefused("DUPLICATE_DAY")
    if not gap.get("fill"):  # GAP-C3 / GAP-E2 hold delivered evidence (stores are append-only)
        raise MechanismRefused("DAY_HAS_EVIDENCE")
    if kind not in gap.get("fill_kinds", ()):
        raise MechanismRefused("PREPARE_ONLY_KIND")
    return gap


# --- seeding (phase 2, PARTIAL: Kobo delivery/assess/match/depth/studies drafted, not yet run) -----------------

FIXTURE_ID, FIXTURE_VERSION = "assetops.mechanism-dataset", "1"
EPOCH = "mechanism-1"


def _url(engine) -> str:
    return engine.url.render_as_string(hide_password=False)


class _Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at


class Deliverer:
    """Seals rows per device in batches of at most `max_envelopes_per_batch`, publishes each sealed batch as the
    authored `assetops.mechanism-dataset` v1 (MD0-PF Q1, the w402 L3 path) and submits it with the decision clock at
    the chunk's last source time + `decided_after_block_minutes` (R4). `real_clock` is the late_fill path (§4)."""

    def __init__(self, spec: dict, url: str, kit, site_code: str, work: Path) -> None:
        self.spec, self.url, self.kit, self.code, self.work = spec, url, kit, site_code, work
        self.seq: dict[str, int] = {}
        self.batches = self.readings = 0
        self.latest: datetime | None = None

    def deliver(self, rows: list[tuple], *, real_clock: bool = False) -> None:
        import contextlib
        import io

        import pg_harness
        from test_s2_evidence_ledger_postgres import _z
        from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
        from assetops_backend.evidence.composition import build_authored_fixture_specs
        from assetops_backend.evidence.ledger_service import BatchIngestionService
        from assetops_backend.publish_source import main as publish_source

        cap = self.spec["delivery"]["max_envelopes_per_batch"]
        after = timedelta(minutes=self.spec["delivery"]["decided_after_block_minutes"])
        by_device: dict[str, list[tuple]] = {}
        for row in sorted(rows, key=lambda r: r[2]):
            by_device.setdefault(row[0], []).append(row)
        specs = build_authored_fixture_specs()
        for device, device_rows in by_device.items():
            for i in range(0, len(device_rows), cap):
                chunk = device_rows[i:i + cap]
                texts = []
                for dev, signal, when, value in chunk:
                    source = self.kit.binding(dev, signal)["source_id"]
                    self.seq[source] = self.seq.get(source, 0) + 1
                    texts.append(self.kit.envelope(dev, self.seq[source], 0, value, source_time=_z(when),
                                                   epoch=EPOCH, bound_signal=signal))
                body = self.kit.seal(texts, device_id=device)
                path = self.work / f"batch-{self.batches}.json"
                path.write_text(body, encoding="utf-8")
                ledger = PostgresEvidenceLedger(self.url)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        code = publish_source(["--site", self.code, "--fixture-id", FIXTURE_ID, "--fixture-version",
                                               FIXTURE_VERSION, "--batch-file", str(path)], ledger=ledger,
                                              specs=specs)
                finally:
                    pg_harness.dispose(ledger)
                assert code == 0, f"authored publication refused ({code})"
                path.unlink()
                decided = chunk[-1][2] + after
                if real_clock:
                    ledger = PostgresEvidenceLedger(self.url)
                    service = BatchIngestionService(ledger)
                else:
                    ledger = PostgresEvidenceLedger(self.url, test_decision_clock_override=_Clock(decided))
                    service = BatchIngestionService(ledger, _Clock(decided))
                try:
                    answer = service.submit(self.kit.principal, body.encode("utf-8"))
                finally:
                    pg_harness.dispose(ledger)
                assert answer.status == 200 and answer.receipt.status == "COMPLETED", answer
                self.batches += 1
                self.readings += len(chunk)
                self.latest = decided if self.latest is None else max(self.latest, decided)


def kobo_day_kind(spec: dict, n: int) -> str:
    return next((e["kind"] for e in spec["sites"]["kobo"]["events"] if e["day"] == n), "normal")


def kobo_rows(spec: dict, n: int, kind: str = "normal") -> list[tuple]:
    """One Site-local Kobo day at the binding step: the normal blocks; an overrun event's values replace the block
    values inside [from_local, to_local] (F01 shape: the generator is STOPPED before and after)."""
    k = spec["sites"]["kobo"]
    rules, step = k["reading_rules"], timedelta(minutes=k["reading_rules"]["step_minutes"])
    sig = rules["signals"]
    event = None if kind == "normal" else next(e for e in k["events"] if e["day"] == n and e["kind"] == kind)
    span = None if event is None else (local_instant(spec, "kobo", n, event["from_local"]),
                                       local_instant(spec, "kobo", n, event["to_local"]))
    rows = []
    for block in k["normal_day"]["blocks"]:
        t, hi = local_instant(spec, "kobo", n, block["from_local"]), local_instant(spec, "kobo", n, block["to_local"])
        while t < hi:
            values = event if span and span[0] <= t <= span[1] else block
            rows.append((*sig["generator"], t, values["generator"]))
            rows += [(f, None, t, rules["feeder_kw"]) for f in rules["feeders"]]
            rows += [(*sig[key], t, values[key]) for key in ("pv", "dis", "soc")]
            t += step
    return rows


class KoboSite:
    """KOBO-001 converted, enabled and configured as the demo (`demo_combined_kobo.configure_at`: roles-2 -> roles-3
    -> supply uses -> roles-4), with the s4 reserve/runtime controls, at story time. Owns its stores (R5). Also the
    S6 harness runner surface (`tick`, `step`, `reload`, `tenant`, `site`, `engine`) for ACT-K1."""

    def __init__(self, spec: dict, store, engine, work: Path) -> None:
        from sqlalchemy import text

        from demo_combined_kobo import configure_at
        from test_s2_evidence_ledger_postgres import Kit, converted_enabled
        from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
        from assetops_backend.sites.foundation_service import FoundationService

        self.spec, self.store, self.engine, self.url = spec, store, engine, _url(engine)
        k = spec["sites"]["kobo"]
        self.result, _ = converted_enabled(store, engine)
        install_at = datetime.fromisoformat(k["configuration"]["install_at"].replace("Z", "+00:00"))
        self.configuration = configure_at(store, self.result, install_at)
        note = f"{spec['label']}: labelled fixture control"
        for control in k["controls"]:
            effective = datetime.fromisoformat(control["effective_from"].replace("Z", "+00:00"))
            service = FoundationService(store, "demo", _Clock(install_at + timedelta(minutes=40)))
            if control["do"] == "reserve":
                service.publish_battery_reserve(self.result.tenant, self.result.site, asset_code="battery",
                                                value=float(control["value"]), effective_from=effective, note=note)
            else:
                service.publish_component_properties(
                    self.result.tenant, self.result.site, asset_code="generator",
                    properties=[{"property_key": "minimum-runtime", "value": control["value"], "unit": "min",
                                 "source": "TEMPLATE", "source_version": 2}], effective_from=effective, note=note)
        with engine.connect() as c:
            set_id = c.execute(text("SELECT id FROM signal_binding_set_revision WHERE site_id = :s "
                                    "ORDER BY valid_from DESC, recorded_at DESC LIMIT 1"),
                               {"s": self.result.site.id}).scalar_one()
        self.kit = Kit(engine, set_id)
        self.tenant, self.site = self.kit.principal.tenant_id, self.kit.principal.site_id
        self.findings = PostgresFindingStore(self.url)
        self.deliverer = Deliverer(spec, self.url, self.kit, k["site_code"], work)
        self.now = install_at

    def tick(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now

    def reload(self) -> dict:
        return self.findings.rows(self.tenant, self.site)

    def step(self, step: dict):
        if step["do"] == "assess":
            return self.assess(self.tick())
        if step["do"] == "match":
            return self.match()
        raise AssertionError(f"no MD-0 step {step['do']!r}")

    def assess(self, at: datetime) -> None:
        import pg_harness
        from assetops_backend.analytics import dispatch_v3
        from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
        from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker

        self.now = max(self.now, at)
        jobs = PostgresAssessmentStore(self.url)
        try:
            for outcome in DispatchAssessmentWorker(jobs, model=dispatch_v3, clock=_Clock(self.now)).run_pending():
                assert outcome.status == "DONE", outcome.error
        finally:
            pg_harness.dispose(jobs)

    def match(self):
        import pg_harness
        from assetops_backend.analytics import dispatch_v3
        from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
        from assetops_backend.analytics.adapters.postgres_finding_store import FindingFenceMoved
        from assetops_backend.analytics.finding_service import FindingMatcher

        reads = PostgresAssessmentStore(self.url)
        try:
            return FindingMatcher(reads, self.findings, model=dispatch_v3, now=lambda: self.tick(),
                                  fence_moved=FindingFenceMoved).match(self.tenant, self.site)
        finally:
            pg_harness.dispose(reads)

    def deliver_day(self, n: int, kind: str | None = None, *, real_clock: bool = False) -> None:
        self.deliverer.deliver(kobo_rows(self.spec, n, kind or kobo_day_kind(self.spec, n)), real_clock=real_clock)

    def settle_day(self, n: int) -> None:
        """Step 5-6 for Dn: dispatch assessment at day end + `assess_after_day_minutes` (never before the latest
        decision instant), mini-depth for the local noon hour, then the matcher."""
        from assetops_backend.mini_depth.store import PostgresMiniDepthStore
        from assetops_backend.mini_depth.worker import MiniDepthWorker

        end = local_instant(self.spec, "kobo", n, "24:00")
        at = max(end + timedelta(minutes=self.spec["delivery"]["assess_after_day_minutes"]),
                 self.deliverer.latest or end)
        self.assess(at)
        lo, hi = (local_instant(self.spec, "kobo", n, x) for x in self.spec["sites"]["kobo"]["noon"]["window_local"])
        outcomes = MiniDepthWorker(None, PostgresMiniDepthStore(self.engine)).reconcile(
            self.spec["sites"]["kobo"]["site_code"], lo, hi)
        assert all(o.status == "DONE" for o in outcomes), outcomes
        self.match()

    def studies(self) -> list:
        """Step 7: `MiniOpportunityWorker.reconcile` + `run_pending` per declared study window (never a direct
        insert), with the lease clock at the window's end + 30 min."""
        import pg_harness
        from assetops_backend.mini_decisions.worker import build_worker

        out = []
        for study in self.spec["sites"]["kobo"]["studies"]:
            hi = local_instant(self.spec, "kobo", study["to_day"], "24:00")
            worker = build_worker(self.url, test_lease_clock=lambda at=hi + timedelta(minutes=30): at)
            try:
                worker.reconcile(self.spec["sites"]["kobo"]["site_code"],
                                 local_instant(self.spec, "kobo", study["from_day"], "00:00"), hi)
                out.append(worker.run_pending())
            finally:
                pg_harness.dispose(worker.jobs, worker.store, worker.reader)
        return out

    def close(self) -> None:
        import pg_harness

        pg_harness.dispose(self.findings)
