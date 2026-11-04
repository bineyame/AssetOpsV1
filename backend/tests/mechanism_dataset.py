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
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

FIXTURE = Path(__file__).resolve().parents[1] / "conversions" / "mechanism-v1.json"
TOOLS = Path(__file__).resolve().parents[2] / "tools"  # demo_combined_kobo, w402_mini_depth_cases (imported, not copied)
for _path in (TOOLS, TOOLS.parent / "host" / "tests"):  # demo_combined_kobo imports host test publication docs
    if str(_path) not in __import__("sys").path:
        __import__("sys").path.append(str(_path))
FIXTURE_ID, FIXTURE_VERSION = "assetops.mechanism-dataset", "1"
DAY_SETS = ("full", "states")

#: R2 / D-AW-1: the only databases MD-0 may seed or fill. The pg_harness worker pattern is
#: `<stem>_pt<run>_<tag>_test` (`pg_harness.database_name`).
#: MD0-S3: also the input templates and their per-run clones `assetops_mechanism_c<hex>_test` (`clone_template`).
#: CH5a1-R3 M4: one template per input fingerprint, `assetops_mechanism_tpl_<fp8>_test`, built under a staging name
#: `assetops_mechanism_tplb_<hex8>_test` and renamed when tagged. `assetops_mechanism_tpl_test` is the legacy
#: single template (MD-0, CH-5a1): still a mechanism DB, never looked up, pruned or dropped implicitly.
MECHANISM_DB_RE = re.compile(r"^assetops_mechanism(_close|_tpl|_tpl_[0-9a-f]{8}|_tplb_[0-9a-f]{8}|_c[0-9a-f]{6,16})?_test$")
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


def _db_now(engine) -> datetime:
    from sqlalchemy import text

    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def _db_now_url(url: str) -> datetime:
    from sqlalchemy import create_engine

    engine = create_engine(url)
    try:
        return _db_now(engine)
    finally:
        engine.dispose()


def dispatch_jobs(engine, site_id, lo: datetime, hi: datetime) -> dict[str, int]:
    """Dispatch recompute jobs overlapping [lo, hi) by status (the F5 assertions' read; SELECT only)."""
    from sqlalchemy import text

    with engine.connect() as c:
        rows = c.execute(text("SELECT status, count(*) FROM recompute_job WHERE site_id = :s AND domain = 'dispatch' "
                              "AND window_start < :hi AND window_end > :lo GROUP BY status"),
                         {"s": site_id, "lo": lo, "hi": hi}).all()
    return {r[0]: r[1] for r in rows}


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
    if set(spec["sites"]) != {"kobo"}:  # MD0-S2: Kobo-first; Cold and EV move to DD-1's real baseline
        raise ValueError("MD-0 declares KOBO-001 only (MD0-S2)")


def _value_nodes(spec: dict):
    """Every dict that declares an input value, so needs a `source` (§2.1)."""
    yield "delivery", spec["delivery"]
    for name in DAY_SETS:
        yield f"day_sets.{name}", spec["day_sets"][name]
    for g in spec["gaps"]:
        yield f"gaps.{g['id']}", g
    yield "late_fill", spec["late_fill"]
    for site, s in spec["sites"].items():
        for key in ("configuration", "reading_rules", "shapes", "noon", "sessions", "derived_channels"):
            if key in s:
                yield f"{site}.{key}", s[key]
        for name, rule in s.get("derived_channels", {}).items():
            if isinstance(rule, dict):
                yield f"{site}.derived_channels.{name}", rule
        if "busy_noon" in s.get("noon", {}):
            yield f"{site}.noon.busy_noon", s["noon"]["busy_noon"]
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
        self.epoch = EPOCH
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

        import w402_mini_depth_cases as cases

        cap = self.spec["delivery"]["max_envelopes_per_batch"]
        after = timedelta(minutes=self.spec["delivery"]["decided_after_block_minutes"])
        by_device: dict[str, list] = {}
        for row in sorted(rows, key=_row_time):
            by_device.setdefault(_row_device(row), []).append(row)
        specs = build_authored_fixture_specs()
        for device, device_rows in by_device.items():
            sealed_source = self.kit.binding(device)["source_id"]
            for i in range(0, len(device_rows), cap):
                chunk = device_rows[i:i + cap]
                texts = []
                for row in chunk:
                    if isinstance(row, tuple):
                        dev, signal, when, value = row
                        b = self.kit.binding(dev, signal)
                    else:  # a remapped w4 `positive` Planned envelope (interval means and points, v3)
                        b = cases._binding(self.kit.doc, row.device, row.signal)
                    assert b["source_id"] == sealed_source, (device, b["source_id"])
                    seq = self.seq[b["source_id"]] = self.seq.get(b["source_id"], 0) + 1
                    if isinstance(row, tuple):
                        texts.append(self.kit.envelope(dev, seq, 0, value, source_time=_z(when), epoch=self.epoch,
                                                       bound_signal=signal))
                    else:
                        texts.append(cases._envelope(self.kit.doc, b, self.epoch, seq, row))
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
                decided = _row_time(chunk[-1]) + after
                if real_clock:  # §4: the real decision clock (the DB's, set at commit); workers run after it
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
                # MD0-S4 (F5 found by the DONE assertion): a COMPLETED receipt may reject every envelope (D7's late
                # batches were all OUTSIDE_FOUNDATION_PERIOD); every generated reading must be accepted.
                counts = answer.receipt.counts
                assert counts.accepted == len(chunk) == counts.total, (device, counts)
                if real_clock:
                    # MD0-S4 R1.4 (F5): the ledger stamps `decided_at` and the job's `available_at` with the DB's
                    # clock_timestamp() at commit, so the worker and matcher clocks are the DB's now AFTER the
                    # submit (never the host's clock, which may lag the container's).
                    decided = _db_now_url(self.url)
                self.batches += 1
                self.readings += len(chunk)
                self.latest = decided if self.latest is None else max(self.latest, decided)


def _row_time(row) -> datetime:
    return row[2] if isinstance(row, tuple) else row.source_time


def _row_device(row) -> str:
    return row[0] if isinstance(row, tuple) else row.device


def kobo_day_kind(spec: dict, n: int) -> str:
    return next((e["kind"] for e in spec["sites"]["kobo"]["events"] if e["day"] == n), "normal")


def noon_planned(spec: dict, n: int, doc: dict) -> tuple[list, list[str]]:
    """P4/MD0-S2: the w4 `positive` variant's means and points (spare solar), re-dated to Dn's local noon hour, on
    KOBO-001's roles-4 bindings. The MG-W402-001 backup chain is omitted (`noon.omit`). A channel KOBO-001 does not
    bind (the residential and mill `requested-power`) is not delivered; it is returned as `dropped` so the manifest
    and the packet name it (R7), never silently."""
    import w402_mini_depth_cases as cases

    noon = spec["sites"]["kobo"]["noon"]
    variant = next(v for v in cases.load_spec()["variants"] if v["variant"] == noon["variant"])
    lo, hi = (local_instant(spec, "kobo", n, x) for x in noon["window_local"])
    moved = {k: v for k, v in variant.items() if k not in noon.get("omit", ())}
    moved["hours"] = [{"day": day(spec, n).isoformat(), "from": _z(lo), "to": _z(hi)}]
    bound = {(b["device_id"], b["signal_id"]) for b in doc["bindings"]}
    planned = cases.plan_variant(moved)
    dropped = sorted({f"{p.device}/{p.signal}" for p in planned if (p.device, p.signal) not in bound})
    return [p for p in planned if (p.device, p.signal) in bound], dropped


def _z(at: datetime) -> str:
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def kobo_rows(spec: dict, n: int, kind: str = "normal") -> list[tuple]:
    """One Site-local Kobo day at the binding step: the normal blocks; an overrun event's values replace the block
    values inside [from_local, to_local] (F01 shape: the generator is STOPPED before and after)."""
    k = spec["sites"]["kobo"]
    rules, step = k["reading_rules"], timedelta(minutes=k["reading_rules"]["step_minutes"])
    sig = rules["signals"]
    event = None if kind == "normal" else next((e for e in k["events"] if e["day"] == n and e["kind"] == kind),
                                               None)
    if kind != "normal" and event is None:
        # §2.2: an overrun is one declared shape (F01, 08:00-09:00, the same on D4/D11/D14); a late overrun on the
        # fillable gap day (§4, GAP-K7) uses that shape re-dated, so it needs no event entry of its own.
        shapes = {json.dumps({x: e[x] for x in ("from_local", "to_local", "generator", "pv", "dis", "soc")})
                  for e in k["events"] if e["kind"] == kind}
        if len(shapes) != 1 or spec_gap(spec, "kobo", n) is None:
            raise MechanismRefused("NO_DECLARED_SHAPE")
        event = json.loads(shapes.pop())
    span = None if event is None else (local_instant(spec, "kobo", n, event["from_local"]),
                                       local_instant(spec, "kobo", n, event["to_local"]))
    import w402_mini_depth_cases as cases

    # MD0-S4 R1: the producer's shapes (`shapes`): a power channel is a 5-min INTERVAL_MEAN [t, t + step) whose
    # source time is its end, written as a w402 `Planned` MEAN (the one interval envelope path); state and SoC are
    # points at t (the tuple shape, `kit.envelope`).
    means = {tuple(x) for x in k["shapes"]["interval_mean"]}
    if timedelta(minutes=k["shapes"]["interval_minutes"]) != step:
        raise MechanismRefused("SHAPE_STEP_MISMATCH")

    def reading(device: str, signal: str, t: datetime, value: str):
        if (device, signal) in means:
            return cases.Planned(device, signal, t + step, "MEAN", value, "kW", t)
        return (device, signal, t, value)

    derived = derived_rules(k)
    noon = k["noon"]
    busy = noon.get("busy_noon")
    busy_lo, busy_hi = (local_instant(spec, "kobo", n, x) for x in noon["window_local"])
    busy_today = busy is not None and n not in noon[busy["except_days"]]

    rows = []
    for block in k["normal_day"]["blocks"]:
        t, hi = local_instant(spec, "kobo", n, block["from_local"]), local_instant(spec, "kobo", n, block["to_local"])
        while t < hi:
            values = event if span and span[0] <= t <= span[1] else block
            rows.append(reading(*sig["generator"], t, values["generator"]))
            feeders = {f: rules["feeder_kw"] for f in rules["feeders"]}
            rows += [reading(f, rules["feeder_signal"], t, v) for f, v in feeders.items()]
            rows += [reading(*sig[key], t, values[key]) for key in ("pv", "dis", "soc")]
            # MD0-S5 M2 (A): the renewable-hour channels, by the fixture's rules (never literals); the busy noon's
            # charge request is the block's own `dis` value (MD-0 new example content).
            charge = values[busy["charge_request"]] if busy_today and busy_lo <= t < busy_hi else None
            rows += [reading(*channel, t, value) for channel, value in derived(values, feeders, charge)]
            t += step
    return rows


#: MD0-S5 M2 (A): the only rules a `derived_channels` entry may name (a renamed or new rule is refused, not guessed).
DERIVED_RULES = {"pv_power": "min(pv, feeders + charge_request)", "charge_request": "zero",
                 "critical_requested": "feeder:clinic-meter", "critical_delivered": "feeder:clinic-meter"}


def _kw(value: Decimal) -> str:
    text_ = format(value.normalize(), "f")
    return text_ if text_ != "-0" else "0"


def derived_rules(k: dict):
    """The fixture's `derived_channels` as one function (values, feeders, busy charge or None) -> [(channel, kW)].
    Evaluates exactly the declared rule strings; any other rule is `MechanismRefused`."""
    spec_rules = {name: r for name, r in k.get("derived_channels", {}).items() if isinstance(r, dict)}
    for name, r in spec_rules.items():
        if DERIVED_RULES.get(name) != r["rule"]:
            raise MechanismRefused(f"UNKNOWN_DERIVED_RULE: {name} {r['rule']!r}")

    def evaluate(values: dict, feeders: dict[str, str], busy_charge: str | None) -> list[tuple[tuple, str]]:
        out = []
        charge = Decimal(busy_charge) if busy_charge is not None else Decimal(0)  # rule "zero" outside the busy noon
        load = sum((Decimal(v) for v in feeders.values()), Decimal(0))
        for name, r in spec_rules.items():
            if name == "pv_power":
                value = min(Decimal(values["pv"]), load + charge)
            elif name == "charge_request":
                value = charge
            else:
                value = Decimal(feeders[r["rule"].split(":", 1)[1]])
            out.append((tuple(r["channel"]), _kw(value)))
        return out
    return evaluate


def row_shape(row) -> tuple[str, str, str, int | None]:
    """(device, signal, measurement, interval seconds) of one generated row: the L1 shape-parity test's view."""
    if isinstance(row, tuple):
        return row[0], row[1], "STATE_AT_INSTANT", None
    if row.kind != "MEAN":
        return row.device, row.signal, "STATE_AT_INSTANT", None
    return row.device, row.signal, "INTERVAL_MEAN", int((row.source_time - row.interval_start).total_seconds())


def _row_start(row) -> datetime:
    """The instant a row describes from: a point's time, an interval mean's start."""
    if isinstance(row, tuple):
        return row[2]
    return row.interval_start if row.interval_start is not None else row.source_time


def _before(row, cut: datetime) -> bool:
    """True when the row describes only time before `cut` (an interval ending at `cut` is before it)."""
    if isinstance(row, tuple) or row.interval_start is None:
        return _row_time(row) < cut
    return _row_time(row) <= cut


class KoboSite:
    """KOBO-001 converted, enabled and configured as the demo (`demo_combined_kobo.configure_at`: roles-2 -> roles-3
    -> supply uses -> roles-4), with the s4 reserve/runtime controls, at story time. Owns its stores (R5). Also the
    S6 harness runner surface (`tick`, `step`, `reload`, `tenant`, `site`, `engine`) for ACT-K1."""

    def __init__(self, spec: dict, store, engine, work: Path, resume: dict | None = None,
                 binding_at: datetime | None = None) -> None:
        """`resume` is a `state()` from an earlier process (the L3m tool builds in parts of at most 600 s): the
        Site is then found, not installed, and the delivery sequences and clocks carry on. `binding_at` (the late
        fill) seals against the binding set, and so the Foundation, in force at that instant, as a gateway that
        buffered the day would have: a later Foundation's period does not cover the day (OUTSIDE_FOUNDATION_PERIOD)."""
        from types import SimpleNamespace

        from sqlalchemy import text

        from test_s2_evidence_ledger_postgres import Kit
        from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
        from assetops_backend.config import DEVELOPMENT_TENANT_SLUG

        self.spec, self.store, self.engine, self.url = spec, store, engine, _url(engine)
        k = spec["sites"]["kobo"]
        install_at = datetime.fromisoformat(k["configuration"]["install_at"].replace("Z", "+00:00"))
        if resume is None:
            self._install(install_at)
        else:
            tenant = store.resolve_tenant(DEVELOPMENT_TENANT_SLUG)
            self.result = SimpleNamespace(tenant=tenant, site=store.find_site(tenant.id, k["site_code"]))
        with engine.connect() as c:
            # The current (unsuperseded) set with the latest valid_from: roles-4. valid_from and recorded_at tie
            # with superseded roles-3 rows at install + 27 min, so `superseded_at IS NULL` decides.
            covering = "" if binding_at is None else "AND valid_from <= :at AND (valid_to IS NULL OR valid_to > :at) "
            set_id = c.execute(text("SELECT id FROM signal_binding_set_revision WHERE site_id = :s "
                                    "AND superseded_at IS NULL " + covering +
                                    "ORDER BY valid_from DESC, version DESC LIMIT 1"),
                               {"s": self.result.site.id, "at": binding_at}).scalar_one()
        self.kit = Kit(engine, set_id)
        self.tenant, self.site = self.kit.principal.tenant_id, self.kit.principal.site_id
        self.findings = PostgresFindingStore(self.url)
        self.deliverer = Deliverer(spec, self.url, self.kit, k["site_code"], work)
        self.now = install_at
        self.noon_dropped: list[str] = []
        if resume is not None:
            d = self.deliverer
            d.seq, d.batches, d.readings = dict(resume["seq"]), resume["batches"], resume["readings"]
            d.latest = None if resume["latest"] is None else datetime.fromisoformat(resume["latest"])
            self.now, self.noon_dropped = datetime.fromisoformat(resume["now"]), list(resume["noon_dropped"])

    def state(self) -> dict:
        d = self.deliverer
        return {"seq": d.seq, "batches": d.batches, "readings": d.readings, "now": self.now.isoformat(),
                "latest": None if d.latest is None else d.latest.isoformat(), "noon_dropped": self.noon_dropped}

    def _install(self, install_at: datetime) -> None:
        from demo_combined_kobo import configure_at
        from test_s2_evidence_ledger_postgres import converted_enabled
        from assetops_backend.sites.foundation_service import FoundationService

        store, k = self.store, self.spec["sites"]["kobo"]
        self.result, _ = converted_enabled(store, self.engine)
        self.configuration = configure_at(store, self.result, install_at)
        note = f"{self.spec['label']}: labelled fixture control"
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

    def assess(self, at: datetime) -> list:
        import pg_harness
        from assetops_backend.analytics import dispatch_v3
        from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
        from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker

        self.now = max(self.now, at)
        jobs = PostgresAssessmentStore(self.url)
        try:
            outcomes = DispatchAssessmentWorker(jobs, model=dispatch_v3, clock=_Clock(self.now)).run_pending()
        finally:
            pg_harness.dispose(jobs)
        for outcome in outcomes:
            assert outcome.status == "DONE", outcome.error
        return outcomes

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

    def day_rows(self, n: int, kind: str | None = None) -> list:
        """Dn's rows. On a declared spare-solar day the noon hour's normal rows on every channel the w4 `positive`
        variant covers are replaced by that variant's envelopes (never both on one channel and instant range)."""
        rows = kobo_rows(self.spec, n, kind or kobo_day_kind(self.spec, n))
        noon = self.spec["sites"]["kobo"]["noon"]
        if n not in noon["spare_solar_days"]:
            return rows
        planned, self.noon_dropped = noon_planned(self.spec, n, self.kit.doc)
        lo, hi = (local_instant(self.spec, "kobo", n, x) for x in noon["window_local"])
        covered = {(p.device, p.signal) for p in planned}

        def replaced(r) -> bool:
            b = self.kit.binding(_row_device(r), r[1] if isinstance(r, tuple) else r.signal)
            return lo <= _row_start(r) < hi and (b["device_id"], b["signal_id"]) in covered
        return [r for r in rows if not replaced(r)] + planned

    def deliver_day(self, n: int, kind: str | None = None, *, real_clock: bool = False,
                    before_local: str | None = None, from_local: str | None = None) -> int:
        """Delivers Dn (or the part before/after a local time, for the ACT-K1 day); returns the row count."""
        rows = self.day_rows(n, kind)
        if before_local is not None:
            cut = local_instant(self.spec, "kobo", n, before_local)
            rows = [r for r in rows if _before(r, cut)]
        if from_local is not None:
            cut = local_instant(self.spec, "kobo", n, from_local)
            rows = [r for r in rows if not _before(r, cut)]
        self.deliverer.deliver(rows, real_clock=real_clock)
        return len(rows)

    def settle_day(self, n: int, *, until_local: str = "24:00", depth: bool = True) -> None:
        """Step 5-6 for Dn: dispatch assessment at `until_local` (day end) + `assess_after_day_minutes`, never
        before the latest decision instant; mini-depth for the local noon hour; then the matcher."""
        from assetops_backend.mini_depth.store import PostgresMiniDepthStore
        from assetops_backend.mini_depth.worker import MiniDepthWorker

        end = local_instant(self.spec, "kobo", n, until_local)
        at = max(end + timedelta(minutes=self.spec["delivery"]["assess_after_day_minutes"]),
                 self.deliverer.latest or end)
        done = [o.job_id for o in self.assess(at) if o.status == "DONE"]
        # MD0-S4 R1.4 (F5): at least one DONE dispatch outcome for the delivered day (an empty list is a failure,
        # never a vacuous pass: a job not yet due is never leased, so the day would go unassessed silently).
        if not self._done_on(done, local_instant(self.spec, "kobo", n, "00:00"), end):
            raise AssertionError(f"D{n}: no DONE dispatch outcome for the delivered day (outcomes {done})")
        if depth:
            lo, hi = (local_instant(self.spec, "kobo", n, x)
                      for x in self.spec["sites"]["kobo"]["noon"]["window_local"])
            depth_store = PostgresMiniDepthStore(self.engine)
            outcomes = MiniDepthWorker(None, depth_store).reconcile(self.spec["sites"]["kobo"]["site_code"], lo, hi)
            assert outcomes and all(o.status == "DONE" for o in outcomes), outcomes
        self.match()

    def _done_on(self, job_ids: list, lo: datetime, hi: datetime) -> bool:
        from sqlalchemy import text

        if not job_ids:
            return False
        with self.engine.connect() as c:
            return bool(c.execute(text(
                "SELECT count(*) FROM recompute_job WHERE id = ANY(CAST(:ids AS uuid[])) AND domain = 'dispatch' "
                "AND status = 'DONE' AND window_start < :hi AND window_end > :lo"),
                {"ids": [str(j) for j in job_ids], "lo": lo, "hi": hi}).scalar_one())

    def studies(self) -> list:
        """Step 7: `MiniOpportunityWorker.reconcile` + `run_pending` per declared study window (never a direct
        insert), with the lease clock at the window's end + 30 min."""
        import pg_harness
        from assetops_backend.mini_decisions.worker import build_worker

        out = []
        for study in self.spec["sites"]["kobo"]["studies"]:
            hi = local_instant(self.spec, "kobo", study["to_day"], "24:00")
            # MD0-S3 Q3: the opportunity job is enqueued at DB time (real), so a story-time lease clock never
            # leases it (seen: both studies returned []). The harness passes the existing `test_lease_clock` seam
            # with DB now, for this worker only; no product code changes. The studies are therefore recorded at
            # build time: an R4 build-time fact (-> DD-1b R7, a story-time `available_at` on the enqueue).
            worker = build_worker(self.url, test_lease_clock=lambda: _db_now(self.engine))
            try:
                queued = worker.reconcile(self.spec["sites"]["kobo"]["site_code"],
                                          local_instant(self.spec, "kobo", study["from_day"], "00:00"), hi)
                out.append({"anchor": study["anchor"], "queued": [repr(q) for q in queued],
                            "outcomes": [repr(o) for o in worker.run_pending()]})
            finally:
                pg_harness.dispose(worker.jobs, worker.store, worker.reader)
        return out

    def close(self) -> None:
        import pg_harness

        pg_harness.dispose(self.findings)


# --- ACT-K1, the derived chain and the seed (MD0-S2: Kobo only) ------------------------------------------------


def act_k1(site: KoboSite) -> dict:
    """ACT-K1 to CHANGE_APPLIED (MD0-PF Q3): the s6 harness accepts the D11 overrun Finding's recommendation at
    D11 13:00 local and applies it at D11 14:00 with the change effective D12 00:00 local (the
    `tools/demo_combined_kobo.py` apply call), then assess + match. VERIFIED and the close variant are MD-0b."""
    from sqlalchemy.engine import make_url

    from test_s4_finding_store_postgres import URL as HARNESS_URL
    from test_s6_action_apply_postgres import applying

    if make_url(HARNESS_URL).database != make_url(site.url).database:  # the harness reads its module-global URL
        raise MechanismRefused("HARNESS_URL_MISMATCH")
    k = site.spec["sites"]["kobo"]
    spec_action = k["actions"][0]
    event = next(e for e in k["events"] if e["anchor"] == spec_action["for_event"])

    def at(step: str) -> datetime:
        return local_instant(site.spec, "kobo", spec_action[step]["day"], spec_action[step]["local"])

    h = applying(site)
    try:
        h.clock.at = max(at("accept"), site.now + timedelta(minutes=1))
        accepted_at = h.clock.at
        finding = finding_for(site, event)
        rec = h.recommendation(finding)
        assert rec.status_code == 200, rec.text
        proposal = rec.json()["proposal"]
        made = h.accept(finding, proposal, idempotency_key="mechanism-accept-k1")
        assert made.status_code == 201, made.text
        action_id = made.json()["action"]["action_id"]
        h.clock.at = max(at("apply"), h.clock.at + timedelta(minutes=1))
        current = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()["application_basis"][
            "current_foundation_revision_id"]
        applied = h.client.post(f"/api/sites/KOBO-001/actions/{action_id}/apply", json={
            "expected_foundation_revision_id": current, "value": proposal["proposed_value"],
            "effective_from": _z(at("effective")), "idempotency_key": "mechanism-apply-k1"})
        assert applied.status_code == 201, applied.text
        site.now = max(site.now, h.clock.at)
        site.step({"do": "assess"})
        site.step({"do": "match"})
        return {"action_id": str(action_id), "finding_id": str(finding), "accepted_at": _z(accepted_at),
                "applied_at": _z(h.clock.at), "effective_from": _z(at("effective")),
                "value": proposal["proposed_value"]}
    finally:
        h.close()


def finding_for(site: KoboSite, event: dict):
    """The Finding whose anchor_start falls on the event's local day (identity by declared anchor, §3)."""
    tz = ZoneInfo(site.spec["sites"]["kobo"]["time_zone"])
    want = day(site.spec, event["day"])
    found = [f["id"] for f in site.reload()["findings"] if f["anchor_start"].astimezone(tz).date() == want]
    assert len(found) == 1, (event["anchor"], found)
    return found[0]


def derive(url: str, tenant, site_id) -> dict:
    """Step 10: backfill step a, thread steps b and c, then the lifecycle (step d) called directly so its report,
    `skipped_causes` included (the D-AW-3 record), is kept verbatim; then the CH-1b `chain_snapshots` stage until
    the outbox is consumed, and one `chain_threads` stage."""
    import pg_harness
    from assetops_backend.chain.backfill import _step_a, run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.chain.lifecycle_run import run_lifecycle
    from assetops_backend.scheduling import stages

    reader, store = build_thread_sources(url), build_thread_store(url)
    try:
        a = _step_a(reader, tenant, site_id, url, False)
        bc = run_threads(reader, store, tenant, site_id, ("b", "c"))
        d = run_lifecycle(reader, store, tenant, site_id)
    finally:
        pg_harness.dispose(reader, store)
    args = {"tenant_id": str(tenant), "site_id": str(site_id)}
    drains = []
    for _ in range(50):
        out = stages.chain_snapshots(url, {**args, "consume_limit": 500, "items": 500})
        assert out["code"] == "OK", out
        drains.append({"processed": out["processed"], "deferred": out["deferred"]})
        if not out["processed"] and not out["deferred"]:
            break
    threads = stages.chain_threads(url, {**args, "limit": 500})
    assert threads["code"] == "OK", threads
    return {"a": a, "bc": bc, "d": d, "snapshots": drains,
            "threads_stage": {"processed": threads["processed"], "deferred": threads["deferred"]}}


def _publish(site: KoboSite) -> list[str]:
    """Step 3: the prices through `publish_price` at their story time; the objective through `declare_objective`
    (no clock seam: build time, MD0-PF Q5, R4 -> DD-1)."""
    import contextlib
    import io

    import pg_harness
    from demo_combined_kobo import publish_price
    from assetops_backend.declare_objective import main as declare
    from assetops_backend.objectives.composition import build_objective_store

    root = Path(__file__).resolve().parents[2]
    out = []
    for pub in site.spec["sites"]["kobo"]["publications"]:
        if pub["kind"] == "price":
            publish_price(site.url, local_instant(site.spec, "kobo", pub["recorded"]["day"],
                                                  pub["recorded"]["local"]))
        else:
            store = build_objective_store(site.url)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    code = declare(["fixture", "--file", str(root / pub["file"]), "--site", "KOBO-001"],
                                   store=store)
            finally:
                pg_harness.dispose(store)
            assert code == 0, f"objective declaration refused ({code})"
        out.append(pub["kind"])
    return out


def seed_steps(spec: dict, day_set: str) -> list[str]:
    """The seed in story order: `begin` (Site, configuration, controls, prices, objective), one `D<n>` per
    delivered day, `studies`, then `derive` (step 10 and the manifest)."""
    return ["begin", *[f"D{n}" for n in spec["day_sets"][day_set]["kobo"]], "studies", "derive"]


def seed_part(store, engine, day_set: str, steps: list[str], state: dict | None, work: Path) -> dict:
    """Runs `steps` (a contiguous slice of `seed_steps`) and returns the state to resume from. One process may run
    every step (`seed_database`); the L3m tool runs them in parts of at most 600 s against its own DB."""
    import time

    require_mechanism_db(engine)
    work.mkdir(parents=True, exist_ok=True)
    spec = load()
    k = spec["sites"]["kobo"]
    act = k["actions"][0]
    act_day, act_local = act["accept"]["day"], act["accept"]["local"]
    state = {"timings": {}, "action": None, "published": None} if state is None else dict(state)
    site = KoboSite(spec, store, engine, work, resume=None if steps[0] == "begin" else state["site"])
    try:
        for step in steps:
            t0 = time.perf_counter()
            if step == "begin":
                state["published"] = _publish(site)
            elif step.startswith("D"):
                n = int(step[1:])
                if n == act_day:  # the morning (with the overrun) is settled before the accept, in story order
                    site.deliver_day(n, before_local=act_local)
                    site.settle_day(n, until_local=act_local, depth=False)
                    state["action"] = act_k1(site)
                    site.deliver_day(n, from_local=act_local)
                else:
                    site.deliver_day(n)
                site.settle_day(n)
            elif step == "studies":
                state["studies"] = site.studies()
            elif step == "derive":
                chain = derive(site.url, site.tenant, site.site)
                days = spec["day_sets"][day_set]["kobo"]
                state["manifest"] = {
                    "variant": "main", "day_set": day_set, "days": days, "tenant_id": str(site.tenant),
                    "site_id": str(site.site), "action": state["action"], "published": state["published"],
                    "findings": {e["anchor"]: str(finding_for(site, e)) for e in k["events"] if e["day"] in days},
                    "batches": site.deliverer.batches, "readings": site.deliverer.readings,
                    "role_set": site.kit.doc["mapping"]["role_set"], "noon_dropped": site.noon_dropped,
                    "studies": state.get("studies"), "lifecycle": chain["d"],
                    "steps": {"a": chain["a"].get("written"), "bc": chain["bc"], "snapshots": chain["snapshots"],
                              "threads_stage": chain["threads_stage"]},
                }
            else:
                raise AssertionError(f"no seed step {step!r}")
            state["timings"][step] = round(time.perf_counter() - t0, 1)
        state["site"] = site.state()
    finally:
        site.close()
    return json.loads(json.dumps(state, default=str))


def seed_database(store, engine, variant: str = "main", day_set: str = "full") -> dict:
    """The setup_cache function op (R5): seeds the Kobo mechanism dataset in story order and returns a plain
    manifest keyed by declared anchor. Owns and disposes every resource it opens; no monkeypatch."""
    import tempfile

    if variant != "main":
        raise MechanismRefused("VARIANT_DEFERRED")  # close -> MD-0b (MD0-PF Q3)
    require_mechanism_db(engine)
    with tempfile.TemporaryDirectory(prefix="mechanism-") as work:
        state = seed_part(store, engine, day_set, seed_steps(load(), day_set), None, Path(work))
    manifest = state["manifest"]
    manifest["timings"] = {**state["timings"], "total": round(sum(state["timings"].values()), 1)}
    return manifest


# --- the input template (Architect MD0-S3 Q1) --------------------------------------------------------------------
#
# `tools/mechanism_dataset.py build --variant states` runs every seed step but `derive` into a staging DB, in parts,
# and only then tags it (COMMENT ON DATABASE) with the input-writer fingerprint and the seed state. A slice's L2m
# clones it (`CREATE DATABASE ... TEMPLATE`, seconds) and runs `derive` (step 10) with its own code. A template whose
# tag is missing (an unfinished build) or whose fingerprint differs from this checkout's input writers is refused:
# the slice rebuilds the template, it never uses stale inputs.

LEGACY_TEMPLATE_DB = "assetops_mechanism_tpl_test"
TEMPLATE_RE = re.compile(r"^assetops_mechanism_tpl_([0-9a-f]{8})_test$")
TEMPLATES_KEPT = 2  # M4: the two newest, so main and one branch never overwrite each other
TEMPLATE_DAY_SET = "states"
TAG_SCHEMA = "assetops-mechanism-template/2"  # /2: MD0-S5 M1 traced module list
REPO = Path(__file__).resolve().parents[2]
#: MD0-S5 M1: the template's inputs are import-traced, not a hand list. Every repo file loaded as a module during the
#: input build (`sys.modules`, filtered to the repo after each step), except the derive step's `chain` package, plus
#: the data folders the build reads as files. The module list is stored in the tag and `check_tag` re-hashes it with
#: the folders; a new import can only arrive by editing a file already in the list, so the scheme is closed.
#: `fixtures/` in the ruling is `backend/tests/fixtures` (the repo has no top-level `fixtures/`; it holds
#: `s1/kobo-001.yaml`, the Site import source).
INPUT_DATA_TREES = ("backend/conversions", "backend/migrations", "backend/tests/fixtures", "config/site-templates",
                    "contracts")
DERIVE_TREE = "backend/assetops_backend/chain/"


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def data_files(root: Path = REPO) -> list[str]:
    out = []
    for tree in INPUT_DATA_TREES:
        out.extend(_rel(p, root) for p in (root / tree).rglob("*") if p.is_file() and "__pycache__" not in p.parts
                   and not p.name.endswith((".pyc", ".sqlite3")))
    return sorted(out)


def loaded_repo_files(root: Path = REPO) -> list[str]:
    """The repo files loaded as modules in this process (`sys.modules`), `chain/**` excluded."""
    import sys

    base, out = root.resolve(), set()
    for module in list(sys.modules.values()):
        f = getattr(module, "__file__", None)
        if not f or not f.endswith(".py"):
            continue
        try:
            rel = _rel(Path(f).resolve(), base)
        except ValueError:
            continue
        if not rel.startswith(DERIVE_TREE) and "/.venv/" not in f"/{rel}":
            out.add(rel)
    return sorted(out)


def file_hashes(files, root: Path = REPO) -> dict[str, str]:
    """rel path -> SHA-256 of its LF-normalised bytes (`missing` when the file is gone: a stale input)."""
    import hashlib

    out = {}
    for rel in sorted(set(files)):
        path = root / rel
        out[rel] = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() if path.is_file() \
            else "missing"
    return out


def fingerprint_of(hashes: dict[str, str]) -> str:
    import hashlib

    digest = hashlib.sha256()
    for rel in sorted(hashes):
        digest.update(f"{rel}\0{hashes[rel]}\n".encode())
    return digest.hexdigest()


def input_hashes(modules, root: Path = REPO) -> dict[str, str]:
    """The traced modules plus every file under the data folders, hashed now."""
    return file_hashes([*modules, *data_files(root)], root)


def input_fingerprint(modules=(), root: Path = REPO) -> str:
    """SHA-256 over the traced modules' and the data folders' paths and LF-normalised bytes."""
    return fingerprint_of(input_hashes(modules, root))


def inputs_changed(saved: dict[str, str], root: Path = REPO) -> list[str]:
    """MD0-S5 L2: the inputs recorded so far (at build start and after each step) that differ now, plus data files
    added or removed since. Empty when a resume may go on."""
    now = file_hashes([*saved, *data_files(root)], root)
    return sorted(rel for rel in now if saved.get(rel) != now[rel])


def record_inputs(saved: dict[str, str], root: Path = REPO) -> dict[str, str]:
    """`saved` plus every repo module loaded since, hashed now (they were just loaded from these bytes)."""
    new = [m for m in loaded_repo_files(root) if m not in saved]
    return {**saved, **file_hashes(new, root)}


def input_steps(spec: dict, day_set: str) -> list[str]:
    """The template's steps: every seed step but `derive` (step 10 runs on the clone, with the branch's code)."""
    return [s for s in seed_steps(spec, day_set) if s != "derive"]


def admin_engine(url: str):
    """One AUTOCOMMIT engine on the server's `postgres` database (the server of `url`)."""
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool

    return create_engine(make_url(url).set(database="postgres"), poolclass=NullPool, isolation_level="AUTOCOMMIT")


def database_url(url: str, name: str) -> str:
    from sqlalchemy.engine import make_url

    return make_url(url).set(database=name).render_as_string(hide_password=False)


def _guarded(name: str) -> str:
    if not mechanism_db_allowed(name) or not MECHANISM_DB_RE.match(name):
        raise MechanismRefused("MECHANISM_DB_ONLY")
    return '"' + name + '"'


def template_name(fingerprint: str) -> str:
    """M4: the template database for one input fingerprint."""
    if not re.fullmatch(r"[0-9a-f]{64}", fingerprint or ""):
        raise MechanismRefused(f"MECHANISM_DB_ONLY: not a fingerprint: {fingerprint!r}")
    return f"assetops_mechanism_tpl_{fingerprint[:8]}_test"


def make_tag(state: dict, day_set: str, modules=(), fingerprint: str | None = None) -> dict:
    """The tag: the fingerprint and the traced module list `check_tag` re-hashes (MD0-S5 M1). `built_at` orders the
    templates for pruning (M4); it is not part of the fingerprint."""
    data = set(data_files())
    modules = sorted(m for m in modules if m not in data)
    return {"schema": TAG_SCHEMA, "fingerprint": fingerprint or input_fingerprint(modules), "modules": modules,
            "day_set": day_set, "state": state, "built_at": datetime.now(timezone.utc).isoformat()}


def tag_template(admin, tag: dict, name: str) -> None:
    """Writes the tag as the database comment; called only after every input step has run."""
    from sqlalchemy import text

    quoted = _guarded(name)
    body = json.dumps(tag, separators=(",", ":"), default=str).replace("'", "''")
    with admin.connect() as c:
        c.exec_driver_sql(f"COMMENT ON DATABASE {quoted} IS '{body}'")  # no bind parsing of the JSON


def read_tag(admin, name: str) -> dict | None:
    """The template's tag, or None (no such database, or an unfinished build: no comment)."""
    from sqlalchemy import text

    with admin.connect() as c:
        raw = c.execute(text("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname = :n"),
                        {"n": name}).scalar_one_or_none()
    if not raw:
        return None
    try:
        tag = json.loads(raw)
    except ValueError:
        return None
    return tag if isinstance(tag, dict) and tag.get("schema") == TAG_SCHEMA else None


def check_tag(tag: dict | None, fingerprint: str | None = None) -> dict:
    """Pure: the usable tag, else `MechanismRefused` with `TEMPLATE_MISSING` (no database or no tag: an unfinished
    build) or `TEMPLATE_STALE` (the input writers changed since the build)."""
    if tag is None:
        raise MechanismRefused("TEMPLATE_MISSING: build it with "
                               "`python tools/mechanism_dataset.py build --variant states --budget 540`")
    want = fingerprint or input_fingerprint(tag.get("modules") or ())
    if tag.get("fingerprint") != want:
        raise MechanismRefused(f"TEMPLATE_STALE: template inputs {str(tag.get('fingerprint'))[:12]} != this "
                               f"checkout {want[:12]}; rebuild with `python tools/mechanism_dataset.py build "
                               f"--variant states --budget 540`")
    return tag


def templates(admin) -> list[tuple[str, dict | None]]:
    """M4: every per-fingerprint template on the server, newest first (by the tag's `built_at`; an untagged one
    sorts last). The legacy `assetops_mechanism_tpl_test` is not listed."""
    from sqlalchemy import text

    with admin.connect() as c:
        names = [r[0] for r in c.execute(text("SELECT datname FROM pg_database WHERE datname ~ :re"),
                                         {"re": TEMPLATE_RE.pattern})]
    found = [(n, read_tag(admin, n)) for n in sorted(names) if TEMPLATE_RE.fullmatch(n)]
    return sorted(found, key=lambda nt: str((nt[1] or {}).get("built_at") or ""), reverse=True)


def find_template(admin, fingerprint: str | None = None) -> str:
    """M4: the template whose tag matches this checkout (each candidate's own traced module list re-hashed, as
    `check_tag` does) and whose name carries that fingerprint. Else `TEMPLATE_STALE` when some template exists
    (naming the newest), or `TEMPLATE_MISSING`."""
    found = templates(admin)
    for name, tag in found:
        if tag is None:
            continue
        want = fingerprint or input_fingerprint(tag.get("modules") or ())
        if tag.get("fingerprint") == want and name == template_name(want):
            return name
    tagged = [tag for _, tag in found if tag is not None]
    check_tag(tagged[0] if tagged else None, fingerprint)  # raises: no match means missing or stale
    raise MechanismRefused("TEMPLATE_STALE: no template is named for its own fingerprint")  # pragma: no cover


def publish_template(admin, staging: str, tag: dict, keep: int = TEMPLATES_KEPT) -> tuple[str, list[str]]:
    """M4: tag the finished staging build, rename it to its fingerprint's name (replacing an older build of the same
    fingerprint), then drop all but the `keep` newest per-fingerprint templates. Returns (name, dropped)."""
    from sqlalchemy import text

    name = template_name(tag["fingerprint"])
    tag_template(admin, tag, staging)
    quoted_staging, quoted_name = _guarded(staging), _guarded(name)
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {quoted_name} WITH (FORCE)"))
        # a rename needs the staging DB idle: end any session the build left open (only that database's)
        c.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :n "
                       "AND pid <> pg_backend_pid()"), {"n": staging})
        c.execute(text(f"ALTER DATABASE {quoted_staging} RENAME TO {quoted_name}"))
    dropped = prune_list([n for n, _ in templates(admin)], name, keep)
    for n in dropped:
        drop_database(admin, n)
    return name, dropped


def prune_list(newest_first: list[str], kept: str, keep: int = TEMPLATES_KEPT) -> list[str]:
    """Pure (M4): the templates to drop, given every per-fingerprint template newest first: all but `kept` and the
    newest `keep - 1` others. Only per-fingerprint names are ever returned (never the legacy single template)."""
    others = [n for n in newest_first if n != kept and TEMPLATE_RE.fullmatch(n)]
    return others[max(0, keep - 1):]


def clone_template(admin, target: str, template: str | None = None) -> dict:
    """Refuses a missing or stale template, then `CREATE DATABASE target TEMPLATE template`. Returns the tag. With no
    `template`, the one matching this checkout's fingerprint (`find_template`)."""
    from sqlalchemy import text

    if template is None:
        template = find_template(admin)
    tag = check_tag(read_tag(admin, template))
    if target == template:
        raise MechanismRefused("MECHANISM_DB_ONLY")
    quoted_target, quoted_template = _guarded(target), _guarded(template)
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {quoted_target} WITH (FORCE)"))
        c.execute(text(f"CREATE DATABASE {quoted_target} TEMPLATE {quoted_template}"))
        c.execute(text(f"ALTER DATABASE {quoted_target} SET synchronous_commit = off"))
    return tag


def drop_database(admin, name: str) -> None:
    from sqlalchemy import text

    quoted = _guarded(name)
    with admin.connect() as c:
        c.execute(text(f"DROP DATABASE IF EXISTS {quoted} WITH (FORCE)"))


def derive_clone(url: str, tag: dict, work: Path) -> dict:
    """Step 10 on a clone with this checkout's code: `seed_part([derive])` resumed from the template's seed state.
    Returns the manifest (as `seed_database`), with the derive time."""
    from sqlalchemy import create_engine

    import pg_harness
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    engine, store = create_engine(url), PostgresFoundationStore(url)
    try:
        state = seed_part(store, engine, tag["day_set"], ["derive"], tag["state"], work)
    finally:
        pg_harness.dispose(store)
        engine.dispose()
    manifest = state["manifest"]
    manifest["timings"] = {"derive": state["timings"]["derive"], "template": tag["state"].get("timings")}
    return manifest


# --- reads, late_fill (§4) and build_work (§6) -------------------------------------------------------------------


def grades(engine, site_id) -> dict[str, dict[str, str]]:
    """local day -> measure -> grade of the latest snapshot revision. SITE subjects are keyed by the measure, ASSET
    subjects by `measure@<asset code>` (productive_kwh and avoidable_gen_min are ASSET measures)."""
    from sqlalchemy import text

    with engine.connect() as c:
        rows = c.execute(text(
            "SELECT DISTINCT ON (s.local_day, s.measure, s.subject_kind, s.subject_ref) s.local_day, s.measure, "
            "s.subject_kind, coalesce(a.asset_code, s.subject_ref), s.grade FROM site_day_snapshot s "
            "LEFT JOIN asset a ON s.subject_kind = 'ASSET' AND a.id::text = lower(s.subject_ref) "
            "WHERE s.site_id = :s ORDER BY s.local_day, s.measure, s.subject_kind, s.subject_ref, s.revision DESC"),
            {"s": site_id}).all()
    out: dict[str, dict[str, str]] = {}
    for d, measure, kind, ref, grade in rows:
        out.setdefault(d.isoformat(), {})[measure if kind == "SITE" else f"{measure}@{ref}"] = grade
    return out


LATE_EPOCH = "mechanism-late-1"


def late_fill(url: str, site_code: str, n: int, kind: str = "normal", now=None) -> dict:
    """§4 (FILL-1 proof): delivers the declared fillable gap day (GAP-K7) with the REAL decision clock, so
    `recorded_at` is now while source times stay on Dn; then steps 5, 6 and 10 for that day. It refuses any other
    day with the FILL-1 codes (`fill_target`). A fresh sequence epoch keeps the seed's sequences untouched. `now`
    is accepted for the §4 signature and unused: the clock is the real one by design."""
    import tempfile

    from sqlalchemy import create_engine

    import pg_harness
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    spec = load()
    fill_target(spec, site_code, n, kind)
    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    try:
        require_mechanism_db(engine)
        real = datetime.now(timezone.utc)
        resume = {"seq": {}, "batches": 0, "readings": 0, "now": real.isoformat(), "latest": None,
                  "noon_dropped": []}
        with tempfile.TemporaryDirectory(prefix="mechanism-late-") as work:
            site = KoboSite(spec, store, engine, Path(work), resume=resume,
                            binding_at=local_instant(spec, "kobo", n, "00:00"))
            try:
                site.deliverer.epoch = LATE_EPOCH
                readings = site.deliver_day(n, kind, real_clock=True)
                before = {f["id"] for f in site.reload()["findings"]}
                site.settle_day(n)
                # MD0-S4 R1.4 (F5): nothing of the filled day may be left waiting for a lease.
                lo, hi = local_instant(spec, "kobo", n, "00:00"), local_instant(spec, "kobo", n, "24:00")
                left = {s: c for s, c in dispatch_jobs(engine, site.site, lo, hi).items() if s in ("PENDING", "LEASED")}
                if left:
                    raise AssertionError(f"D{n}: dispatch jobs left after the late fill: {left}")
                after = {f["id"] for f in site.reload()["findings"]}
                derive(site.url, site.tenant, site.site)
                tenant, site_id = site.tenant, site.site
            finally:
                site.close()
        snaps = grades(engine, site_id).get(day(spec, n).isoformat(), {})
        return {"day": day(spec, n).isoformat(), "kind": kind, "readings": readings,
                "events": sorted(str(f) for f in after - before), "recorded_at": real.isoformat(),
                "snapshots": snaps, "tenant_id": str(tenant), "site_id": str(site_id)}
    finally:
        pg_harness.dispose(store)
        engine.dispose()


def build_work(url: str, out: Path, manifest: dict, variant: str = "main") -> None:
    """§6: story.json, days.json (R10: Kobo entries are UTC days, CH-5a1 changes them with `day_windows`),
    keys.json (fresh random keys for `demo_combined.KEY_NAMES`) and expected-threads.json (R9: Finding ids by
    declared anchor, grouping from the fixture's `threads`, never read from thread output)."""
    import secrets

    from demo_combined import KEY_NAMES

    spec = load()
    k = spec["sites"]["kobo"]
    out.mkdir(parents=True, exist_ok=True)
    story = {"S": spec["story"]["S"], "code": "mechanism-v1", "sites": ["kobo"], "label": spec["label"],
             "variant": variant, "day_set": manifest["day_set"]}
    days = []
    for n in range(1, 15):
        d = day(spec, n)
        gap = spec_gap(spec, "kobo", n)
        kind = "gap" if gap else kobo_day_kind(spec, n)
        if not gap and n not in manifest["days"]:
            continue  # not delivered in this day set: no expected Site-day
        start = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
        days.append({"site": "kobo", "kind": kind, "day": d.isoformat(), "start": _z(start),
                     "end": _z(start + timedelta(days=1)), "assess": "build"})
    threads = [{"name": t["name"], "site_code": k["site_code"], "mechanism": t["mechanism"],
                "findings": [manifest["findings"][a] for a in t["events"] if a in manifest["findings"]]}
               for t in spec["threads"] if t.get("events")]
    files = {"story.json": story, "days.json": {"days": days},
             "keys.json": {name: secrets.token_hex(32) for name in KEY_NAMES},
             "expected-threads.json": {"schema": "chain-coherence-threads/1",
                                       "basis": "MD-0 build_work: Finding ids by declared anchor (R9)",
                                       "threads": threads}}
    for name, doc in files.items():
        (out / name).write_text(json.dumps(doc, indent=1), encoding="utf-8")
